"""Safe loopback media proxy and HLS manifest rewriting helpers."""

from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import quote, urljoin, urlparse

import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
URI_ATTRIBUTE_RE = re.compile(r'URI="([^"]+)"')


class ProxyError(RuntimeError):
    pass


def validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ProxyError("仅支持公开的 http(s) 媒体地址。")
    try:
        default_port = 443 if parsed.scheme == "https" else 80
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or default_port)}
    except socket.gaierror as exc:
        raise ProxyError("媒体主机无法解析。") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ProxyError("出于安全原因，不能代理本机或私有网络地址。")
    return url


def proxy_url(target_url: str, referer: str = "") -> str:
    value = f"/api/proxy?url={quote(target_url, safe='')}"
    if referer:
        value += f"&referer={quote(referer, safe='')}"
    return value


def rewrite_hls_manifest(manifest: str, manifest_url: str, referer: str = "") -> str:
    def wrapped(value: str) -> str:
        absolute = urljoin(manifest_url, value)
        return proxy_url(absolute, referer)

    output: list[str] = []
    for line in manifest.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            output.append(wrapped(stripped))
            continue
        if "URI=\"" in line:
            line = URI_ATTRIBUTE_RE.sub(lambda match: f'URI="{wrapped(match.group(1))}"', line)
        output.append(line)
    return "\n".join(output) + ("\n" if manifest.endswith(("\n", "\r")) else "")


def fetch_upstream(url: str, referer: str = "", range_header: str = "", max_redirects: int = 5):
    current = url
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if referer:
        headers["Referer"] = referer
    if range_header:
        headers["Range"] = range_header
    for _ in range(max_redirects + 1):
        validate_public_http_url(current)
        response = requests.get(
            current,
            headers=headers,
            stream=True,
            timeout=(8, 30),
            allow_redirects=False,
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise ProxyError("上游返回了无效重定向。")
            current = urljoin(current, location)
            continue
        response.raise_for_status()
        return response, current
    raise ProxyError("媒体地址重定向次数过多。")
