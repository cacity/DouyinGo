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


def build_sidecar() -> Path:
    extension = ".exe" if platform.system() == "Windows" else ""
    ffmpeg_path = PROJECT_ROOT / "ffmpeg.exe"
    add_binary: list[str] = []
    if ffmpeg_path.exists():
        separator = ";" if platform.system() == "Windows" else ":"
        add_binary = ["--add-binary", f"{ffmpeg_path}{separator}."]

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
            *excludes,
            *add_binary,
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
