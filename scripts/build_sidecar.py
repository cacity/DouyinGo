#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BINARIES_DIR = PROJECT_ROOT / "src-tauri" / "binaries"
MIN_YT_DLP_VERSION = (2026, 8, 19)
EXCLUDED_MODULES = [
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "tkinter",
    "_tkinter",
    "IPython",
    "ipykernel",
    "jupyter",
    "jupyter_client",
    "jupyter_core",
    "matplotlib",
    "notebook",
    "nbformat",
    "numpy",
    "PIL",
    "pytest",
    "sphinx",
    "docutils",
    "black",
    "yapf",
]


def run(command: list[str], cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    print(" ".join(command))
    return subprocess.run(command, cwd=cwd, text=True, check=True)


def host_triple() -> str:
    try:
        result = subprocess.run(
            ["rustc", "-vV"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SystemExit("rustc is required to calculate the Tauri sidecar target triple") from exc

    for line in result.stdout.splitlines():
        if line.startswith("host: "):
            return line.split("host: ", 1)[1].strip()
    raise SystemExit("Could not find host triple in rustc -vV output")


def deno_binary() -> Path:
    try:
        import deno
        import yt_dlp.version
        import yt_dlp_ejs.yt.solver  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            'YouTube packaging dependencies are missing. Run: '
            'python -m pip install "yt-dlp[default,deno]==2026.8.19"'
        ) from exc

    installed_version = tuple(
        int(part) for part in yt_dlp.version.__version__.split(".")[:3]
    )
    if installed_version < MIN_YT_DLP_VERSION:
        raise SystemExit(
            f"yt-dlp {yt_dlp.version.__version__} is too old for the packaged sidecar. "
            'Run: python -m pip install --upgrade "yt-dlp[default,deno]==2026.8.19"'
        )

    path = Path(deno.find_deno_bin())
    if not path.exists():
        raise SystemExit(f"The deno package did not provide an executable at {path}")
    return path


def build_sidecar() -> Path:
    extension = ".exe" if platform.system() == "Windows" else ""
    separator = ";" if platform.system() == "Windows" else ":"
    binary_paths = [deno_binary()]
    for executable in ("ffmpeg", "ffprobe"):
        local_path = PROJECT_ROOT / f"{executable}{extension}"
        if local_path.exists():
            binary_paths.append(local_path)

    add_binaries: list[str] = []
    for binary_path in binary_paths:
        add_binaries.extend(["--add-binary", f"{binary_path}{separator}."])

    excludes: list[str] = []
    for module in EXCLUDED_MODULES:
        excludes.extend(["--exclude-module", module])

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            "douyingo-sidecar",
            "--paths",
            str(PROJECT_ROOT),
            "--hidden-import",
            "uvicorn.logging",
            "--hidden-import",
            "uvicorn.loops.auto",
            "--hidden-import",
            "uvicorn.protocols.http.auto",
            "--hidden-import",
            "uvicorn.protocols.websockets.auto",
            "--hidden-import",
            "uvicorn.lifespan.on",
            "--hidden-import",
            "yt_dlp_ejs.yt.solver",
            *excludes,
            *add_binaries,
            str(PROJECT_ROOT / "backend" / "sidecar.py"),
        ]
    )

    built = PROJECT_ROOT / "dist" / f"douyingo-sidecar{extension}"
    if not built.exists():
        raise SystemExit(f"PyInstaller did not produce {built}")
    return built


def install_for_tauri(built: Path) -> Path:
    BINARIES_DIR.mkdir(parents=True, exist_ok=True)
    extension = ".exe" if platform.system() == "Windows" else ""
    target = BINARIES_DIR / f"douyingo-sidecar-{host_triple()}{extension}"
    shutil.copy2(built, target)
    return target


def main() -> int:
    built = build_sidecar()
    target = install_for_tauri(built)
    print(f"Sidecar installed for Tauri: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
