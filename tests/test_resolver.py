import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resolver import ResolveError, StreamResolver, media_kind, official_cctv_live_url, youtube_video_id


class UnsupportedYDL:
    options = None

    def __init__(self, options):
        type(self).options = options

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def extract_info(self, *_args, **_kwargs):
        self.options["logger"].error("ERROR: Unsupported URL")
        raise RuntimeError("Unsupported URL")


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = StreamResolver()

    def test_youtube_uses_official_embed(self):
        result = self.resolver.resolve("https://www.youtube.com/watch?v=abc123xyz")
        self.assertEqual(result.kind, "embed")
        self.assertIn("youtube-nocookie.com/embed/abc123xyz", result.playback_url)

    def test_cctv5_uses_official_page_without_extracting_media(self):
        result = self.resolver.resolve("https://tv.cctv.com/live/cctv5/m/")
        self.assertEqual(result.kind, "external")
        self.assertEqual(result.engine, "cctv-official")
        self.assertEqual(result.playback_url, "https://tv.cctv.com/live/cctv5/")

    def test_cctv_url_match_is_limited_to_official_live_channels(self):
        self.assertEqual(official_cctv_live_url("https://tv.cctv.com/live/cctv5plus/sd/"), "https://tv.cctv.com/live/cctv5plus/")
        self.assertIsNone(official_cctv_live_url("https://example.com/live/cctv5/"))

    def test_direct_hls(self):
        result = self.resolver.resolve("https://cdn.example.com/live/index.m3u8?token=1")
        self.assertEqual(result.kind, "hls")
        self.assertEqual(result.engine, "direct")

    def test_direct_dash_without_drm(self):
        scanner = type("Scanner", (), {"probe": lambda *_args, **_kwargs: SimpleNamespace(drm=False)})()
        result = StreamResolver(page_scanner=scanner).resolve("https://cdn.example.com/live/manifest.mpd")
        self.assertEqual(result.kind, "dash")
        self.assertEqual(result.engine, "direct")

    def test_direct_dash_with_drm_is_rejected(self):
        scanner = type("Scanner", (), {"probe": lambda *_args, **_kwargs: SimpleNamespace(drm=True)})()
        with self.assertRaisesRegex(ResolveError, "DRM"):
            StreamResolver(page_scanner=scanner).resolve("https://cdn.example.com/live/manifest.mpd")

    def test_unverified_direct_dash_is_rejected(self):
        scanner = type("Scanner", (), {"probe": lambda *_args, **_kwargs: None})()
        with self.assertRaisesRegex(ResolveError, "无法读取并验证"):
            StreamResolver(page_scanner=scanner).resolve("https://cdn.example.com/live/manifest.mpd")

    def test_invalid_scheme_is_rejected(self):
        with self.assertRaises(ResolveError):
            self.resolver.resolve("file:///etc/passwd")

    def test_helpers(self):
        self.assertEqual(youtube_video_id("https://youtu.be/abc123xyz"), "abc123xyz")
        self.assertEqual(media_kind("https://cdn.example/video.mp4"), "native")
        self.assertEqual(media_kind("https://cdn.example/manifest.mpd"), "dash")

    def test_ytdlp_unsupported_url_is_a_silent_fallback(self):
        fake_module = type("FakeYTDLP", (), {"YoutubeDL": UnsupportedYDL})
        with patch("resolver.yt_dlp", fake_module):
            self.assertIsNone(self.resolver._resolve_ytdlp("https://example.com/live"))
        self.assertIsNotNone(UnsupportedYDL.options.get("logger"))


if __name__ == "__main__":
    unittest.main()
