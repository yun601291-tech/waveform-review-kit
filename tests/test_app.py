from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = ROOT / "examples" / "demo"
        cls.manifest = app.load_manifest(cls.project)

    def test_demo_items_are_unique_and_have_existing_assets(self) -> None:
        ids = [item["id"] for item in self.manifest["items"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 5)
        for item in self.manifest["items"]:
            self.assertTrue(item["pages"])
            for page in item["pages"]:
                self.assertTrue((self.project / "assets" / page["image"]).is_file())

    def test_safe_file_blocks_directory_escape(self) -> None:
        self.assertIsNone(app.safe_file(self.project / "assets", "../project.json"))


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = ROOT / "examples" / "demo"
        cls.manifest = app.load_manifest(cls.project)
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), app.make_handler(cls.project, cls.manifest)
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def fetch(self, path: str):
        with urllib.request.urlopen(self.base + path, timeout=4) as response:
            return response.status, response.headers, response.read()

    def test_health(self) -> None:
        status, _, payload = self.fetch("/health")
        body = json.loads(payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["items"], len(self.manifest["items"]))
        self.assertTrue(body["read_only"])

    def test_main_manifest_and_asset(self) -> None:
        status, headers, html = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"Waveform Review Kit", html)

        status, _, payload = self.fetch("/project.json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["project_id"], "synthetic-waveform-demo")

        status, headers, image = self.fetch("/assets/review_clear.svg")
        self.assertEqual(status, 200)
        self.assertIn("image/svg+xml", headers["Content-Type"])
        self.assertTrue(image.startswith(b"<svg"))

    def test_unknown_and_traversal_paths_are_rejected(self) -> None:
        for path in ["/missing", "/assets/%2e%2e/project.json"]:
            with self.assertRaises(urllib.error.HTTPError) as context:
                self.fetch(path)
            self.assertEqual(context.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
