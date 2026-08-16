import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search import YouTubeSearchProvider, detect_sport, video_platform_status


class FakeYDL:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def extract_info(self, query, download=False):
        self.query = query
        return {
            "entries": [
                {
                    "id": "abc123xyz",
                    "title": "Formula 1 Grand Prix Live",
                    "url": "abc123xyz",
                    "channel": "Official Sports",
                    "live_status": "is_live",
                    "thumbnail": "https://img.example/thumb.jpg",
                    "concurrent_view_count": 4200,
                },
                {"id": "abc123xyz", "title": "duplicate", "url": "abc123xyz"},
            ]
        }


class SearchTests(unittest.TestCase):
    def test_search_normalises_and_deduplicates_results(self):
        provider = YouTubeSearchProvider(ydl_factory=FakeYDL)
        results = provider.search("Monaco", "f1", 10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://www.youtube.com/watch?v=abc123xyz")
        self.assertEqual(results[0].live_status, "live")
        self.assertEqual(results[0].sport, "f1")

    def test_url_input_becomes_direct_result(self):
        provider = YouTubeSearchProvider(ydl_factory=FakeYDL)
        result = provider.search("https://example.com/live", "football", 10)[0]
        self.assertEqual(result.provider, "网页地址")
        self.assertEqual(result.url, "https://example.com/live")

    def test_detect_sport(self):
        self.assertEqual(detect_sport("NBA Finals live"), "basketball")
        self.assertEqual(detect_sport("unknown event", "football"), "football")

    def test_old_video_title_does_not_override_platform_replay_state(self):
        entry = {
            "title": "昨晚足球直播完整版",
            "live_status": "not_live",
            "duration": 7200,
        }
        self.assertEqual(video_platform_status(entry), "replay")


if __name__ == "__main__":
    unittest.main()
