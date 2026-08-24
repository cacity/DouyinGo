#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Sidecar API smoke tests that do not perform network downloads."""

import sys

from fastapi.testclient import TestClient

from backend.app import app
from backend.schemas import Platform
from backend.url_utils import extract_url


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
    for name in {"python", "ffmpeg", "yt-dlp", "models-dir"}:
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


def main():
    test_url_resolution()
    test_api_health_and_inventory()
    test_invalid_download_request()
    print("Sidecar API smoke tests passed.")


if __name__ == "__main__":
    main()
