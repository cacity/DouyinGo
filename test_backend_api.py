#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Sidecar API smoke tests that do not perform network downloads."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend import runtime_paths
from backend.runtime_paths import data_root, download_root
from backend.schemas import Platform
from backend.sidecar import build_parser, process_is_running
from backend.url_utils import extract_url
from core.youtube_downloader import YouTubeDownloader


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def assert_equal(actual, expected, label: str):
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_url_resolution():
    cases = [
        ("抖音 https://v.douyin.com/abcd1234/ text", Platform.DOUYIN),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", Platform.YOUTUBE),
        ("tweet https://x.com/user/status/1234567890", Platform.TWITTER),
        ("https://www.koushare.com/video/details/203628", Platform.KOUSHARE),
    ]

    for text, platform in cases:
        resolved = extract_url(text)
        assert_equal(resolved.platform, platform, f"platform for {text}")
        assert_equal(resolved.supported, True, f"supported for {text}")


def test_api_health_and_inventory():
    client = TestClient(app)

    health = client.get("/health")
    assert_equal(health.status_code, 200, "health status")
    assert_equal(health.json()["ok"], True, "health ok")

    tools = client.get("/api/tools")
    assert_equal(tools.status_code, 200, "tools status")
    tool_names = {item["name"] for item in tools.json()}
    for name in {"python", "ffmpeg", "yt-dlp", "yt-dlp-ejs", "deno", "models-dir"}:
        if name not in tool_names:
            raise AssertionError(f"missing tool entry: {name}")

    models = client.get("/api/models")
    assert_equal(models.status_code, 200, "models status")
    if not isinstance(models.json(), list):
        raise AssertionError("models response must be a list")

    downloads = client.get("/api/downloads")
    assert_equal(downloads.status_code, 200, "downloads status")
    assert_equal(downloads.json(), [], "initial downloads")


def test_invalid_download_request():
    client = TestClient(app)
    response = client.post("/api/downloads", json={"text": "not a url"})
    assert_equal(response.status_code, 400, "invalid download status")


def test_sidecar_lifecycle_arguments():
    args = build_parser().parse_args(
        ["serve", "--host", "127.0.0.1", "--port", "12345", "--parent-pid", str(os.getpid())]
    )
    assert_equal(args.port, 12345, "sidecar port argument")
    assert_equal(args.parent_pid, os.getpid(), "sidecar parent pid argument")
    assert_equal(process_is_running(os.getpid()), True, "current process is running")


def test_youtube_packaged_runtime_options():
    with tempfile.TemporaryDirectory() as temp_dir:
        downloader = YouTubeDownloader(
            temp_dir,
            ffmpeg_path=str(Path(temp_dir) / "ffmpeg.exe"),
            deno_path=str(Path(temp_dir) / "deno.exe"),
        )
        options = downloader._runtime_options()
        assert_equal(options["ffmpeg_location"], str(Path(temp_dir) / "ffmpeg.exe"), "ffmpeg path")
        assert_equal(
            options["js_runtimes"],
            {"deno": {"path": str(Path(temp_dir) / "deno.exe")}},
            "deno runtime",
        )
        if "bestvideo" not in downloader._get_format_selector("best"):
            raise AssertionError("best quality must combine the best video and audio streams")
        if "height<=1080" not in downloader._get_format_selector("1080p"):
            raise AssertionError("1080p quality must apply a height limit")


def test_runtime_path_overrides():
    with tempfile.TemporaryDirectory() as temp_dir:
        downloads = Path(temp_dir) / "downloads"
        data = Path(temp_dir) / "data"
        with patch.dict(
            os.environ,
            {
                "DOUYINGO_DOWNLOADS_DIR": str(downloads),
                "DOUYINGO_DATA_DIR": str(data),
            },
        ):
            assert_equal(download_root(), downloads, "download root override")
            assert_equal(data_root(), data, "data root override")


def test_packaged_download_root_fallback():
    with tempfile.TemporaryDirectory() as temp_dir:
        home = Path(temp_dir) / "home"
        preferred = home / "Downloads" / "DouyinGo"
        preferred.parent.mkdir(parents=True)
        preferred.write_text("blocks directory creation", encoding="utf-8")
        data = Path(temp_dir) / "data"
        with (
            patch.dict(os.environ, {"DOUYINGO_DATA_DIR": str(data)}, clear=False),
            patch.object(runtime_paths, "is_frozen", return_value=True),
            patch.object(runtime_paths.Path, "home", return_value=home),
        ):
            assert_equal(download_root(), data / "downloads", "packaged download fallback")
            assert_equal((data / "downloads").is_dir(), True, "fallback directory exists")

        blocked_data = Path(temp_dir) / "blocked-data"
        blocked_data.write_text("blocks app-data fallback", encoding="utf-8")
        temp_fallback = Path(temp_dir) / "temp"
        with (
            patch.dict(os.environ, {"DOUYINGO_DATA_DIR": str(blocked_data)}, clear=False),
            patch.object(runtime_paths, "is_frozen", return_value=True),
            patch.object(runtime_paths.Path, "home", return_value=home),
            patch.object(runtime_paths.tempfile, "gettempdir", return_value=str(temp_fallback)),
        ):
            expected = temp_fallback / "DouyinGo" / "downloads"
            assert_equal(download_root(), expected, "sandboxed download fallback")
            assert_equal(expected.is_dir(), True, "sandboxed fallback directory exists")


def main():
    test_url_resolution()
    test_api_health_and_inventory()
    test_invalid_download_request()
    test_sidecar_lifecycle_arguments()
    test_youtube_packaged_runtime_options()
    test_runtime_path_overrides()
    test_packaged_download_root_fallback()
    print("Sidecar API smoke tests passed.")


if __name__ == "__main__":
    main()
