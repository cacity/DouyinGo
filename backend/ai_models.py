from __future__ import annotations

import hashlib
import os
from pathlib import Path

from backend.schemas import AIModelInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_EXTENSIONS = {".gguf", ".onnx", ".safetensors", ".pt", ".pth", ".bin"}


def model_search_dirs() -> list[Path]:
    dirs = [PROJECT_ROOT / "models"]
    env_dir = os.getenv("DOUYINGO_MODELS_DIR")
    if env_dir:
        dirs.insert(0, Path(env_dir))
    return dirs


def discover_ai_models() -> list[AIModelInfo]:
    models: list[AIModelInfo] = []

    for model_dir in model_search_dirs():
        if not model_dir.exists():
            continue
        for path in sorted(model_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in MODEL_EXTENSIONS:
                continue
            model_id = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
            models.append(
                AIModelInfo(
                    id=model_id,
                    name=path.stem,
                    provider="local",
                    path=str(path),
                    status="available",
                    capabilities=["metadata", "postprocess"],
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
            capabilities=["metadata", "postprocess"],
        )
    ]
