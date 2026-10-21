"""End-to-end checks for the CSV-to-project builder.

Uses only Python's standard library; all files are generated in temp dirs.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_project.py"


class ProjectBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.assets = self.base / "source"
        self.assets.mkdir()
        (self.assets / "waveform.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8"
        )
        self.input = self.base / "events.csv"
        self.output = self.base / "review"

    def write_csv(self, rows):
        with self.input.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=["id", "section", "image", "tags", "meta_time"]
            )
            writer.writeheader()
            writer.writerows(rows)

    def run_builder(self, *args):
        return subprocess.run(
            [
                sys.executable, str(BUILDER), "--csv", str(self.input),
                "--assets-root", str(self.assets),
                "--output", str(self.output),
                "--title", "Test review",
                *args,
            ],
            text=True, capture_output=True, check=False, timeout=20,
        )

    def test_creates_project_with_assets_and_metadata(self):
        self.write_csv([
            {
                "id": "EVT-001", "section": "review", "image": "waveform.svg",
                "tags": "P|S", "meta_time": "2026-01-01T00:00:00",
            },
            {
                "id": "REF-001", "section": "known", "image": "waveform.svg",
                "tags": "known", "meta_time": "",
            },
        ])
        result = self.run_builder()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.output / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(len(manifest["items"]), 2)
        self.assertEqual(manifest["items"][0]["tags"], ["P", "S"])
        self.assertEqual(manifest["items"][0]["metadata"]["time"], "2026-01-01T00:00:00")
        sections = {entry["id"]: entry for entry in manifest["sections"]}
        self.assertTrue(sections["review"]["reviewable"])
        self.assertFalse(sections["known"]["reviewable"])
        for item in manifest["items"]:
            for page in item["pages"]:
                self.assertTrue((self.output / "assets" / page["image"]).is_file())

    def test_duplicate_ids_are_rejected(self):
        row = {"id": "SAME", "section": "review", "image": "waveform.svg",
               "tags": "", "meta_time": ""}
        self.write_csv([row, row])
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate id", result.stderr)

    def test_path_escape_is_rejected(self):
        (self.base / "outside.svg").write_text("<svg/>", encoding="utf-8")
        self.write_csv([{"id": "EVT-1", "section": "review",
                         "image": "../outside.svg", "tags": "", "meta_time": ""}])
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escapes assets root", result.stderr)

    def test_missing_image_is_rejected(self):
        self.write_csv([{"id": "EVT-1", "section": "review",
                         "image": "not-here.svg", "tags": "", "meta_time": ""}])
        result = self.run_builder()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("image does not exist", result.stderr)

    def test_overwrite_requires_explicit_flag(self):
        self.write_csv([{"id": "EVT-1", "section": "review",
                         "image": "waveform.svg", "tags": "", "meta_time": ""}])
        self.assertEqual(self.run_builder().returncode, 0)
        blocked = self.run_builder()
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("--overwrite", blocked.stderr)
        allowed = self.run_builder("--overwrite")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)


if __name__ == "__main__":
    unittest.main()
