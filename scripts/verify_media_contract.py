#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.ffmpeg_tools import find_ffmpeg, find_ffprobe  # noqa: E402


TEST_URL = "https://www.koushare.com/video/details/203628"
CONTRACTS = (
    ("video", "MKV", "video", ".mkv", {"video", "audio"}),
    ("audio", "MP3", "audio", ".mp3", {"audio"}),
    ("cover", "JPG", "image", ".jpg", {"video"}),
)


class FixtureServer(ThreadingHTTPServer):
    fixture_dir: Path
    base_url: str


class KoushareFixtureHandler(BaseHTTPRequestHandler):
    server: FixtureServer

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/video/v1/video/info":
            self._send_json({"success": True, "data": {"title": "Koushare HLS fixture"}})
            return
        if path == "/video/v1/video/getVideoPlayAddress":
            self._send_json(
                {
                    "success": True,
                    "data": [
                        {
                            "list": [
                                {
                                    "labelEn": "FHD",
                                    "height": 180,
                                    "fileUrl": f"{self.server.base_url}/hls/media.m3u8",
                                }
                            ]
                        }
                    ],
                }
            )
            return
        if path.startswith("/hls/"):
            self._send_file(self.server.fixture_dir / Path(path).name)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        if path == "/video/v1/video/checkVideoAuth":
            self._send_json({"success": True, "data": {"secret": "fixture-secret"}})
            return
        self.send_error(404)

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        content_type = (
            "application/vnd.apple.mpegurl" if path.suffix == ".m3u8" else "video/mp2t"
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Koushare HLS and FFmpeg contracts without external media."
    )
    parser.add_argument(
        "--mode",
        choices=("source", "packaged", "both"),
        default="both",
    )
    parser.add_argument("--sidecar", type=Path)
    args = parser.parse_args()

    ffmpeg = _required_tool(find_ffmpeg(), "ffmpeg")
    ffprobe = _required_tool(find_ffprobe(), "ffprobe")
    packaged = args.sidecar or _packaged_sidecar()
    if args.mode in {"packaged", "both"} and not packaged.is_file():
        raise SystemExit(f"Packaged sidecar was not found: {packaged}")

    with tempfile.TemporaryDirectory(prefix="douyingo-media-contract-") as temp_dir:
        root = Path(temp_dir)
        fixture_dir = root / "hls"
        fixture_dir.mkdir()
        _generate_hls(ffmpeg, fixture_dir)

        server = FixtureServer(("127.0.0.1", 0), KoushareFixtureHandler)
        server.fixture_dir = fixture_dir
        server.base_url = f"http://127.0.0.1:{server.server_port}"
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            if args.mode in {"source", "both"}:
                _verify_sidecar(
                    "source",
                    [sys.executable, "-m", "backend.sidecar"],
                    server.base_url,
                    root / "source",
                    ffprobe,
                    expect_bundled=False,
                )
            if args.mode in {"packaged", "both"}:
                _verify_sidecar(
                    "packaged",
                    [str(packaged.resolve())],
                    server.base_url,
                    root / "packaged",
                    ffprobe,
                    expect_bundled=True,
                )
        finally:
            server.shutdown()
            server.server_close()

    verified = "source and packaged" if args.mode == "both" else args.mode
    print(f"{verified.capitalize()} media contract verification passed.")
    return 0


def _generate_hls(ffmpeg: str, fixture_dir: Path) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=320x180:rate=24",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:sample_rate=48000",
        "-t",
        "2",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-f",
        "hls",
        "-hls_time",
        "1",
        "-hls_list_size",
        "0",
        "-hls_segment_filename",
        str(fixture_dir / "segment-%03d.ts"),
        str(fixture_dir / "media.m3u8"),
    ]
    _run(command, "FFmpeg could not generate the local HLS fixture")
    if not (fixture_dir / "media.m3u8").is_file():
        raise RuntimeError("FFmpeg did not produce the local HLS playlist")


def _verify_sidecar(
    label: str,
    command_prefix: list[str],
    api_base: str,
    root: Path,
    ffprobe: str,
    expect_bundled: bool,
) -> None:
    data_dir = root / "data"
    downloads_dir = root / "downloads"
    data_dir.mkdir(parents=True)
    downloads_dir.mkdir(parents=True)
    port = _free_port()
    log_path = root / "sidecar.log"
    env = os.environ.copy()
    env.update(
        {
            "DOUYINGO_DATA_DIR": str(data_dir),
            "DOUYINGO_DOWNLOADS_DIR": str(downloads_dir),
            "DOUYINGO_KOUSHARE_API_BASE": api_base,
        }
    )
    command = [
        *command_prefix,
        "serve",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]

    with log_path.open("w", encoding="utf-8") as log_file:
        sentinel = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(3600)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process: subprocess.Popen[str] | None = None
        try:
            command.extend(["--parent-pid", str(sentinel.pid)])
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )
            base_url = f"http://127.0.0.1:{port}"
            _wait_for_health(base_url, process, log_path)
            tools = _request_json(f"{base_url}/api/tools")
            bundled = {
                item["name"]: bool(item.get("details", {}).get("bundled"))
                for item in tools
                if item["name"] in {"ffmpeg", "ffprobe", "deno"}
            }
            if expect_bundled and bundled != {"ffmpeg": True, "ffprobe": True, "deno": True}:
                raise AssertionError(f"Packaged tools are not bundled: {bundled}")

            for download_type, output_format, file_type, suffix, expected_streams in CONTRACTS:
                output_dir = downloads_dir / download_type
                payload = {
                    "text": TEST_URL,
                    "platform": "koushare",
                    "options": {
                        "quality": "best",
                        "format": output_format,
                        "download_type": download_type,
                        "save_metadata": True,
                        "output_dir": str(output_dir),
                    },
                }
                job = _request_json(f"{base_url}/api/downloads", "POST", payload)
                job = _wait_for_job(base_url, job["id"], process, log_path)
                if job["status"] != "success":
                    raise AssertionError(f"{label} {download_type} failed: {job}")

                files = job["downloaded_files"]
                media = next((item for item in files if item["type"] == file_type), None)
                metadata = next((item for item in files if item["type"] == "metadata"), None)
                if media is None or metadata is None:
                    raise AssertionError(f"{label} {download_type} output contract failed: {files}")
                media_path = Path(media["path"])
                if media_path.suffix.lower() != suffix or not media_path.is_file():
                    raise AssertionError(f"Unexpected {label} media output: {media_path}")
                if not Path(metadata["path"]).is_file():
                    raise AssertionError(f"Missing {label} metadata output: {metadata}")
                streams = _probe_streams(ffprobe, media_path)
                if not expected_streams.issubset(streams):
                    raise AssertionError(
                        f"{label} {download_type} streams {streams} do not include {expected_streams}"
                    )
                print(
                    f"{label}: {download_type}/{output_format} -> "
                    f"{media_path.name} ({media_path.stat().st_size} bytes, {sorted(streams)})"
                )
        except Exception:
            log_file.flush()
            print(log_path.read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
            raise
        finally:
            _stop_process_tree(process, sentinel, port)


def _wait_for_health(base_url: str, process: subprocess.Popen[str], log_path: Path) -> None:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Sidecar exited with {process.returncode}: "
                f"{log_path.read_text(encoding='utf-8', errors='replace')}"
            )
        try:
            health = _request_json(f"{base_url}/health")
            if health.get("ok"):
                return
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for sidecar at {base_url}")


def _wait_for_job(
    base_url: str,
    job_id: str,
    process: subprocess.Popen[str],
    log_path: Path,
) -> dict[str, Any]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Sidecar exited with {process.returncode}: "
                f"{log_path.read_text(encoding='utf-8', errors='replace')}"
            )
        job = _request_json(f"{base_url}/api/downloads/{job_id}")
        if job["status"] in {"success", "error", "cancelled"}:
            return job
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for download job {job_id}")


def _request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _probe_streams(ffprobe: str, path: Path) -> set[str]:
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {completed.stderr}")
    payload = json.loads(completed.stdout)
    return {stream["codec_type"] for stream in payload.get("streams", [])}


def _stop_process_tree(
    process: subprocess.Popen[str] | None,
    sentinel: subprocess.Popen[bytes],
    port: int,
) -> None:
    if sentinel.poll() is None:
        sentinel.terminate()
        try:
            sentinel.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sentinel.kill()
            sentinel.wait(timeout=5)

    deadline = time.monotonic() + 5
    while _port_is_open(port) and time.monotonic() < deadline:
        time.sleep(0.2)

    if process is not None and process.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            process.terminate()

    if os.name == "nt" and _port_is_open(port):
        listener_pid = _windows_listener_pid(port)
        if listener_pid:
            subprocess.run(
                ["taskkill", "/PID", str(listener_pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    if process is not None:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    deadline = time.monotonic() + 5
    while _port_is_open(port) and time.monotonic() < deadline:
        time.sleep(0.2)
    if _port_is_open(port):
        raise RuntimeError(f"Sidecar listener on port {port} did not stop")


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _windows_listener_pid(port: int) -> int | None:
    completed = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    for line in completed.stdout.splitlines():
        fields = line.split()
        if (
            len(fields) == 5
            and fields[0] == "TCP"
            and fields[1] == f"127.0.0.1:{port}"
            and fields[3] == "LISTENING"
            and fields[4].isdigit()
        ):
            return int(fields[4])
    return None


def _packaged_sidecar() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    matches = sorted(
        (PROJECT_ROOT / "src-tauri" / "binaries").glob(f"douyingo-sidecar-*{suffix}")
    )
    return matches[0] if len(matches) == 1 else Path()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _required_tool(path: str | None, name: str) -> str:
    if not path:
        raise SystemExit(f"{name} is required for media contract verification")
    return path


def _run(command: list[str], message: str) -> None:
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{message}: {completed.stderr or completed.stdout}")


if __name__ == "__main__":
    raise SystemExit(main())
