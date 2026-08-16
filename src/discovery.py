"""Discover browser-playable media exposed by a public web page.

Static scanning reads HTML and embedded JSON.  Optional dynamic scanning opens
the page in an isolated, cookie-free Chromium context and observes network
requests.  Neither scanner attempts authentication, DRM decryption or access-
control bypasses.
"""

from __future__ import annotations

import html
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from proxy import USER_AGENT, ProxyError, fetch_upstream, validate_public_http_url

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


MAX_PAGE_BYTES = 5 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MEDIA_EXT_RE = re.compile(r"\.(m3u8|mpd|flv|mp4|m4v|webm)(?:$|[?#])", re.IGNORECASE)
ABSOLUTE_MEDIA_RE = re.compile(
    r"https?://[^\s\"'<>]+?\.(?:m3u8|mpd|flv|mp4|m4v|webm)(?:\?[^\s\"'<>]*)?",
    re.IGNORECASE,
)
ATTRIBUTE_URL_RE = re.compile(
    r"(?:src|href|data-src|data-url|play_url|stream_url|hls_url|flv_url)\s*[:=]\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)
IFRAME_RE = re.compile(r"<iframe[^>]+src\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
DRM_TERMS = (
    "com.widevine.alpha",
    "widevine",
    "playready",
    "fairplay",
    "skd://",
    "urn:uuid:edef8ba9",
    "urn:uuid:9a04f079",
)
LICENSE_TERMS = ("license", "widevine", "playready", "fairplay", "drm")


@dataclass(slots=True)
class MediaCandidate:
    url: str
    kind: str
    source: str
    referer: str
    content_type: str = ""
    drm: bool = False


@dataclass(slots=True)
class DiscoveryReport:
    candidates: list[MediaCandidate]
    diagnostics: list[str]
    drm_detected: bool = False


def media_kind(url: str, content_type: str = "") -> str | None:
    lowered_type = content_type.casefold()
    match = MEDIA_EXT_RE.search(url)
    extension = match.group(1).lower() if match else ""
    if extension == "m3u8" or "mpegurl" in lowered_type:
        return "hls"
    if extension == "mpd" or "dash+xml" in lowered_type:
        return "dash"
    if extension == "flv" or "flv" in lowered_type:
        return "flv"
    if extension in {"mp4", "m4v", "webm"} or lowered_type.startswith("video/"):
        return "native"
    return None


def detect_manifest_drm(text: str) -> bool:
    lowered = text.casefold()
    if any(term in lowered for term in DRM_TERMS):
        return True
    if "#ext-x-key" in lowered:
        if "method=sample-aes" in lowered:
            return True
        formats = re.findall(r"keyformat\s*=\s*[\"']?([^,\"'\s]+)", lowered)
        if any(value not in {"identity", "\"identity\""} for value in formats):
            return True
    return False


def _read_limited(response, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(64 * 1024):
        total += len(chunk)
        if total > limit:
            raise ProxyError("页面或媒体清单超过安全扫描上限。")
        chunks.append(chunk)
    return b"".join(chunks)


def _normalise_embedded_text(text: str) -> str:
    value = html.unescape(text)
    value = value.replace("\\/", "/")
    value = re.sub(r"\\u002[fF]", "/", value)
    value = re.sub(r"\\u003[aA]", ":", value)
    value = re.sub(r"\\u002[eE]", ".", value)
    value = value.replace("&amp;", "&")
    return value


def extract_media_urls(text: str, base_url: str) -> list[str]:
    decoded = _normalise_embedded_text(text)
    found: list[str] = []
    for match in ABSOLUTE_MEDIA_RE.findall(decoded):
        found.append(match.rstrip("\\"))
    for value in ATTRIBUTE_URL_RE.findall(decoded):
        absolute = urljoin(base_url, value.strip())
        if media_kind(absolute):
            found.append(absolute)
    unique: list[str] = []
    seen: set[str] = set()
    for value in found:
        if value.startswith(("http://", "https://")) and value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


class PageMediaScanner:
    def scan(self, page_url: str, include_frames: bool = True) -> DiscoveryReport:
        validate_public_http_url(page_url)
        response = None
        diagnostics: list[str] = []
        try:
            response, final_url = fetch_upstream(page_url)
            content_type = response.headers.get("Content-Type", "")
            raw = _read_limited(response, MAX_PAGE_BYTES)
            text = raw.decode(response.encoding or "utf-8", errors="replace")
        except Exception as exc:
            return DiscoveryReport([], [f"HTML 扫描失败：{exc}"])
        finally:
            if response is not None:
                response.close()

        urls = extract_media_urls(text, final_url)
        if include_frames:
            for frame in IFRAME_RE.findall(_normalise_embedded_text(text))[:3]:
                frame_url = urljoin(final_url, frame)
                try:
                    frame_report = self.scan(frame_url, include_frames=False)
                    urls.extend(item.url for item in frame_report.candidates)
                    diagnostics.extend(frame_report.diagnostics)
                except Exception:
                    continue

        candidates: list[MediaCandidate] = []
        unique_urls: list[str] = []
        seen: set[str] = set()
        drm_detected = False
        for url in urls[:40]:
            if url in seen:
                continue
            seen.add(url)
            unique_urls.append(url)
        with ThreadPoolExecutor(max_workers=min(8, len(unique_urls) or 1), thread_name_prefix="arena-probe") as executor:
            futures = [executor.submit(self.probe, url, final_url) for url in unique_urls]
            for future in as_completed(futures):
                candidate = future.result()
                if candidate is not None:
                    drm_detected = drm_detected or candidate.drm
                    candidates.append(candidate)
        diagnostics.insert(0, f"HTML/脚本扫描发现 {len(candidates)} 个媒体候选")
        if drm_detected:
            diagnostics.append("检测到受保护媒体清单，已跳过 DRM 候选")
        return DiscoveryReport(candidates, diagnostics, drm_detected)

    def probe(self, url: str, referer: str, source: str = "html-scan") -> MediaCandidate | None:
        response = None
        try:
            response, final_url = fetch_upstream(url, referer)
            content_type = response.headers.get("Content-Type", "")
            kind = media_kind(final_url, content_type)
            if kind in {"hls", "dash"}:
                manifest = _read_limited(response, MAX_MANIFEST_BYTES).decode(response.encoding or "utf-8", errors="replace")
                drm = detect_manifest_drm(manifest)
            else:
                drm = False
            if not kind:
                return None
            return MediaCandidate(final_url, kind, source, referer, content_type, drm)
        except Exception:
            return None
        finally:
            if response is not None:
                response.close()


class BrowserNetworkScanner:
    def __init__(self, observe_ms: int = 7000):
        self.observe_ms = max(2000, min(observe_ms, 15000))

    def scan(self, page_url: str) -> DiscoveryReport:
        if sync_playwright is None:
            return DiscoveryReport([], ["未安装 Playwright，跳过浏览器网络观察"])
        if getattr(sys, "frozen", False) and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                # PyInstaller otherwise forces Playwright to look for a browser
                # inside its temporary one-file extraction directory.  The
                # setup script installs Chromium in Playwright's normal cache.
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(Path(local_app_data) / "ms-playwright")
        validate_public_http_url(page_url)
        captured: dict[str, tuple[str, str]] = {}
        drm_detected = False
        diagnostics: list[str] = []
        try:
            with sync_playwright() as runtime:
                browser = runtime.chromium.launch(
                    headless=True,
                    args=["--autoplay-policy=no-user-gesture-required", "--disable-background-networking"],
                )
                context = browser.new_context(user_agent=USER_AGENT, locale="zh-CN", ignore_https_errors=False)
                page = context.new_page()
                validated_hosts: dict[str, bool] = {}

                def guard_route(route):
                    request_url = route.request.url
                    parsed = urlparse(request_url)
                    if parsed.scheme not in {"http", "https"}:
                        route.continue_()
                        return
                    host = parsed.hostname or ""
                    allowed = validated_hosts.get(host)
                    if allowed is None:
                        try:
                            validate_public_http_url(request_url)
                            allowed = True
                        except Exception:
                            allowed = False
                        validated_hosts[host] = allowed
                    route.continue_() if allowed else route.abort()

                page.route("**/*", guard_route)

                def on_request(request):
                    nonlocal drm_detected
                    url = request.url
                    lowered = url.casefold()
                    if any(term in lowered for term in LICENSE_TERMS):
                        drm_detected = True
                    kind = media_kind(url)
                    if kind:
                        captured[url] = (kind, "")

                def on_response(response):
                    nonlocal drm_detected
                    try:
                        content_type = response.headers.get("content-type", "")
                        kind = media_kind(response.url, content_type)
                        if kind:
                            captured[response.url] = (kind, content_type)
                        if any(term in response.url.casefold() for term in LICENSE_TERMS):
                            drm_detected = True
                    except Exception:
                        pass

                page.on("request", on_request)
                page.on("response", on_response)
                page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
                try:
                    page.locator("video").first.click(timeout=1000)
                except Exception:
                    pass
                page.wait_for_timeout(self.observe_ms)
                context.close()
                browser.close()
        except Exception as exc:
            return DiscoveryReport([], [f"浏览器网络观察失败：{exc}"], drm_detected)

        candidates = [
            MediaCandidate(url, kind, "browser-network", page_url, content_type)
            for url, (kind, content_type) in captured.items()
            if url.startswith(("http://", "https://"))
        ]
        diagnostics.append(f"无痕 Chromium 观察到 {len(candidates)} 个媒体请求")
        if drm_detected:
            diagnostics.append("观察到 DRM/许可证请求；不会获取或处理许可证")
        return DiscoveryReport(candidates, diagnostics, drm_detected)
