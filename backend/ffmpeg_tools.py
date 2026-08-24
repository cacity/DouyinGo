from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from backend.schemas import ToolInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def find_ffmpeg() -> str | None:
    configured = os.getenv("DOUYINGO_FFMPEG_PATH")
    if configured and Path(configured).exists():
        return configured

    pyinstaller_dir = getattr(sys, "_MEIPASS", None)
    if pyinstaller_dir:
        bundled_ffmpeg = Path(pyinstaller_dir) / "ffmpeg.exe"
        if bundled_ffmpeg.exists():
            return str(bundled_ffmpeg)

    executable_dir = Path(sys.executable).resolve().parent
    adjacent_ffmpeg = executable_dir / "ffmpeg.exe"
    if adjacent_ffmpeg.exists():
        return str(adjacent_ffmpeg)

    local_windows_ffmpeg = PROJECT_ROOT / "ffmpeg.exe"
    if platform.system() == "Windows" and local_windows_ffmpeg.exists():
        return str(local_windows_ffmpeg)
    return shutil.which("ffmpeg")


def find_ffprobe() -> str | None:
    configured = os.getenv("DOUYINGO_FFPROBE_PATH")
    if configured and Path(configured).exists():
        return configured

    pyinstaller_dir = getattr(sys, "_MEIPASS", None)
    if pyinstaller_dir:
        bundled_ffprobe = Path(pyinstaller_dir) / "ffprobe.exe"
        if bundled_ffprobe.exists():
            return str(bundled_ffprobe)

    executable_dir = Path(sys.executable).resolve().parent
    adjacent_ffprobe = executable_dir / "ffprobe.exe"
    if adjacent_ffprobe.exists():
        return str(adjacent_ffprobe)

    local_windows_ffprobe = PROJECT_ROOT / "ffprobe.exe"
    if platform.system() == "Windows" and local_windows_ffprobe.exists():
        return str(local_windows_ffprobe)
    return shutil.which("ffprobe")


def _first_line(command: list[str], timeout: int = 5) -> str | None:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    output = (result.stdout or "").splitlines()
    return output[0].strip() if output else None


def _package_version(package_name: str) -> str | None:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        if package_name == "yt-dlp":
            try:
                import yt_dlp.version

                return yt_dlp.version.__version__
            except Exception:
                return None
        return None


def collect_tool_status() -> list[ToolInfo]:
    ffmpeg_path = find_ffmpeg()
    ffprobe_path = find_ffprobe()
    yt_dlp_version = _package_version("yt-dlp")

    return [
        ToolInfo(
            name="python",
            available=True,
            path=sys.executable,
            version=platform.python_version(),
        ),
        ToolInfo(
            name="ffmpeg",
            available=ffmpeg_path is not None,
            path=ffmpeg_path,
            version=_first_line([ffmpeg_path, "-version"]) if ffmpeg_path else None,
            details={"bundled": bool(ffmpeg_path and Path(ffmpeg_path).parent == PROJECT_ROOT)},
        ),
        ToolInfo(
            name="ffprobe",
            available=ffprobe_path is not None,
            path=ffprobe_path,
            version=_first_line([ffprobe_path, "-version"]) if ffprobe_path else None,
        ),
        ToolInfo(
            name="yt-dlp",
            available=yt_dlp_version is not None,
            path=None,
            version=yt_dlp_version,
        ),
        ToolInfo(
            name="models-dir",
            available=(PROJECT_ROOT / "models").exists()
            or bool(os.getenv("DOUYINGO_MODELS_DIR")),
            path=os.getenv("DOUYINGO_MODELS_DIR")
            or str(PROJECT_ROOT / "models"),
        ),
    ]
