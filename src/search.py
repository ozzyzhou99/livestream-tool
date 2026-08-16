"""Parallel, Chinese-first live-stream search aggregation."""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from domain import SearchResult, Sport
from ytdlp_support import SilentYTDLPLogger

try:
    import yt_dlp
except ImportError:  # pragma: no cover
    yt_dlp = None

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover
    DDGS = None


SPORT_HINTS: dict[Sport, str] = {
    "all": "体育 赛事 sports",
    "football": "足球 football soccer",
    "basketball": "篮球 basketball NBA CBA",
    "f1": "F1 一级方程式 Formula 1 大奖赛",
    "nfl": "橄榄球 NFL American football",
}

SPORT_TERMS: dict[Sport, tuple[str, ...]] = {
    "football": ("football", "soccer", "premier league", "champions league", "英超", "欧冠", "中超", "足球"),
    "basketball": ("basketball", "nba", "wnba", "cba", "欧篮", "篮球"),
    "f1": ("formula 1", "formula one", "f1", "grand prix", "大奖赛", "一级方程式"),
    "nfl": ("nfl", "american football", "super bowl", "超级碗", "橄榄球"),
    "all": (),
}

CHINESE_LIVE_DOMAINS: tuple[str, ...] = (
    "live.bilibili.com",
    "douyu.com",
    "huya.com",
    "live.douyin.com",
    "yangshipin.cn",
    "cctv.com",
    "weibo.com",
    "kuaishou.com",
)

DOMAIN_LABELS = {
    "live.bilibili.com": "哔哩哔哩直播",
    "bilibili.com": "哔哩哔哩",
    "douyu.com": "斗鱼",
    "huya.com": "虎牙",
    "live.douyin.com": "抖音直播",
    "douyin.com": "抖音",
    "yangshipin.cn": "央视频",
    "cctv.com": "央视网",
    "weibo.com": "微博",
    "kuaishou.com": "快手",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "twitch.tv": "Twitch",
}

TRACKING_PARAMS = {"spm_id_from", "vd_source", "from", "source", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
LIVE_TERMS = ("直播中", "正在直播", "live now", " is live ", "现场直播", "🔴")
UPCOMING_TERMS = ("即将直播", "即将开始", "预约", "upcoming", "premieres")
REPLAY_TERMS = ("回放", "集锦", "录像", "highlights", "replay", "full match")


class SearchError(RuntimeError):
    pass


def detect_sport(text: str, fallback: Sport = "all") -> Sport:
    lowered = text.casefold()
    for sport, terms in SPORT_TERMS.items():
        if any(term.casefold() in lowered for term in terms):
            return sport
    return fallback


def infer_live_status(text: str, explicit: object = None, duration: object = None) -> str:
    if explicit == "is_live":
        return "live"
    if explicit == "is_upcoming":
        return "upcoming"
    if explicit in {"was_live", "post_live"}:
        return "replay"
    if explicit in {"not_live", "is_private"}:
        return "replay" if isinstance(duration, (int, float)) and duration > 0 else "unknown"
    lowered = f" {text.casefold()} "
    if any(term in lowered for term in UPCOMING_TERMS):
        return "upcoming"
    if any(term in lowered for term in LIVE_TERMS):
        return "live"
    if any(term in lowered for term in REPLAY_TERMS):
        return "replay"
    if isinstance(duration, (int, float)) and duration > 0:
        return "replay"
    return "unknown"


def video_platform_status(entry: dict) -> str:
    explicit = entry.get("live_status")
    if explicit == "is_live":
        return "live"
    if explicit == "is_upcoming":
        return "upcoming"
    if explicit in {"was_live", "post_live", "not_live"} or isinstance(entry.get("duration"), (int, float)):
        return "replay"
    return "unknown"


def canonical_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    netloc = host + (f":{parsed.port}" if parsed.port else "")
    query = urlencode([(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.casefold() not in TRACKING_PARAMS])
    return urlunparse((parsed.scheme.lower(), netloc, parsed.path.rstrip("/") or "/", "", query, ""))


def provider_for_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for domain, label in DOMAIN_LABELS.items():
        if host == domain or host.endswith(f".{domain}"):
            return label
    return host.removeprefix("www.") or "网页来源"


def _thumbnail(entry: dict) -> str:
    direct = entry.get("thumbnail") or entry.get("image")
    if isinstance(direct, str):
        return direct
    if isinstance(direct, dict):
        for value in reversed(list(direct.values())):
            if isinstance(value, str) and value.startswith("http"):
                return value
    images = entry.get("images") or entry.get("thumbnails") or []
    if isinstance(images, dict):
        images = list(images.values())
    for item in reversed(images):
        if isinstance(item, str):
            return item
        if isinstance(item, dict) and item.get("url"):
            return str(item["url"])
    return ""


def _network_message(exc: Exception) -> str:
    detail = str(exc).casefold()
    if any(term in detail for term in ("connection", "network", "socket", "timed out", "timeout", "winerror")):
        return "搜索引擎网络连接失败。"
    return "搜索引擎暂时不可用。"


class YouTubeSearchProvider:
    name = "YouTube"

    def __init__(self, ydl_factory=None):
        self._ydl_factory = ydl_factory

    def _create_ydl(self):
        if self._ydl_factory:
            return self._ydl_factory()
        if yt_dlp is None:
            raise SearchError("缺少 yt-dlp。")
        return yt_dlp.YoutubeDL({
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": "in_playlist",
            "socket_timeout": 15,
            "playlistend": 30,
            "logger": SilentYTDLPLogger(),
        })

    def search(self, query: str, sport: Sport = "all", limit: int = 18, deep: bool = False) -> list[SearchResult]:
        if URL_RE.match(query.strip()):
            parsed = urlparse(query.strip())
            return [SearchResult(
                id=hashlib.sha1(query.encode()).hexdigest()[:16],
                title=f"深度解析 {parsed.netloc}",
                url=query.strip(),
                provider="网页地址",
                channel="直接解析输入的网址",
                sport=sport,
                source_type="direct-input",
            )]
        request_count = min(max(limit * 2, 12), 30)
        terms = f"{query} {SPORT_HINTS.get(sport, '')} 直播 live".strip()
        try:
            with self._create_ydl() as ydl:
                payload = ydl.extract_info(f"ytsearch{request_count}:{terms}", download=False)
        except SearchError:
            raise
        except Exception as exc:
            raise SearchError(_network_message(exc)) from exc
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
        results: list[SearchResult] = []
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            video_id = str(entry.get("id") or "").strip()
            url = str(entry.get("webpage_url") or entry.get("url") or "").strip()
            if video_id and not URL_RE.match(url):
                url = f"https://www.youtube.com/watch?v={video_id}"
            if not URL_RE.match(url):
                continue
            key = canonical_url(url)
            if key in seen:
                continue
            seen.add(key)
            title = str(entry.get("title") or "未命名直播")
            results.append(SearchResult(
                id=video_id or hashlib.sha1(url.encode()).hexdigest()[:16],
                title=title,
                url=url,
                provider=self.name,
                channel=str(entry.get("channel") or entry.get("uploader") or ""),
                thumbnail=_thumbnail(entry),
                sport=detect_sport(title, sport),
                live_status=video_platform_status(entry),
                viewers=entry.get("concurrent_view_count") or entry.get("view_count"),
                source_type="video-search",
            ))
            if len(results) >= limit:
                break
        return results


class WebMetaSearchProvider:
    name = "中文全网搜索"

    def _ddgs(self):
        if DDGS is None:
            raise SearchError("缺少 ddgs 搜索组件。")
        return DDGS(timeout=12)

    def search(self, query: str, sport: Sport = "all", limit: int = 18, deep: bool = False) -> list[SearchResult]:
        terms = f"{query} {SPORT_HINTS.get(sport, '')} 直播".strip()
        rows: list[dict] = []
        try:
            jobs = [("videos", terms, min(limit, 20))]
            if deep:
                per_domain = max(2, min(4, limit // 5 or 2))
                jobs.append(("text", f"{query} {SPORT_HINTS.get(sport, '')} 直播 在线观看", min(12, limit)))
                jobs.extend(("text", f"{query} 直播 site:{domain}", per_domain) for domain in CHINESE_LIVE_DOMAINS)
            with ThreadPoolExecutor(max_workers=min(5, len(jobs)), thread_name_prefix="arena-meta") as executor:
                futures = []
                for kind, terms_value, count in jobs:
                    engine = self._ddgs()
                    method = engine.videos if kind == "videos" else engine.text
                    futures.append(executor.submit(method, terms_value, region="cn-zh", safesearch="moderate", max_results=count))
                for future in as_completed(futures):
                    try:
                        rows.extend(future.result())
                    except Exception:
                        continue
            if not rows:
                raise SearchError("中文全网搜索没有返回结果。")
        except Exception as exc:
            raise SearchError(_network_message(exc)) from exc

        results: list[SearchResult] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            url = str(row.get("content") or row.get("href") or row.get("url") or row.get("embed_url") or "").strip()
            if not URL_RE.match(url):
                continue
            title = str(row.get("title") or row.get("name") or provider_for_url(url))
            description = str(row.get("description") or row.get("body") or "")
            results.append(SearchResult(
                id=hashlib.sha1(canonical_url(url).encode()).hexdigest()[:16],
                title=title,
                url=url,
                provider=provider_for_url(url),
                channel=str(row.get("publisher") or ""),
                thumbnail=_thumbnail(row),
                sport=detect_sport(f"{title} {description}", sport),
                live_status=infer_live_status(f"{title} {description}"),
                description=description[:280],
                source_type="web-search",
            ))
        return results


class SearchService:
    def __init__(self, providers=None):
        self.providers = providers or [YouTubeSearchProvider(), WebMetaSearchProvider()]

    def search(self, query: str, sport: Sport = "all", limit: int = 30, deep: bool = True) -> list[SearchResult]:
        query = " ".join(query.split())[:120]
        limit = max(1, min(limit, 60))
        if sport not in SPORT_HINTS:
            sport = "all"
        if URL_RE.match(query):
            parsed = urlparse(query)
            return [SearchResult(
                id=hashlib.sha1(query.encode()).hexdigest()[:16],
                title=f"深度解析 {parsed.netloc or '直播页面'}",
                url=query,
                provider="网页地址",
                channel="Streamlink · yt-dlp · HTML · 浏览器网络观察",
                sport=sport,
                source_type="direct-input",
                score=1000,
            )]

        merged: dict[str, SearchResult] = {}
        errors: list[str] = []
        per_provider = min(30, max(12, limit))
        with ThreadPoolExecutor(max_workers=len(self.providers), thread_name_prefix="arena-search") as executor:
            futures = {executor.submit(provider.search, query, sport, per_provider, deep): provider for provider in self.providers}
            for future in as_completed(futures):
                try:
                    found = future.result()
                except SearchError as exc:
                    errors.append(str(exc))
                    continue
                for item in found:
                    key = canonical_url(item.url)
                    current = merged.get(key)
                    if current is None or (item.thumbnail and not current.thumbnail):
                        merged[key] = item

        if not merged and errors:
            raise SearchError("；".join(dict.fromkeys(errors)))
        results = list(merged.values())
        self._score(results, query)
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    @staticmethod
    def _score(results: list[SearchResult], query: str) -> None:
        tokens = [part.casefold() for part in re.split(r"\s+", query) if part]
        status_score = {"live": 120, "upcoming": 70, "unknown": 20, "replay": 0}
        for item in results:
            text = f"{item.title} {item.description} {item.channel}".casefold()
            score = float(status_score.get(item.live_status, 20))
            score += sum(18 for token in tokens if token in text)
            if item.thumbnail:
                score += 4
            if item.source_type == "video-search":
                score += 5
            if any(domain in item.url for domain in CHINESE_LIVE_DOMAINS):
                score += 8
            item.score = score
