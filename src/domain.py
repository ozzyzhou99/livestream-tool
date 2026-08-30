"""Shared domain objects for search and playback."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Sport = Literal["all", "football", "basketball", "f1", "nfl"]
LiveStatus = Literal["live", "upcoming", "replay", "unknown"]
PlaybackKind = Literal["embed", "external", "hls", "dash", "flv", "native"]


@dataclass(slots=True)
class SearchResult:
    id: str
    title: str
    url: str
    provider: str
    channel: str = ""
    thumbnail: str = ""
    sport: Sport = "all"
    live_status: LiveStatus = "unknown"
    viewers: int | None = None
    description: str = ""
    source_type: str = "platform"
    score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ResolvedStream:
    source_url: str
    playback_url: str
    kind: PlaybackKind
    title: str = ""
    referer: str = ""
    engine: str = "direct"
    diagnostics: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)
