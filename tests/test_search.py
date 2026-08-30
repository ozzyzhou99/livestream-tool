import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search import BingSearchProvider, OfficialChannelProvider, PlatformSearchProvider, SearchService, YouTubeSearchProvider, detect_sport, video_platform_status


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


class FakeBingResponse:
    content = b"""<?xml version='1.0' encoding='utf-8'?>
    <rss><channel>
      <item><title>Arsenal Live Now</title><link>https://www.twitch.tv/arsenal</link><description>Official sports live stream</description></item>
      <item><title>Match report</title><link>https://example.com/report</link><description>News article</description></item>
    </channel></rss>"""

    def raise_for_status(self):
        return None


class SlowSearchProvider:
    def search(self, *_args, **_kwargs):
        time.sleep(0.1)
        return []


class SearchTests(unittest.TestCase):
    def test_bing_rss_results_include_live_room_source(self):
        calls = []

        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            return FakeBingResponse()

        provider = BingSearchProvider(http_get=fake_get)
        results = provider.search("Arsenal", "football", 10, deep=False)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].provider, "Bing · Twitch")
        self.assertEqual(results[0].source_type, "live-room-search")
        self.assertEqual(calls[0][1]["params"]["format"], "rss")

    def test_platform_search_links_are_query_specific(self):
        results = PlatformSearchProvider().search("阿森纳", "football", 10)
        self.assertEqual(len(results), 5)
        self.assertTrue(all(item.source_type == "platform-search" for item in results))
        self.assertIn("keyword=", results[0].url)
        self.assertIn("%E9%98%BF%E6%A3%AE%E7%BA%B3", results[0].url)

    def test_slow_provider_does_not_block_available_results(self):
        service = SearchService(providers=[PlatformSearchProvider(), SlowSearchProvider()])
        started = time.monotonic()
        with patch("search.SEARCH_PROVIDER_TIMEOUT", 0.01):
            results = service.search("阿森纳", "football", 10)
        self.assertLess(time.monotonic() - started, 0.08)
        self.assertTrue(any(item.source_type == "platform-search" for item in results))

    def test_official_cctv5_alias_returns_stable_channel(self):
        provider = OfficialChannelProvider()
        results = provider.search("央视五套", "all", 10)
        self.assertEqual([item.id for item in results], ["official-cctv5"])
        self.assertEqual(results[0].url, "https://tv.cctv.com/live/cctv5/")
        self.assertEqual(results[0].source_type, "official-channel")

    def test_empty_search_returns_official_channels_without_network(self):
        service = SearchService(providers=[])
        results = service.search("", "all", 10)
        self.assertEqual([item.id for item in results], ["official-cctv5", "official-cctv5plus"])

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
