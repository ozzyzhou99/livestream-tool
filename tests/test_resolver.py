import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resolver import ResolveError, StreamResolver, media_kind, youtube_video_id


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

    def test_direct_hls(self):
        result = self.resolver.resolve("https://cdn.example.com/live/index.m3u8?token=1")
        self.assertEqual(result.kind, "hls")
        self.assertEqual(result.engine, "direct")

    def test_invalid_scheme_is_rejected(self):
        with self.assertRaises(ResolveError):
            self.resolver.resolve("file:///etc/passwd")

    def test_helpers(self):
        self.assertEqual(youtube_video_id("https://youtu.be/abc123xyz"), "abc123xyz")
        self.assertEqual(media_kind("https://cdn.example/video.mp4"), "native")

    def test_ytdlp_unsupported_url_is_a_silent_fallback(self):
        fake_module = type("FakeYTDLP", (), {"YoutubeDL": UnsupportedYDL})
        with patch("resolver.yt_dlp", fake_module):
            self.assertIsNone(self.resolver._resolve_ytdlp("https://example.com/live"))
        self.assertIsNotNone(UnsupportedYDL.options.get("logger"))


if __name__ == "__main__":
    unittest.main()
