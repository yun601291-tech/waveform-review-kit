#!/usr/bin/env python3
"""Capture the real Waveform Review Kit browser UI with synthetic demo data.

Optional dependency: Playwright + installed Chromium. Does not load private data.
"""
from __future__ import annotations

import argparse
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import load_manifest, make_handler  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("demo-screenshot.png"),
        help="PNG output; default is demo-screenshot.png",
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise SystemExit(
            "Playwright is optional. Install with 'python -m pip install playwright' "
            "and 'python -m playwright install chromium'."
        ) from error

    demo_root = ROOT / "examples" / "demo"
    manifest = load_manifest(demo_root)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), make_handler(demo_root, manifest)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    viewport={"width": 1440, "height": 1000},
                    device_scale_factor=1,
                )
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/",
                    wait_until="networkidle",
                )
                page.locator("#viewer").wait_for(state="visible")
                page.locator("#waveformImage").evaluate(
                    "(image) => image.decode()"
                )
                output.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(output), full_page=True)
                print(f"Captured the synthetic demo UI: {output}")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


if __name__ == "__main__":
    main()
