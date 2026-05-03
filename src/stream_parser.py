"""
流媒体URL解析模块
支持 streamlink（主要）和 yt-dlp（备选）两种解析引擎
"""
import re
from typing import Optional

# ── streamlink ───────────────────────────────────────────────────────────────
try:
    from streamlink import Streamlink
    from streamlink.exceptions import NoPluginError, PluginError
    STREAMLINK_OK = True
except ImportError:
    STREAMLINK_OK = False

# ── yt-dlp ───────────────────────────────────────────────────────────────────
try:
    import yt_dlp
    YTDLP_OK = True
except ImportError:
    YTDLP_OK = False


DIRECT_PATTERNS = [
    r"\.m3u8(\?|$|#)",
    r"\.flv(\?|$|#)",
    r"^rtmp://",
    r"^rtsp://",
    r"^mms://",
]


def is_direct_url(url: str) -> bool:
    for pat in DIRECT_PATTERNS:
        if re.search(pat, url, re.IGNORECASE):
            return True
    return False


# ── streamlink helpers ───────────────────────────────────────────────────────

def _sl_get_streams(url: str):
    """返回 (streams_dict | None, error_str | None)"""
    if not STREAMLINK_OK:
        return None, "streamlink 未安装，请运行 setup_conda.bat 配置环境"
    try:
        session = Streamlink()
        streams = session.streams(url)
        if not streams:
            return None, "未找到直播流，请确认直播正在进行中"
        return streams, None
    except NoPluginError:
        return None, "不支持该网站（streamlink无插件），将尝试备选引擎"
    except PluginError as e:
        return None, f"插件解析失败：{e}"
    except Exception as e:
        return None, f"streamlink 错误：{e}"


def _sl_stream_to_url(stream) -> Optional[str]:
    """从 streamlink stream 对象提取可直接播放的 URL"""
    url = getattr(stream, "url", None)
    if url:
        return url
    # RTMPStream 等特殊类型
    try:
        return stream.to_url()
    except Exception:
        return None


# ── yt-dlp helpers ───────────────────────────────────────────────────────────

def _ytdlp_get_url(url: str, quality: str = "best") -> tuple[Optional[str], Optional[str]]:
    if not YTDLP_OK:
        return None, "yt-dlp 未安装"

    fmt = "bestvideo[ext=mp4]+bestaudio/best" if quality == "best" else quality
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": fmt,
        "live_from_start": False,
        "skip_download": True,
        "nocheckcertificate": True,   # 跳过 SSL 证书验证
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if isinstance(info, dict):
                if "url" in info:
                    return info["url"], None
                formats = info.get("formats", [])
                if formats:
                    return formats[-1].get("url"), None
        return None, "yt-dlp 未能提取到播放地址"
    except Exception as e:
        err = str(e)
        if "certificate" in err.lower() or "ssl" in err.lower():
            return None, "SSL证书验证失败（已尝试跳过仍失败），该网站可能拒绝自动解析"
        return None, f"yt-dlp 错误：{err}"


def _ytdlp_get_qualities(url: str) -> tuple[Optional[list], Optional[str]]:
    if not YTDLP_OK:
        return None, "yt-dlp 未安装"
    opts = {"quiet": True, "no_warnings": True, "listformats": False,
            "skip_download": True, "nocheckcertificate": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if isinstance(info, dict):
                formats = info.get("formats", [])
                seen = set()
                qs = []
                for f in reversed(formats):
                    height = f.get("height")
                    label = f"{height}p" if height else f.get("format_note", "unknown")
                    if label not in seen:
                        seen.add(label)
                        qs.append(label)
                return (["最佳画质"] + qs) if qs else ["最佳画质"], None
        return ["最佳画质"], None
    except Exception as e:
        return None, f"yt-dlp 错误：{e}"


# ── 公共接口 ─────────────────────────────────────────────────────────────────

def get_qualities(url: str) -> tuple[Optional[list], Optional[str]]:
    """获取可用画质列表，返回 (qualities, error)"""
    if is_direct_url(url):
        return ["直接播放"], None

    streams, err = _sl_get_streams(url)
    if streams:
        order = ["best", "1080p60", "1080p", "720p60", "720p", "480p", "360p", "240p", "worst"]
        keys = list(streams.keys())
        result = [k for k in order if k in keys] + [k for k in keys if k not in order]
        # 本地化 best/worst 显示名
        display = []
        for k in result:
            if k == "best":
                display.append("最佳画质")
            elif k == "worst":
                display.append("最低画质")
            else:
                display.append(k)
        return display, None

    # streamlink 失败，尝试 yt-dlp
    qs, err2 = _ytdlp_get_qualities(url)
    if qs:
        return qs, None
    return None, err or err2


def get_stream_url(url: str, quality_display: str = "最佳画质") -> tuple[Optional[str], Optional[str]]:
    """获取实际播放地址，返回 (stream_url, error)"""
    if is_direct_url(url):
        return url, None

    # 画质显示名 → streamlink key
    quality_map = {"最佳画质": "best", "最低画质": "worst", "直接播放": "best"}
    sl_quality = quality_map.get(quality_display, quality_display)

    streams, err = _sl_get_streams(url)
    if streams:
        stream = streams.get(sl_quality) or streams.get("best") or next(iter(streams.values()), None)
        if stream:
            su = _sl_stream_to_url(stream)
            if su:
                return su, None

    # 备选：yt-dlp
    ytdlp_quality = "best" if quality_display in ("最佳画质", "直接播放") else quality_display
    su, err2 = _ytdlp_get_url(url, ytdlp_quality)
    if su:
        return su, None

    return None, err or err2 or "无法获取播放地址，请检查直播是否正在进行"


def available_engines() -> list[str]:
    engines = []
    if STREAMLINK_OK:
        engines.append("streamlink")
    if YTDLP_OK:
        engines.append("yt-dlp")
    return engines
