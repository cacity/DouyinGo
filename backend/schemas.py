from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Platform(str, Enum):
    DOUYIN = "douyin"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    KOUSHARE = "koushare"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RESOLVING = "resolving"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class DownloadOptions(BaseModel):
    quality: str = "best"
    format: str = "MP4"
    download_type: Literal["video", "audio", "cover"] = "video"
    output_dir: str | None = None
    save_metadata: bool = False
    ai_model_id: str | None = None


class DownloadRequest(BaseModel):
    text: str = Field(..., description="URL or share text copied from a platform.")
    platform: Platform | None = None
    options: DownloadOptions = Field(default_factory=DownloadOptions)


class ResolveRequest(BaseModel):
    text: str
    platform: Platform | None = None


class ResolvedUrl(BaseModel):
    url: str
    platform: Platform
    supported: bool


class DownloadedFile(BaseModel):
    type: str
    path: str
    size: int | None = None
    format: str | None = None
    ext: str | None = None
    resolution: str | None = None
    thumbnail: str | None = None
    url: str | None = None


class DownloadJob(BaseModel):
    id: str
    url: str
    platform: Platform
    title: str
    status: JobStatus
    progress: int = 0
    message: str = ""
    output_dir: str
    error: str | None = None
    downloaded_files: list[DownloadedFile] = Field(default_factory=list)
    options: DownloadOptions = Field(default_factory=DownloadOptions)
    created_at: datetime
    updated_at: datetime


class ToolInfo(BaseModel):
    name: str
    available: bool
    path: str | None = None
    version: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AIModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    path: str | None = None
    status: Literal["available", "missing", "disabled"]
    capabilities: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    time: datetime
