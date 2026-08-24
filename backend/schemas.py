from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


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


BrowserCookieSource = Literal["chrome", "edge", "firefox", "brave", "chromium"]


class YtDlpNetworkOptions(BaseModel):
    proxy_url: str | None = None
    cookies_from_browser: BrowserCookieSource | None = None

    @field_validator("proxy_url")
    @classmethod
    def validate_proxy_url(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        if not value:
            return None
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {
            "http",
            "https",
            "socks4",
            "socks4a",
            "socks5",
            "socks5h",
        } or not parsed.hostname:
            raise ValueError("Proxy must be a valid HTTP, HTTPS, SOCKS4, or SOCKS5 URL")
        return value


class SidecarConfig(BaseModel):
    output_dir: str | None = None
    save_metadata: bool = False
    ai_model_id: str | None = None
    youtube_proxy_url: str | None = None
    youtube_cookies_from_browser: BrowserCookieSource | None = None
    twitter_proxy_url: str | None = None
    twitter_cookies_from_browser: BrowserCookieSource | None = None

    @field_validator("youtube_proxy_url", "twitter_proxy_url")
    @classmethod
    def validate_proxy_url(cls, value: str | None) -> str | None:
        return YtDlpNetworkOptions.validate_proxy_url(value)


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
