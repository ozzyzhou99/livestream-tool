import socket
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from proxy import ProxyError, rewrite_hls_manifest, validate_public_http_url


class ProxyTests(unittest.TestCase):
    def test_rewrites_segments_and_uri_attributes(self):
        manifest = '#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key.bin"\nsegment-01.ts\n'
        output = rewrite_hls_manifest(manifest, "https://cdn.example/live/index.m3u8", "https://site.example/")
        self.assertIn("url=https%3A%2F%2Fcdn.example%2Flive%2Fkey.bin", output)
        self.assertIn("url=https%3A%2F%2Fcdn.example%2Flive%2Fsegment-01.ts", output)
        self.assertIn("referer=https%3A%2F%2Fsite.example%2F", output)

    @patch("proxy.socket.getaddrinfo")
    def test_private_network_target_is_rejected(self, getaddrinfo):
        getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
        with self.assertRaises(ProxyError):
            validate_public_http_url("http://localhost/media.m3u8")

    @patch("proxy.socket.getaddrinfo")
    def test_public_target_is_allowed(self, getaddrinfo):
        getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        self.assertEqual(validate_public_http_url("https://example.com/a"), "https://example.com/a")
        self.assertEqual(getaddrinfo.call_args.args[1], 443)

    @patch("proxy.socket.getaddrinfo")
    def test_http_uses_port_80_by_default(self, getaddrinfo):
        getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]
        validate_public_http_url("http://example.com/a")
        self.assertEqual(getaddrinfo.call_args.args[1], 80)


if __name__ == "__main__":
    unittest.main()
