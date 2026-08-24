from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.koushare_downloader import KoushareDownloader
from core.pure_python_extractor import PurePythonExtractor
from core.twitter_downloader import TwitterDownloader
from core.youtube_downloader import YouTubeDownloader

from backend.ai_models import get_model_runner, run_ai_postprocess
from backend.ffmpeg_tools import find_deno, find_ffmpeg
from backend.job_store import JobStore
from backend.media_postprocess import append_metadata_file, transform_downloaded_media
from backend.runtime_paths import jobs_db_path
from backend.schemas import (
    DownloadJob,
    DownloadOptions,
    DownloadRequest,
    DownloadedFile,
    JobStatus,
    Platform,
    SidecarConfig,
    YtDlpNetworkOptions,
)
from backend.url_utils import default_output_dir, extract_url
from core.ytdlp_media import normalize_media_format


QUALITY_ALIASES = {
    "最佳质量": "best",
    "原画": "best",
    "4K": "4k",
    "2K(1440p)": "1440p",
    "超清(1080p)": "1080p",
    "高清(720p)": "720p",
    "标清(480p)": "480p",
}

ACTIVE_STATUSES = {JobStatus.QUEUED, JobStatus.RESOLVING, JobStatus.DOWNLOADING}
TERMINAL_STATUSES = {JobStatus.SUCCESS, JobStatus.ERROR, JobStatus.CANCELLED}


class DownloadService:
    def __init__(
        self,
        project_root: Path | None = None,
        max_workers: int = 3,
        job_store: JobStore | None = None,
    ):
        self.project_root = project_root or Path(__file__).resolve().parents[1]
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="download")
        self._job_store = job_store or JobStore(jobs_db_path())
        self._jobs = {job.id: job for job in self._job_store.load_jobs()}
        self._network_options: dict[str, YtDlpNetworkOptions] = {}
        self._cancel_requested: set[str] = set()
        self._lock = threading.RLock()
        self._recover_interrupted_jobs()

    def create_download(
        self,
        request: DownloadRequest,
        config: SidecarConfig | None = None,
    ) -> DownloadJob:
        resolved = extract_url(request.text, request.platform)
        platform = request.platform or resolved.platform
        if platform == Platform.UNKNOWN or not resolved.supported:
            raise ValueError("Unsupported or unrecognized video URL")
        normalize_media_format(request.options.download_type, request.options.format)
        if request.options.ai_model_id:
            get_model_runner(request.options.ai_model_id)

        output_dir = request.options.output_dir or default_output_dir(platform)
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = self.project_root / output_path
        output_path.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        job = DownloadJob(
            id=uuid.uuid4().hex,
            url=resolved.url,
            platform=platform,
            title=_default_title(platform),
            status=JobStatus.QUEUED,
            progress=0,
            message="Queued",
            output_dir=str(output_path),
            options=request.options,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._jobs[job.id] = job
            self._network_options[job.id] = _network_options_for_platform(config, platform)
            self._job_store.save(job)

        self._executor.submit(self._run_download, job.id)
        return job

    def list_jobs(self) -> list[DownloadJob]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def get_job(self, job_id: str) -> DownloadJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> DownloadJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            if job.status in TERMINAL_STATUSES:
                return job
            self._cancel_requested.add(job_id)
            if job.status in {JobStatus.QUEUED, JobStatus.RESOLVING}:
                return self._update_job(
                    job_id,
                    status=JobStatus.CANCELLED,
                    message="Cancelled before download started",
                    error=None,
                )
            return self._update_job(job_id, message="Cancellation requested")

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            if job.status in ACTIVE_STATUSES:
                raise ValueError("Active download jobs must be cancelled before deletion")
            self._job_store.delete(job_id)
            del self._jobs[job_id]
            self._cancel_requested.discard(job_id)
            self._network_options.pop(job_id, None)
            return True

    def clear_terminal_jobs(self) -> int:
        with self._lock:
            terminal_ids = [
                job_id for job_id, job in self._jobs.items() if job.status in TERMINAL_STATUSES
            ]
            deleted = self._job_store.delete_terminal()
            for job_id in terminal_ids:
                self._jobs.pop(job_id, None)
                self._cancel_requested.discard(job_id)
                self._network_options.pop(job_id, None)
            return deleted

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if job.status in ACTIVE_STATUSES:
                    self._cancel_requested.add(job_id)
                    self._update_job(
                        job_id,
                        status=JobStatus.CANCELLED,
                        message="Sidecar stopped before this task completed",
                        error=None,
                    )
        self._executor.shutdown(wait=wait, cancel_futures=True)
        if wait:
            self._job_store.close()

    def resolve_info(
        self,
        text: str,
        platform: Platform | None = None,
        config: SidecarConfig | None = None,
    ) -> dict[str, Any]:
        resolved = extract_url(text, platform)
        if not resolved.supported:
            return {"resolved": resolved.model_dump(), "info": None}

        downloader = self._create_downloader(
            resolved.platform,
            default_output_dir(resolved.platform),
            _network_options_for_platform(config, resolved.platform),
        )
        info = downloader.get_video_info(resolved.url)
        if hasattr(info, "to_dict"):
            info = info.to_dict()
        return {"resolved": resolved.model_dump(), "info": info}

    def _run_download(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        try:
            if self._is_cancelled(job_id):
                self._update_job(job_id, status=JobStatus.CANCELLED, message="Cancelled")
                return

            self._update_job(job_id, status=JobStatus.RESOLVING, progress=3, message="Resolving media")
            downloader = self._create_downloader(
                job.platform,
                job.output_dir,
                self._network_options.get(job_id),
            )

            try:
                info = downloader.get_video_info(job.url)
                title = _title_from_info(info, job.platform)
                if title:
                    self._update_job(job_id, title=title)
            except Exception:
                # A failed preflight should not block downloaders that can resolve during download.
                pass

            if self._is_cancelled(job_id):
                self._update_job(job_id, status=JobStatus.CANCELLED, message="Cancelled")
                return

            job = self.get_job(job_id) or job

            self._update_job(job_id, status=JobStatus.DOWNLOADING, progress=8, message="Starting download")

            def progress_callback(progress: int, message: str):
                if self._is_cancelled(job_id):
                    raise RuntimeError("Download cancellation requested")
                self._update_job(
                    job_id,
                    status=JobStatus.DOWNLOADING,
                    progress=max(0, min(100, int(progress))),
                    message=message,
                )

            result = self._download_with_platform_downloader(downloader, job, progress_callback)
            if result.get("success"):
                if job.platform in {Platform.DOUYIN, Platform.KOUSHARE}:
                    result = transform_downloaded_media(
                        result,
                        job,
                        find_ffmpeg(),
                        progress_callback,
                    )
                if job.options.save_metadata:
                    result = append_metadata_file(result, job)
                if job.options.ai_model_id:
                    result = run_ai_postprocess(
                        job.options.ai_model_id,
                        job,
                        result,
                        progress_callback,
                    )
                files = [_normalize_downloaded_file(item) for item in result.get("downloaded_files", [])]
                title = result.get("title") or job.title
                self._update_job(
                    job_id,
                    title=title,
                    status=JobStatus.SUCCESS,
                    progress=100,
                    message="Download completed",
                    downloaded_files=files,
                    error=None,
                )
            else:
                self._update_job(
                    job_id,
                    status=JobStatus.ERROR,
                    message="Download failed",
                    error=result.get("error", "Unknown error"),
                )
        except Exception as exc:
            status = JobStatus.CANCELLED if self._is_cancelled(job_id) else JobStatus.ERROR
            self._update_job(job_id, status=status, message=str(exc), error=str(exc))
        finally:
            with self._lock:
                self._cancel_requested.discard(job_id)
                self._network_options.pop(job_id, None)

    def _create_downloader(
        self,
        platform: Platform,
        output_dir: str,
        network: YtDlpNetworkOptions | None = None,
    ):
        network = network or YtDlpNetworkOptions()
        if platform == Platform.DOUYIN:
            return PurePythonExtractor()
        if platform == Platform.YOUTUBE:
            return YouTubeDownloader(
                output_dir,
                ffmpeg_path=find_ffmpeg(),
                deno_path=find_deno(),
                proxy_url=network.proxy_url,
                cookies_from_browser=network.cookies_from_browser,
            )
        if platform == Platform.TWITTER:
            return TwitterDownloader(
                output_dir,
                ffmpeg_path=find_ffmpeg(),
                proxy_url=network.proxy_url,
                cookies_from_browser=network.cookies_from_browser,
            )
        if platform == Platform.KOUSHARE:
            return KoushareDownloader(output_dir)
        raise ValueError(f"Unsupported platform: {platform}")

    def _download_with_platform_downloader(
        self,
        downloader: Any,
        job: DownloadJob,
        progress_callback: Callable[[int, str], None],
    ) -> dict[str, Any]:
        quality = _normalize_quality(job.platform, job.options.quality)
        if job.platform == Platform.DOUYIN:
            return downloader.download_video(job.url, job.output_dir, progress_callback)
        if job.platform in {Platform.YOUTUBE, Platform.TWITTER}:
            return downloader.download_video(
                job.url,
                download_dir=job.output_dir,
                quality=quality,
                progress_callback=progress_callback,
                download_type=job.options.download_type,
                output_format=job.options.format,
            )
        return downloader.download_video(
            job.url,
            download_dir=job.output_dir,
            quality=quality,
            progress_callback=progress_callback,
        )

    def _update_job(self, job_id: str, **changes: Any) -> DownloadJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            next_status = changes.get("status")
            if (
                job.status == JobStatus.CANCELLED
                and next_status is not None
                and next_status != JobStatus.CANCELLED
            ):
                return job
            data = job.model_dump()
            data.update(changes)
            data["updated_at"] = datetime.now(timezone.utc)
            updated = DownloadJob.model_validate(data)
            self._jobs[job_id] = updated
            self._job_store.save(updated)
            return updated

    def _is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            return job_id in self._cancel_requested or (
                bool(job) and job.status == JobStatus.CANCELLED
            )

    def _recover_interrupted_jobs(self) -> None:
        for job_id, job in list(self._jobs.items()):
            if job.status not in ACTIVE_STATUSES:
                continue
            data = job.model_dump()
            data.update(
                status=JobStatus.CANCELLED,
                message="Sidecar restarted before this task completed",
                error=None,
                updated_at=datetime.now(timezone.utc),
            )
            recovered = DownloadJob.model_validate(data)
            self._jobs[job_id] = recovered
            self._job_store.save(recovered)


def _normalize_quality(platform: Platform, quality: str) -> str:
    if platform == Platform.KOUSHARE:
        return quality
    return QUALITY_ALIASES.get(quality, quality).lower()


def _network_options_for_platform(
    config: SidecarConfig | None,
    platform: Platform,
) -> YtDlpNetworkOptions:
    if not config:
        return YtDlpNetworkOptions()
    if platform == Platform.YOUTUBE:
        return YtDlpNetworkOptions(
            proxy_url=config.youtube_proxy_url,
            cookies_from_browser=config.youtube_cookies_from_browser,
        )
    if platform == Platform.TWITTER:
        return YtDlpNetworkOptions(
            proxy_url=config.twitter_proxy_url,
            cookies_from_browser=config.twitter_cookies_from_browser,
        )
    return YtDlpNetworkOptions()


def _default_title(platform: Platform) -> str:
    names = {
        Platform.DOUYIN: "Douyin video",
        Platform.YOUTUBE: "YouTube video",
        Platform.TWITTER: "Twitter/X video",
        Platform.KOUSHARE: "Koushare video",
    }
    return names.get(platform, "Video")


def _title_from_info(info: Any, platform: Platform) -> str | None:
    if not info:
        return None
    if hasattr(info, "to_dict"):
        info = info.to_dict()
    if platform == Platform.DOUYIN:
        return info.get("desc") or None
    return info.get("title") or info.get("desc") or None


def _normalize_downloaded_file(item: dict[str, Any]) -> DownloadedFile:
    size = item.get("size")
    if size is not None:
        try:
            size = int(size)
        except (TypeError, ValueError):
            size = None
    return DownloadedFile(
        type=str(item.get("type", "file")),
        path=str(item.get("path", "")),
        size=size,
        format=item.get("format"),
        ext=item.get("ext"),
        resolution=item.get("resolution"),
        thumbnail=item.get("thumbnail"),
        url=item.get("url"),
    )
