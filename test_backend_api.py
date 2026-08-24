#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Sidecar API smoke tests that do not perform network downloads."""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.ai_models import discover_ai_models, run_ai_postprocess
from backend.download_service import DownloadService
from backend.job_store import JobStore
from backend.media_postprocess import append_metadata_file, transform_downloaded_media
from backend import runtime_paths
from backend.runtime_paths import data_root, download_root, jobs_db_path
from backend.schemas import DownloadJob, DownloadOptions, DownloadRequest, JobStatus, Platform
from backend.sidecar import build_parser, process_is_running
from backend.url_utils import extract_url
from core.ytdlp_media import media_options, normalize_media_format
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
    if not isinstance(downloads.json(), list):
        raise AssertionError("downloads response must be a list")


def test_invalid_download_request():
    client = TestClient(app)
    response = client.post("/api/downloads", json={"text": "not a url"})
    assert_equal(response.status_code, 400, "invalid download status")

    invalid_format = client.post(
        "/api/downloads",
        json={
            "text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "platform": "youtube",
            "options": {"download_type": "audio", "format": "MP4"},
        },
    )
    assert_equal(invalid_format.status_code, 400, "invalid format status")

    invalid_model = client.post(
        "/api/downloads",
        json={
            "text": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "platform": "youtube",
            "options": {"ai_model_id": "missing-model"},
        },
    )
    assert_equal(invalid_model.status_code, 400, "invalid model status")


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
            assert_equal(jobs_db_path(), data / "jobs.sqlite3", "jobs database override")


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


def test_media_option_contract():
    assert_equal(normalize_media_format("video", "MKV"), "mkv", "video format")
    assert_equal(normalize_media_format("audio", "MP3"), "mp3", "audio format")
    assert_equal(normalize_media_format("cover", "JPG"), "jpg", "cover format")
    assert_equal(media_options("audio", "M4A")["format"], "bestaudio/best", "audio selector")
    assert_equal(media_options("cover", "JPG")["skip_download"], True, "cover skips media")
    try:
        normalize_media_format("audio", "MP4")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid media format must be rejected")


def test_sidecar_config_api():
    client = TestClient(app)
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "sidecar-config.json"
        output_dir = Path(temp_dir) / "downloads"
        with patch("backend.app.config_path", return_value=config_file):
            response = client.put(
                "/api/config",
                json={
                    "output_dir": str(output_dir),
                    "save_metadata": True,
                    "ai_model_id": None,
                },
            )
            assert_equal(response.status_code, 200, "config update status")
            assert_equal(config_file.is_file(), True, "config persisted")
            assert_equal(output_dir.is_dir(), True, "configured output exists")
            loaded = client.get("/api/config")
            assert_equal(loaded.json()["save_metadata"], True, "config reload")


def test_media_postprocess_and_metadata():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "sample.mp4"
        source.write_bytes(b"source")
        job = _test_job(root, DownloadOptions(format="MP3", download_type="audio", save_metadata=True))
        result = {
            "success": True,
            "title": "sample",
            "info": {"id": "sample", "title": "sample"},
            "downloaded_files": [{"type": "video", "path": str(source), "size": source.stat().st_size}],
        }

        def fake_ffmpeg(command, **_kwargs):
            Path(command[-1]).write_bytes(b"audio")
            return type("Completed", (), {"returncode": 0, "stderr": ""})()

        with patch("backend.media_postprocess.subprocess.run", side_effect=fake_ffmpeg):
            transformed = transform_downloaded_media(result, job, "ffmpeg", lambda *_args: None)
        audio = transformed["downloaded_files"][0]
        assert_equal(audio["type"], "audio", "postprocess output type")
        assert_equal(Path(audio["path"]).suffix, ".mp3", "postprocess extension")
        assert_equal(source.exists(), False, "source removed after conversion")

        with_metadata = append_metadata_file(transformed, job)
        metadata = next(item for item in with_metadata["downloaded_files"] if item["type"] == "metadata")
        payload = json.loads(Path(metadata["path"]).read_text(encoding="utf-8"))
        assert_equal(payload["platform"], "youtube", "metadata platform")
        assert_equal(payload["options"]["download_type"], "audio", "metadata options")


def test_ai_model_manifest_execution():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        model_dir = root / "models" / "fixture"
        output_dir = root / "output"
        model_dir.mkdir(parents=True)
        output_dir.mkdir()
        runner_script = model_dir / "runner.py"
        runner_script.write_text(
            "import json, pathlib, sys\n"
            "output = pathlib.Path(sys.argv[2]) / 'ai-result.txt'\n"
            "output.write_text(pathlib.Path(sys.argv[1]).name, encoding='utf-8')\n"
            "print(json.dumps({'downloaded_files': [{'type': 'ai-output', 'path': output.name}]}))\n",
            encoding="utf-8",
        )
        manifest = {
            "id": "fixture-model",
            "name": "Fixture model",
            "provider": "test",
            "command": [sys.executable, str(runner_script), "{input}", "{output_dir}"],
            "timeout_seconds": 30,
        }
        (model_dir / "douyingo-model.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / "models" / "unconfigured.gguf").write_bytes(b"weights")
        media = output_dir / "media.mp4"
        media.write_bytes(b"media")
        options = DownloadOptions(format="MP4", download_type="video", ai_model_id="fixture-model")
        job = _test_job(output_dir, options)
        result = {"success": True, "downloaded_files": [{"type": "video", "path": str(media)}]}

        with patch.dict(os.environ, {"DOUYINGO_MODELS_DIR": str(root / "models")}):
            models = discover_ai_models()
            fixture = next(model for model in models if model.id == "fixture-model")
            raw = next(model for model in models if model.name == "unconfigured")
            assert_equal(fixture.status, "available", "manifest model status")
            assert_equal(raw.status, "disabled", "raw model status")
            processed = run_ai_postprocess("fixture-model", job, result, lambda *_args: None)
        ai_output = next(item for item in processed["downloaded_files"] if item["type"] == "ai-output")
        assert_equal(Path(ai_output["path"]).read_text(encoding="utf-8"), "media.mp4", "AI output")


def test_job_history_persistence_and_recovery():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        database = root / "jobs.sqlite3"
        active = _test_job(root, DownloadOptions())

        store = JobStore(database)
        store.save(active)
        store.close()

        service = DownloadService(root, max_workers=1, job_store=JobStore(database))
        recovered = service.get_job(active.id)
        assert_equal(recovered is not None, True, "recovered job exists")
        assert_equal(recovered.status, JobStatus.CANCELLED, "interrupted job status")
        assert_equal(
            recovered.message,
            "Sidecar restarted before this task completed",
            "interrupted job message",
        )
        service.shutdown(wait=True)

        reloaded_store = JobStore(database)
        reloaded = reloaded_store.load_jobs()
        assert_equal(len(reloaded), 1, "persisted history count")
        assert_equal(reloaded[0].status, JobStatus.CANCELLED, "persisted recovered status")
        reloaded_store.close()


def test_job_history_deletion_contract():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        service = DownloadService(
            root,
            max_workers=1,
            job_store=JobStore(root / "jobs.sqlite3"),
        )
        request = DownloadRequest(
            text="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            platform=Platform.YOUTUBE,
            options=DownloadOptions(output_dir=str(root / "downloads")),
        )

        with patch.object(service._executor, "submit", return_value=None):
            first = service.create_download(request)
            second = service.create_download(request)

        try:
            service.delete_job(first.id)
        except ValueError:
            pass
        else:
            raise AssertionError("active jobs must not be deleted")

        cancelled = service.cancel_job(first.id)
        assert_equal(cancelled.status, JobStatus.CANCELLED, "cancel before delete")
        unchanged = service._update_job(
            first.id,
            status=JobStatus.DOWNLOADING,
            message="late worker update",
        )
        assert_equal(unchanged.status, JobStatus.CANCELLED, "cancelled job cannot be revived")
        assert_equal(service.delete_job(first.id), True, "delete terminal job")

        service.cancel_job(second.id)
        assert_equal(service.clear_terminal_jobs(), 1, "clear terminal history")
        assert_equal(service.list_jobs(), [], "history cleared")
        service.shutdown(wait=True)


def _test_job(output_dir: Path, options: DownloadOptions) -> DownloadJob:
    now = datetime.now(timezone.utc)
    return DownloadJob(
        id="0123456789abcdef",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        platform=Platform.YOUTUBE,
        title="sample",
        status=JobStatus.DOWNLOADING,
        progress=90,
        output_dir=str(output_dir),
        options=options,
        created_at=now,
        updated_at=now,
    )


def main():
    test_url_resolution()
    test_api_health_and_inventory()
    test_invalid_download_request()
    test_sidecar_lifecycle_arguments()
    test_youtube_packaged_runtime_options()
    test_runtime_path_overrides()
    test_packaged_download_root_fallback()
    test_media_option_contract()
    test_sidecar_config_api()
    test_media_postprocess_and_metadata()
    test_ai_model_manifest_execution()
    test_job_history_persistence_and_recovery()
    test_job_history_deletion_contract()
    print("Sidecar API smoke tests passed.")


if __name__ == "__main__":
    main()
