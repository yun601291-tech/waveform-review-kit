#!/usr/bin/env python3
"""Serve a local waveform-review project with no third-party dependencies."""

from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

APP_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = APP_ROOT / "static"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the local Waveform Review Kit web application."
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=APP_ROOT / "examples" / "demo",
        help="Project directory containing project.json and assets/.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Listening host.")
    parser.add_argument("--port", type=int, default=8765, help="Listening port.")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the review page in the default browser after startup.",
    )
    return parser.parse_args()


def safe_file(root: Path, relative: str) -> Path | None:
    root = root.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def load_manifest(project_root: Path) -> dict:
    manifest_path = project_root / "project.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing project manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("items"), list):
        raise ValueError("project.json must contain an items array")
    if not manifest.get("labels"):
        raise ValueError("project.json must contain at least one decision label")
    return manifest


def make_handler(project_root: Path, manifest: dict):
    manifest_bytes = json.dumps(
        manifest, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        server_version = "WaveformReviewKit/1.0"

        def do_HEAD(self) -> None:
            self._serve(send_body=False)

        def do_GET(self) -> None:
            self._serve(send_body=True)

        def _send(self, payload: bytes, mime: str, send_body: bool) -> None:
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if send_body:
                self.wfile.write(payload)

        def _serve_file(self, path: Path, send_body: bool) -> None:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if path.suffix.lower() in {".js", ".css", ".json", ".svg"}:
                mime += "; charset=utf-8"
            self._send(path.read_bytes(), mime, send_body)

        def _serve(self, send_body: bool) -> None:
            path = unquote(urlsplit(self.path).path)
            if path in {"/", "/index.html"}:
                self._serve_file(STATIC_ROOT / "index.html", send_body)
                return
            if path == "/project.json":
                self._send(manifest_bytes, "application/json; charset=utf-8", send_body)
                return
            if path == "/health":
                payload = json.dumps(
                    {
                        "status": "ok",
                        "project_id": manifest.get("project_id", ""),
                        "items": len(manifest["items"]),
                        "read_only": True,
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
                self._send(payload, "application/json; charset=utf-8", send_body)
                return
            if path.startswith("/static/"):
                file_path = safe_file(STATIC_ROOT, path.removeprefix("/static/"))
            elif path.startswith("/assets/"):
                file_path = safe_file(project_root / "assets", path.removeprefix("/assets/"))
            elif path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            else:
                file_path = None
            if file_path is None:
                self.send_error(404)
                return
            self._serve_file(file_path, send_body)

        def log_message(self, fmt: str, *args) -> None:
            print(f"{self.address_string()} - {fmt % args}")

    return Handler


def main() -> None:
    args = parse_args()
    project_root = args.project.expanduser().resolve()
    manifest = load_manifest(project_root)
    server = ThreadingHTTPServer(
        (args.host, args.port), make_handler(project_root, manifest)
    )
    host_for_url = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    url = f"http://{host_for_url}:{server.server_port}/"
    print(f"Waveform Review Kit: {url}", flush=True)
    print(f"Project: {project_root}", flush=True)
    print("Decisions stay in this browser until exported or cleared.", flush=True)
    if args.open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
