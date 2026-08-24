from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from backend.runtime_paths import models_dir
from backend.schemas import AIModelInfo, DownloadJob


MODEL_EXTENSIONS = {".gguf", ".onnx", ".safetensors", ".pt", ".pth", ".bin"}
MANIFEST_NAME = "douyingo-model.json"


@dataclass(frozen=True)
class ModelRunner:
    info: AIModelInfo
    manifest_path: Path
    command: list[str]
    timeout_seconds: int


def model_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    env_dir = os.getenv("DOUYINGO_MODELS_DIR")
    for path in ([Path(env_dir).expanduser()] if env_dir else []) + [models_dir()]:
        if path not in dirs:
            dirs.append(path)
    return dirs


def discover_ai_models() -> list[AIModelInfo]:
    models: list[AIModelInfo] = []
    manifest_artifacts: set[Path] = set()

    for model_dir in model_search_dirs():
        if not model_dir.exists():
            continue
        for manifest_path in sorted(model_dir.rglob(MANIFEST_NAME)):
            runner = _load_manifest(manifest_path)
            models.append(runner.info)
            manifest_artifacts.update(
                path.resolve()
                for path in manifest_path.parent.iterdir()
                if path.is_file() and path.suffix.lower() in MODEL_EXTENSIONS
            )

        for path in sorted(model_dir.rglob("*")):
            if (
                not path.is_file()
                or path.suffix.lower() not in MODEL_EXTENSIONS
                or path.resolve() in manifest_artifacts
            ):
                continue
            models.append(
                AIModelInfo(
                    id=_path_id(path),
                    name=path.stem,
                    provider="unconfigured",
                    path=str(path),
                    status="disabled",
                    capabilities=["artifact"],
                )
            )

    return models


def configured_model_status() -> list[AIModelInfo]:
    discovered = discover_ai_models()
    if discovered:
        return discovered
    return [
        AIModelInfo(
            id="local-models",
            name="Local AI models",
            provider="local",
            path=str(model_search_dirs()[0]),
            status="missing",
            capabilities=["postprocess"],
        )
    ]


def get_model_runner(model_id: str) -> ModelRunner:
    for model_dir in model_search_dirs():
        if not model_dir.exists():
            continue
        for manifest_path in model_dir.rglob(MANIFEST_NAME):
            runner = _load_manifest(manifest_path)
            if runner.info.id == model_id:
                if runner.info.status != "available":
                    raise ValueError(f"AI model runner is unavailable: {runner.info.name}")
                return runner
    raise ValueError(f"Unknown AI model: {model_id}")


def run_ai_postprocess(
    model_id: str,
    job: DownloadJob,
    result: dict[str, Any],
    progress_callback: Callable[[int, str], None],
) -> dict[str, Any]:
    runner = get_model_runner(model_id)
    output_dir = Path(job.output_dir).resolve()
    media_files = [
        Path(item["path"]).resolve()
        for item in result.get("downloaded_files", [])
        if item.get("type") in {"video", "audio", "image"}
        and item.get("path")
        and Path(item["path"]).is_file()
    ]
    if not media_files:
        raise RuntimeError("AI post-processing requires a downloaded media file")

    metadata_files = [
        Path(item["path"]).resolve()
        for item in result.get("downloaded_files", [])
        if item.get("type") == "metadata" and item.get("path")
    ]
    replacements = {
        "input": str(media_files[0]),
        "output_dir": str(output_dir),
        "metadata": str(metadata_files[0]) if metadata_files else "",
        "model_dir": str(runner.manifest_path.parent.resolve()),
    }
    command = [part.format_map(replacements) for part in runner.command]
    before = {path.resolve() for path in output_dir.rglob("*") if path.is_file()}
    payload = {
        "schema_version": 1,
        "job": job.model_dump(mode="json"),
        "downloaded_files": result.get("downloaded_files", []),
    }

    progress_callback(97, f"Running AI model: {runner.info.name}")
    completed = subprocess.run(
        command,
        cwd=runner.manifest_path.parent,
        input=json.dumps(payload, ensure_ascii=False),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=runner.timeout_seconds,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        detail = "\n".join((completed.stderr or "").splitlines()[-8:])
        raise RuntimeError(f"AI model runner failed: {detail or completed.returncode}")

    reported = _reported_outputs(completed.stdout, output_dir)
    if not reported:
        after = {path.resolve() for path in output_dir.rglob("*") if path.is_file()}
        reported = [
            {
                "type": "ai-output",
                "path": str(path),
                "size": path.stat().st_size,
                "ext": path.suffix.lstrip(".").lower() or None,
            }
            for path in sorted(after - before)
        ]
    result.setdefault("downloaded_files", []).extend(reported)
    return result


def _load_manifest(path: Path) -> ModelRunner:
    manifest_id = _path_id(path)
    name = path.parent.name
    provider = "command"
    capabilities = ["postprocess"]
    status = "disabled"
    command: list[str] = []
    timeout_seconds = 3600
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        manifest_id = str(data.get("id") or manifest_id)
        name = str(data.get("name") or name)
        provider = str(data.get("provider") or provider)
        capabilities = [str(item) for item in data.get("capabilities", capabilities)]
        raw_command = data.get("command")
        if not isinstance(raw_command, list) or not raw_command or not all(
            isinstance(item, str) and item for item in raw_command
        ):
            raise ValueError("command must be a non-empty string array")
        command = list(raw_command)
        command[0] = _resolve_executable(command[0], path.parent)
        timeout_seconds = max(1, min(int(data.get("timeout_seconds", 3600)), 86400))
        status = "available"
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

    return ModelRunner(
        info=AIModelInfo(
            id=manifest_id,
            name=name,
            provider=provider,
            path=str(path),
            status=status,
            capabilities=capabilities,
        ),
        manifest_path=path,
        command=command,
        timeout_seconds=timeout_seconds,
    )


def _resolve_executable(value: str, model_dir: Path) -> str:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        local = model_dir / candidate
        if local.is_file():
            return str(local.resolve())
        resolved = shutil.which(value)
        if resolved:
            return resolved
    elif candidate.is_file():
        return str(candidate.resolve())
    raise ValueError(f"AI model executable was not found: {value}")


def _reported_outputs(stdout: str, output_dir: Path) -> list[dict[str, Any]]:
    if not stdout.strip():
        return []
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return []
    raw_files = payload.get("downloaded_files", []) if isinstance(payload, dict) else []
    files: list[dict[str, Any]] = []
    for item in raw_files:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        path = Path(item["path"])
        if not path.is_absolute():
            path = output_dir / path
        path = path.resolve()
        try:
            path.relative_to(output_dir)
        except ValueError as exc:
            raise RuntimeError(f"AI output is outside the task directory: {path}") from exc
        if not path.is_file():
            raise RuntimeError(f"AI runner reported a missing output: {path}")
        files.append(
            {
                "type": str(item.get("type") or "ai-output"),
                "path": str(path),
                "size": path.stat().st_size,
                "format": item.get("format"),
                "ext": item.get("ext") or path.suffix.lstrip(".").lower() or None,
            }
        )
    return files


def _path_id(path: Path) -> str:
    return hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
