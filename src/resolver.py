"""Layered resolver for public, non-DRM live pages."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from discovery import BrowserNetworkScanner, PageMediaScanner, media_kind as discovered_kind
from domain import ResolvedStream
from ytdlp_support import SilentYTDLPLogger

try:
    from streamlink import Streamlink
except ImportError:  # pragma: no cover
    Streamlink = None

try:
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
CCTV_LIVE_HOSTS = {"tv.cctv.com"}


class ResolveError(RuntimeError):
    pass


def youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host not in YOUTUBE_HOSTS:
        return None
    if host.endswith("youtu.be"):
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    elif parsed.path.startswith(("/live/", "/shorts/", "/embed/")):
        candidate = parsed.path.strip("/").split("/")[-1]
    else:
        return None
    return candidate if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", candidate or "") else None


def media_kind(url: str) -> str | None:
    kind = discovered_kind(url)
    return kind if kind in {"hls", "dash", "flv", "native"} else None


def official_cctv_live_url(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in CCTV_LIVE_HOSTS:
        return None
    match = re.fullmatch(r"/live/(cctv(?:5|5plus))(?:/(?:m|sd))?/?(?:index\.shtml)?", parsed.path, re.IGNORECASE)
    if not match:
        return None
    return f"https://tv.cctv.com/live/{match.group(1).lower()}/"


class StreamResolver:
    def __init__(self, page_scanner=None, browser_scanner=None):
        self.page_scanner = page_scanner or PageMediaScanner()
        self.browser_scanner = browser_scanner or BrowserNetworkScanner()

    def resolve(self, url: str, deep: bool = True) -> ResolvedStream:
        url = url.strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ResolveError("请输入有效的 http(s) 直播页面或媒体地址。")

        official_url = official_cctv_live_url(url)
        if official_url:
            return ResolvedStream(
                source_url=url,
                playback_url=official_url,
                kind="external",
                engine="cctv-official",
                diagnostics=("央视频道使用官方播放器", "播放范围由央视按地区与赛事版权决定"),
            )

        video_id = youtube_video_id(url)
        if video_id:
            return ResolvedStream(
                source_url=url,
                playback_url=f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&playsinline=1",
                kind="embed",
                engine="youtube-embed",
                diagnostics=("识别为 YouTube，使用官方嵌入播放器",),
            )

        direct_kind = discovered_kind(url)
        if direct_kind == "dash":
            candidate = self.page_scanner.probe(url, f"{parsed.scheme}://{parsed.netloc}/", source="direct")
            if candidate is None:
                raise ResolveError("无法读取并验证 DASH 清单，已停止播放以避免处理未知的受保护媒体。")
            if candidate and candidate.drm:
                raise ResolveError("检测到 DRM 保护的 DASH 清单，工具不会获取许可证或解密。")
            return ResolvedStream(
                source_url=url,
                playback_url=url,
                kind="dash",
                referer=f"{parsed.scheme}://{parsed.netloc}/",
                engine="direct",
                diagnostics=("输入为无 DRM 的 MPEG-DASH 媒体地址",),
            )
        if direct_kind in {"hls", "flv", "native"}:
            if direct_kind == "hls":
                candidate = self.page_scanner.probe(url, f"{parsed.scheme}://{parsed.netloc}/", source="direct")
                if candidate and candidate.drm:
                    raise ResolveError("检测到 DRM/SAMPLE-AES 保护的 HLS 清单，已停止解析。")
            return ResolvedStream(
                source_url=url,
                playback_url=url,
                kind=direct_kind,
                referer=f"{parsed.scheme}://{parsed.netloc}/",
                diagnostics=("输入为直接媒体地址",),
            )

        diagnostics: list[str] = []
        stream = self._resolve_streamlink(url)
        if stream:
            return stream
        diagnostics.append("Streamlink 未返回可播放流")

        stream = self._resolve_ytdlp(url)
        if stream:
            return stream
        diagnostics.append("yt-dlp 未返回可播放流")

        static_report = self.page_scanner.scan(url)
        diagnostics.extend(static_report.diagnostics)
        stream = self._from_candidates(url, static_report.candidates, diagnostics)
        if stream:
            return stream

        if deep:
            browser_report = self.browser_scanner.scan(url)
            diagnostics.extend(browser_report.diagnostics)
            checked = []
            for candidate in browser_report.candidates[:12]:
                verified = self.page_scanner.probe(candidate.url, url, source="browser-network")
                if verified:
                    checked.append(verified)
            stream = self._from_candidates(url, checked, diagnostics)
            if stream:
                return stream
            if browser_report.drm_detected:
                raise ResolveError("页面发出了 DRM/许可证请求，已停止深度解析。")

        summary = "；".join(diagnostics[-4:])
        raise ResolveError(f"未找到可播放的公开直播流。{summary}" if summary else "未找到可播放的公开直播流。")

    @staticmethod
    def _from_candidates(source_url: str, candidates, diagnostics: list[str]) -> ResolvedStream | None:
        priority = {"hls": 0, "dash": 1, "native": 2, "flv": 3}
        playable = [item for item in candidates if not item.drm and item.kind in priority]
        playable.sort(key=lambda item: priority[item.kind])
        if not playable:
            return None
        item = playable[0]
        return ResolvedStream(
            source_url=source_url,
            playback_url=item.url,
            kind=item.kind,
            referer=item.referer,
            engine=item.source,
            diagnostics=tuple(diagnostics + [f"选择 {item.kind.upper()} 媒体候选"]),
        )

    def _resolve_streamlink(self, url: str) -> ResolvedStream | None:
        if Streamlink is None:
            return None
        try:
            session = Streamlink()
            session.set_option("http-timeout", 15)
            streams = session.streams(url)
            stream = streams.get("best") or next(iter(streams.values()), None)
            if not stream:
                return None
            stream_url = getattr(stream, "url", None) or stream.to_url()
            kind = media_kind(stream_url or "")
            if not stream_url or not kind:
                return None
            return ResolvedStream(
                source_url=url,
                playback_url=stream_url,
                kind=kind,
                referer=url,
                engine="streamlink",
                diagnostics=(f"Streamlink 识别站点并选择最佳画质",),
            )
        except Exception:
            return None

    def _resolve_ytdlp(self, url: str) -> ResolvedStream | None:
        if yt_dlp is None:
            return None
        options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 15,
            "format": "best[protocol^=m3u8]/best[ext=flv]/best[ext=mp4]/best",
            "logger": SilentYTDLPLogger(),
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            return None
        if not isinstance(info, dict):
            return None
        stream_url = info.get("url")
        kind = media_kind(stream_url) if isinstance(stream_url, str) else None
        if not stream_url or not kind:
            return None
        headers = info.get("http_headers") or {}
        return ResolvedStream(
            source_url=url,
            playback_url=stream_url,
            kind=kind,
            title=str(info.get("title") or ""),
            referer=str(headers.get("Referer") or url),
            engine="yt-dlp",
            diagnostics=("yt-dlp 提取到直接媒体地址",),
        )
