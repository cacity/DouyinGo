from __future__ import annotations

import json
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.ai_models import configured_model_status
from backend.download_service import DownloadService
from backend.ffmpeg_tools import collect_tool_status
from backend.runtime_paths import config_path, download_root
from backend.schemas import DownloadJob, DownloadRequest, HealthResponse, ResolveRequest, ToolInfo


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
        time=datetime.utcnow(),
    )


@app.get("/api/config")
def get_config() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
