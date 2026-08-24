from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from backend.schemas import DownloadJob
from core.ytdlp_media import normalize_media_format


def transform_downloaded_media(
    result: dict[str, Any],
    job: DownloadJob,
    ffmpeg_path: str | None,
    progress_callback: Callable[[int, str], None],
) -> dict[str, Any]:
    download_type = job.options.download_type
    output_format = normalize_media_format(download_type, job.options.format)
    if download_type == "video" and output_format == "mp4":
        return result

    source_files = [
        item
        for item in result.get("downloaded_files", [])
        if item.get("path") and Path(item["path"]).is_file()
    ]
    source_files.extend(
        {"type": "thumbnail", "path": item["thumbnail"]}
        for item in result.get("downloaded_files", [])
        if item.get("thumbnail") and Path(item["thumbnail"]).is_file()
    )
    video_files = [item for item in source_files if item.get("type") == "video"]
    image_files = [item for item in source_files if item.get("type") in {"image", "thumbnail"}]

    if download_type == "cover" and image_files:
        source = Path(image_files[0]["path"])
        output = source.with_name(f"{source.stem}_cover.jpg")
        if source.resolve() != output.resolve():
            shutil.copy2(source, output)
        _remove_sources(source_files, keep={output.resolve()})
        result["downloaded_files"] = [_file_record(output, "image", "jpg")]
        return result

    if not video_files:
        raise RuntimeError(f"No video output is available for {download_type} post-processing")
    if not ffmpeg_path:
        raise RuntimeError("FFmpeg is required for the selected output type or format")

    converted: list[dict[str, Any]] = []
    for index, item in enumerate(video_files, start=1):
        source = Path(item["path"])
        progress_callback(92, f"Post-processing file {index}/{len(video_files)}")
        if download_type == "video":
            output = source.with_suffix(f".{output_format}")
            command = [ffmpeg_path, "-y", "-i", str(source), "-map", "0", "-c", "copy", str(output)]
            file_type = "video"
        elif download_type == "audio":
            output = source.with_suffix(f".{output_format}")
            codec_args = {
                "mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
                "m4a": ["-c:a", "aac", "-b:a", "192k"],
                "wav": ["-c:a", "pcm_s16le"],
            }[output_format]
            command = [ffmpeg_path, "-y", "-i", str(source), "-vn", *codec_args, str(output)]
            file_type = "audio"
        else:
            output = source.with_name(f"{source.stem}_cover.jpg")
            command = [
                ffmpeg_path,
                "-y",
                "-ss",
                "00:00:01",
                "-i",
                str(source),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(output),
            ]
            file_type = "image"

        _run_ffmpeg(command)
        converted.append(_file_record(output, file_type, output_format))

    _remove_sources(source_files, keep={Path(item["path"]).resolve() for item in converted})
    result["downloaded_files"] = converted
    return result


def append_metadata_file(result: dict[str, Any], job: DownloadJob) -> dict[str, Any]:
    title = _safe_filename(result.get("title") or job.title)
    path = Path(job.output_dir) / f"{title} [{job.id[:8]}].metadata.json"
    media_info = result.get("video_info") or result.get("info") or {}
    try:
        from yt_dlp.utils import sanitize_info

        media_info = sanitize_info(media_info)
    except (ImportError, TypeError, ValueError):
        media_info = json.loads(json.dumps(media_info, ensure_ascii=False, default=str))

    payload = {
        "schema_version": 1,
        "source_url": job.url,
        "platform": job.platform.value,
        "title": result.get("title") or job.title,
        "options": job.options.model_dump(),
        "downloaded_files": result.get("downloaded_files", []),
        "media": media_info,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    result.setdefault("downloaded_files", []).append(_file_record(path, "metadata", "json"))
    return result


def _run_ffmpeg(command: list[str]) -> None:
    completed = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=3600,
        check=False,
    )
    if completed.returncode != 0:
        detail = "\n".join((completed.stderr or "").splitlines()[-8:])
        raise RuntimeError(f"FFmpeg post-processing failed: {detail or completed.returncode}")


def _remove_sources(files: list[dict[str, Any]], keep: set[Path]) -> None:
    for item in files:
        path = Path(item["path"])
        try:
            if path.resolve() not in keep:
                path.unlink(missing_ok=True)
        except OSError:
            pass


def _file_record(path: Path, file_type: str, output_format: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Post-processing did not produce {path}")
    return {
        "type": file_type,
        "path": str(path),
        "size": path.stat().st_size,
        "format": output_format.upper(),
        "ext": output_format,
    }


def _safe_filename(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", value).strip()[:100] or "media"
