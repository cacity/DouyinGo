from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.ai_models import configured_model_status, get_model_runner
from backend.download_service import DownloadService
from backend.ffmpeg_tools import collect_tool_status
from backend.runtime_paths import config_path, download_root
from backend.schemas import (
    DownloadJob,
    DownloadRequest,
    HealthResponse,
    ResolveRequest,
    SidecarConfig,
    ToolInfo,
)


download_service = DownloadService(download_root())

app = FastAPI(title="DouyinGo Sidecar", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        service="douyingo-sidecar",
        version=__version__,
        time=datetime.now(timezone.utc),
    )


@app.get("/api/config", response_model=SidecarConfig)
def get_config() -> SidecarConfig:
    path = config_path()
    if not path.exists():
        return SidecarConfig()
    try:
        return SidecarConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return SidecarConfig()


@app.put("/api/config", response_model=SidecarConfig)
def update_config(config: SidecarConfig) -> SidecarConfig:
    if config.ai_model_id:
        try:
            get_model_runner(config.ai_model_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if config.output_dir:
        try:
            output_dir = download_service.project_root / config.output_dir
            if not output_dir.is_absolute():
                output_dir = output_dir.resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    path = config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return config


@app.get("/api/tools", response_model=list[ToolInfo])
def get_tools() -> list[ToolInfo]:
    return collect_tool_status()


@app.get("/api/models")
def get_models():
    return configured_model_status()


@app.post("/api/resolve")
def resolve_media(request: ResolveRequest) -> dict:
    try:
        return download_service.resolve_info(request.text, request.platform)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/downloads", response_model=DownloadJob)
def create_download(request: DownloadRequest) -> DownloadJob:
    try:
        return download_service.create_download(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/downloads", response_model=list[DownloadJob])
def list_downloads() -> list[DownloadJob]:
    return download_service.list_jobs()


@app.get("/api/downloads/{job_id}", response_model=DownloadJob)
def get_download(job_id: str) -> DownloadJob:
    job = download_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")
    return job


@app.post("/api/downloads/{job_id}/cancel", response_model=DownloadJob)
def cancel_download(job_id: str) -> DownloadJob:
    job = download_service.cancel_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")
    return job
