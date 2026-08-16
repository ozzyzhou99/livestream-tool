import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain import ResolvedStream, SearchResult
from server import create_server, write_client_chunk


class FakeSearch:
    def search(self, query, sport, limit, deep=True):
        return [SearchResult(id="1", title="Test Live", url="https://example.com/live.m3u8", provider="test", sport=sport)]


class FakeResolver:
    def resolve(self, url, deep=True):
        return ResolvedStream(source_url=url, playback_url=url, kind="hls", engine="test")


class AbortedWriter:
    def write(self, _data):
        raise ConnectionAbortedError(10053, "client disconnected")


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, search_service=FakeSearch(), resolver=FakeResolver())
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get_json(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_health(self):
        self.assertTrue(self.get_json("/api/health")["ok"])

    def test_search(self):
        payload = self.get_json("/api/search?q=test&sport=football")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["sport"], "football")

    def test_resolve(self):
        request = Request(
            self.base + "/api/resolve",
            data=json.dumps({"url": "https://example.com/live.m3u8"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["kind"], "hls")
        self.assertIn("/api/proxy?url=", payload["proxy_url"])

    def test_static_index(self):
        with urlopen(self.base + "/", timeout=3) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertIn("ARENA", body)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', body)

    def test_client_disconnect_is_not_raised(self):
        self.assertFalse(write_client_chunk(AbortedWriter(), b"media"))


if __name__ == "__main__":
    unittest.main()
