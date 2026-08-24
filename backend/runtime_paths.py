from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


APP_NAME = "DouyinGo"
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None))


def data_root() -> Path:
    configured = os.getenv("DOUYINGO_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    if not is_frozen():
        return SOURCE_ROOT

    if sys.platform == "win32":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / APP_NAME


def download_root() -> Path:
    configured = os.getenv("DOUYINGO_DOWNLOADS_DIR")
    if configured:
        return Path(configured).expanduser()
    if not is_frozen():
        return SOURCE_ROOT

    candidates = (
        Path.home() / "Downloads" / APP_NAME,
        data_root() / "downloads",
        Path(tempfile.gettempdir()) / APP_NAME / "downloads",
    )
    last_error: OSError | None = None
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError as exc:
            last_error = exc
    raise last_error or OSError("No writable download directory is available")


def config_path() -> Path:
    return data_root() / "sidecar-config.json"


def jobs_db_path() -> Path:
    return data_root() / "jobs.sqlite3"


def models_dir() -> Path:
    return data_root() / "models"
