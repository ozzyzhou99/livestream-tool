import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from discovery import detect_manifest_drm, extract_media_urls, media_kind


class DiscoveryTests(unittest.TestCase):
    def test_extracts_absolute_escaped_and_relative_media(self):
        page = r'''
        <video src="/media/live.flv"></video>
        <script>window.player={"play_url":"https:\/\/cdn.example.com\/a\/index.m3u8?token=1"}</script>
        '''
        urls = extract_media_urls(page, "https://site.example/watch/1")
        self.assertIn("https://site.example/media/live.flv", urls)
        self.assertIn("https://cdn.example.com/a/index.m3u8?token=1", urls)

    def test_detects_widevine_and_sample_aes(self):
        self.assertTrue(detect_manifest_drm('<ContentProtection schemeIdUri="urn:uuid:edef8ba9"/>'))
        self.assertTrue(detect_manifest_drm('#EXT-X-KEY:METHOD=SAMPLE-AES,URI="key"'))
        self.assertFalse(detect_manifest_drm('#EXT-X-KEY:METHOD=AES-128,KEYFORMAT="identity",URI="key"'))

    def test_media_kind_from_url_and_content_type(self):
        self.assertEqual(media_kind("https://cdn.example/live.m3u8"), "hls")
        self.assertEqual(media_kind("https://cdn.example/play", "video/x-flv"), "flv")
        self.assertEqual(media_kind("https://cdn.example/manifest.mpd"), "dash")


if __name__ == "__main__":
    unittest.main()
