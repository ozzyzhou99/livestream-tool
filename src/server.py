"""Loopback HTTP server for the Arena Stream web application."""

from __future__ import annotations

import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from proxy import ProxyError, fetch_upstream, proxy_url, rewrite_hls_manifest
from resolver import ResolveError, StreamResolver
from search import SPORT_HINTS, SearchError, SearchService


MAX_BODY = 64 * 1024
MAX_MANIFEST = 5 * 1024 * 1024
FORWARDED_HEADERS = {
    "content-type",
    "cache-control",
    "expires",
    "etag",
    "last-modified",
    "accept-ranges",
    "content-range",
}
CLIENT_DISCONNECT_ERRORS = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)


def write_client_chunk(writer, data: bytes) -> bool:
    """Write a response chunk; return False when the browser went away."""
    try:
        writer.write(data)
        return True
    except CLIENT_DISCONNECT_ERRORS:
        return False


def web_root() -> Path:
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "web"
    if getattr(sys, "_MEIPASS", None) and bundled.exists():
        return bundled
    return Path(__file__).resolve().parent / "web"


class ArenaHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler_class, search_service=None, resolver=None, static_root=None):
        super().__init__(address, handler_class)
        self.search_service = search_service or SearchService()
        self.resolver = resolver or StreamResolver()
        self.static_root = Path(static_root or web_root()).resolve()


class ArenaRequestHandler(BaseHTTPRequestHandler):
    server: ArenaHTTPServer
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt: str, *args) -> None:
        if os.environ.get("ARENA_DEBUG"):
            super().log_message(fmt, *args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json({
                "ok": True,
                "service": "arena-stream",
                "version": "3.0.1",
                "capabilities": ["youtube-search", "chinese-web-search", "streamlink", "yt-dlp", "html-scan", "browser-network-scan"],
            })
            return
        if parsed.path == "/api/search":
            self._search(parse_qs(parsed.query))
            return
        if parsed.path == "/api/proxy":
            self._proxy(parse_qs(parsed.query))
            return
        if parsed.path.startswith("/api/"):
            self._error(HTTPStatus.NOT_FOUND, "接口不存在。")
            return
        self._static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/resolve":
            self._resolve()
            return
        self._error(HTTPStatus.NOT_FOUND, "接口不存在。")

    def _search(self, params: dict[str, list[str]]) -> None:
        query = params.get("q", [""])[0].strip()
        sport = params.get("sport", ["all"])[0]
        try:
            limit = int(params.get("limit", ["18"])[0])
        except ValueError:
            limit = 18
        deep = params.get("deep", ["1"])[0].casefold() not in {"0", "false", "off"}
        if len(query) > 120:
            self._error(HTTPStatus.BAD_REQUEST, "关键词不能超过 120 个字符。")
            return
        if sport not in SPORT_HINTS:
            sport = "all"
        try:
            results = self.server.search_service.search(query, sport, limit, deep)
        except SearchError as exc:
            self._error(HTTPStatus.BAD_GATEWAY, str(exc))
            return
        self._json({"query": query, "sport": sport, "deep": deep, "count": len(results), "results": [item.to_dict() for item in results]})

    def _resolve(self) -> None:
        try:
            payload = self._read_json()
            url = str(payload.get("url") or "")
            deep = bool(payload.get("deep", True))
            resolved = self.server.resolver.resolve(url, deep=deep)
        except (ValueError, ResolveError) as exc:
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        data = resolved.to_dict()
        if resolved.kind != "embed":
            data["proxy_url"] = proxy_url(resolved.playback_url, resolved.referer)
        self._json(data)

    def _proxy(self, params: dict[str, list[str]]) -> None:
        target = params.get("url", [""])[0]
        referer = params.get("referer", [""])[0]
        if not target:
            self._error(HTTPStatus.BAD_REQUEST, "缺少媒体地址。")
            return
        upstream = None
        try:
            upstream, final_url = fetch_upstream(target, referer, self.headers.get("Range", ""))
            content_type = upstream.headers.get("Content-Type", "").lower()
            is_manifest = "mpegurl" in content_type or ".m3u8" in urlparse(final_url).path.lower()
            if is_manifest:
                raw = upstream.content
                if len(raw) > MAX_MANIFEST:
                    raise ProxyError("HLS 清单过大。")
                encoding = upstream.encoding or "utf-8"
                manifest = raw.decode(encoding, errors="replace")
                rewritten = rewrite_hls_manifest(manifest, final_url, referer).encode("utf-8")
                self.send_response(upstream.status_code)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl; charset=utf-8")
                self.send_header("Content-Length", str(len(rewritten)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                write_client_chunk(self.wfile, rewritten)
                return

            self.send_response(upstream.status_code)
            for name, value in upstream.headers.items():
                if name.lower() in FORWARDED_HEADERS:
                    self.send_header(name, value)
            self.end_headers()
            for chunk in upstream.iter_content(64 * 1024):
                if chunk:
                    if not write_client_chunk(self.wfile, chunk):
                        break
        except CLIENT_DISCONNECT_ERRORS:
            return
        except (ProxyError, OSError) as exc:
            if not self.wfile.closed:
                self._error(HTTPStatus.BAD_GATEWAY, str(exc))
        except Exception as exc:
            if not self.wfile.closed:
                self._error(HTTPStatus.BAD_GATEWAY, f"媒体代理失败：{exc}")
        finally:
            if upstream is not None:
                upstream.close()

    def _static(self, request_path: str) -> None:
        relative = request_path.lstrip("/") or "index.html"
        candidate = (self.server.static_root / relative).resolve()
        try:
            candidate.relative_to(self.server.static_root)
        except ValueError:
            self._error(HTTPStatus.FORBIDDEN, "禁止访问该路径。")
            return
        if not candidate.is_file():
            candidate = self.server.static_root / "index.html"
        if not candidate.is_file():
            self._error(HTTPStatus.NOT_FOUND, "前端资源不存在。")
            return
        data = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith(("text/", "application/javascript")) else content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        # YouTube embeds require a Referer (error 153 otherwise).  This policy
        # sends only the local app origin cross-site, without exposing paths,
        # queries, search terms, or resolved media URLs.
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' https: data:; media-src 'self' blob:; frame-src https://www.youtube-nocookie.com; script-src 'self'; style-src 'self'; connect-src 'self'; worker-src 'self' blob:;")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("请求长度无效。") from exc
        if length <= 0 or length > MAX_BODY:
            raise ValueError("请求内容为空或过大。")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("请求 JSON 无效。") from exc
        if not isinstance(payload, dict):
            raise ValueError("请求 JSON 必须是对象。")
        return payload

    def _json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if not write_client_chunk(self.wfile, data):
            # A newer search can abort the browser's previous request while the
            # provider threads are still finishing.  That is normal, not a
            # server error worth printing a socketserver traceback for.
            return

    def _error(self, status: int, message: str) -> None:
        self._json({"error": message}, status)


def create_server(host: str = "127.0.0.1", port: int = 8765, **kwargs) -> ArenaHTTPServer:
    return ArenaHTTPServer((host, port), ArenaRequestHandler, **kwargs)
