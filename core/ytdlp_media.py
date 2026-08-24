from __future__ import annotations

from pathlib import Path
from typing import Any


VIDEO_FORMATS = {"mp4", "mkv", "mov"}
AUDIO_FORMATS = {"mp3", "m4a", "wav"}
COVER_FORMATS = {"jpg"}


def normalize_media_format(download_type: str, output_format: str) -> str:
    normalized = output_format.strip().lower()
    allowed = {
        "video": VIDEO_FORMATS,
        "audio": AUDIO_FORMATS,
        "cover": COVER_FORMATS,
    }.get(download_type)
    if allowed is None:
        raise ValueError(f"Unsupported download type: {download_type}")
    if normalized not in allowed:
        supported = ", ".join(sorted(item.upper() for item in allowed))
        raise ValueError(f"{download_type} downloads support these formats: {supported}")
    return normalized


def media_options(download_type: str, output_format: str) -> dict[str, Any]:
    output_format = normalize_media_format(download_type, output_format)
    if download_type == "audio":
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": output_format,
                    "preferredquality": "0",
                }
            ],
        }
    if download_type == "cover":
        return {
            "skip_download": True,
            "writethumbnail": True,
            "postprocessors": [
                {
                    "key": "FFmpegThumbnailsConvertor",
                    "format": output_format,
                    "when": "before_dl",
                }
            ],
        }

    options: dict[str, Any] = {"merge_output_format": output_format}
    if output_format != "mp4":
        options["postprocessors"] = [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": output_format,
            }
        ]
    return options


def output_template(target_dir: str) -> str:
    return str(Path(target_dir) / "%(title)s [%(id)s].%(ext)s")


def collect_media_files(
    target_dir: str,
    info: dict[str, Any],
    download_type: str,
    output_format: str,
) -> list[dict[str, Any]]:
    output_format = normalize_media_format(download_type, output_format)
    media_id = str(info.get("id") or "")
    expected_suffix = f".{output_format}"
    paths = [
        path
        for path in Path(target_dir).iterdir()
        if path.is_file()
        and path.suffix.lower() == expected_suffix
        and (not media_id or f"[{media_id}]" in path.name)
    ]

    file_type = "image" if download_type == "cover" else download_type
    width = info.get("width") or 0
    height = info.get("height") or 0
    resolution = f"{width}x{height}" if width and height else None
    return [
        {
            "type": file_type,
            "path": str(path),
            "size": path.stat().st_size,
            "format": output_format.upper(),
            "ext": output_format,
            "resolution": resolution if download_type == "video" else None,
            "thumbnail": info.get("thumbnail") if download_type != "cover" else None,
            "url": info.get("thumbnail") if download_type == "cover" else None,
        }
        for path in sorted(paths)
    ]
