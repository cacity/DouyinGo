from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from backend.runtime_paths import SOURCE_ROOT, models_dir
from backend.schemas import ToolInfo


PROJECT_ROOT = SOURCE_ROOT


def _bundled_executable(name: str) -> str | None:
    pyinstaller_dir = getattr(sys, "_MEIPASS", None)
    if pyinstaller_dir:
        candidate = Path(pyinstaller_dir) / name
        if candidate.exists():
            return str(candidate)

    executable_dir = Path(sys.executable).resolve().parent
    candidate = executable_dir / name
    if candidate.exists():
        return str(candidate)
    return None


def find_ffmpeg() -> str | None:
    configured = os.getenv("DOUYINGO_FFMPEG_PATH")
    if configured and Path(configured).exists():
        return configured

    bundled_ffmpeg = _bundled_executable("ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg")
    if bundled_ffmpeg:
        return bundled_ffmpeg

    local_windows_ffmpeg = PROJECT_ROOT / "ffmpeg.exe"
    if platform.system() == "Windows" and local_windows_ffmpeg.exists():
        return str(local_windows_ffmpeg)
    return shutil.which("ffmpeg")


def find_ffprobe() -> str | None:
    configured = os.getenv("DOUYINGO_FFPROBE_PATH")
    if configured and Path(configured).exists():
        return configured

    bundled_ffprobe = _bundled_executable("ffprobe.exe" if platform.system() == "Windows" else "ffprobe")
    if bundled_ffprobe:
        return bundled_ffprobe

    local_windows_ffprobe = PROJECT_ROOT / "ffprobe.exe"
    if platform.system() == "Windows" and local_windows_ffprobe.exists():
        return str(local_windows_ffprobe)
    return shutil.which("ffprobe")


def find_deno() -> str | None:
    configured = os.getenv("DOUYINGO_DENO_PATH")
    if configured and Path(configured).exists():
        return configured

    executable_name = "deno.exe" if platform.system() == "Windows" else "deno"
    bundled_deno = _bundled_executable(executable_name)
    if bundled_deno:
        return bundled_deno
    return shutil.which("deno")


def _is_bundled(path: str | None) -> bool:
    pyinstaller_dir = getattr(sys, "_MEIPASS", None)
    return bool(path and pyinstaller_dir and Path(path).parent == Path(pyinstaller_dir))


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
        if package_name == "yt-dlp-ejs":
            try:
                import yt_dlp_ejs

                return yt_dlp_ejs.version
            except Exception:
                return None
        return None


def collect_tool_status() -> list[ToolInfo]:
    ffmpeg_path = find_ffmpeg()
    ffprobe_path = find_ffprobe()
    deno_path = find_deno()
    yt_dlp_version = _package_version("yt-dlp")
    yt_dlp_ejs_version = _package_version("yt-dlp-ejs")
    model_path = models_dir()

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
            details={"bundled": _is_bundled(ffmpeg_path)},
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
            name="yt-dlp-ejs",
            available=yt_dlp_ejs_version is not None,
            path=None,
            version=yt_dlp_ejs_version,
        ),
        ToolInfo(
            name="deno",
            available=deno_path is not None,
            path=deno_path,
            version=_first_line([deno_path, "--version"]) if deno_path else None,
            details={"bundled": _is_bundled(deno_path)},
        ),
        ToolInfo(
            name="models-dir",
            available=model_path.exists() or bool(os.getenv("DOUYINGO_MODELS_DIR")),
            path=os.getenv("DOUYINGO_MODELS_DIR")
            or str(model_path),
        ),
    ]
