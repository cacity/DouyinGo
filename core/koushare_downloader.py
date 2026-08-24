#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
寇享视频下载模块
"""

import hashlib
import json
import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from loguru import logger


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class KoushareDownloader:
    API_BASE = "https://api-core.koushare.com"
    SALT_KEY = "arfw2r4k4rdwrlmchvcu7q61fs"

    def __init__(
        self,
        download_dir: str = "koushare_downloads",
        api_base: Optional[str] = None,
    ):
        self.download_dir = download_dir
        self.api_base = (
            api_base or os.getenv("DOUYINGO_KOUSHARE_API_BASE") or self.API_BASE
        ).rstrip("/")
        self._access_token = ""
        self._session: Optional[requests.Session] = None
        os.makedirs(download_dir, exist_ok=True)

    def is_koushare_url(self, url: str) -> bool:
        return "koushare.com" in url

    def extract_koushare_url_from_text(self, text: str) -> Optional[str]:
        patterns = [
            r'https?://(?:www\.)?koushare\.com/live/details/\d+\?(?:[^\s]*&)?(?:vid|videoId)=\d+[^\s]*',
            r'https?://(?:www\.)?koushare\.com/video/details/\d+[^\s]*',
            r'https?://(?:www\.)?koushare\.com/video/videodetail/\d+[^\s]*',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        text = text.strip()
        if text.startswith('http') and 'koushare.com' in text:
            return text.split()[0]

        return None

    def set_token(self, access_token: str):
        self._access_token = access_token or ""
        session = self._get_session()
        if self._access_token:
            session.headers["Authorization"] = self._access_token
        else:
            session.headers.pop("Authorization", None)

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        if not self.is_koushare_url(url):
            logger.error(f"不是有效的寇享链接: {url}")
            return None

        try:
            live_id, video_id = self._parse_koushare_url(url)
            title = f"koushare_{video_id}"
            playback_data = None

            if live_id:
                video_item = self._get_live_video_info(live_id, video_id)
                raw_title = (video_item or {}).get("title") or (video_item or {}).get("name")
                if raw_title:
                    title = self._sanitize_filename(raw_title)
                else:
                    live_info = self._get_live_info(live_id)
                    raw_title = (live_info or {}).get("title") or (live_info or {}).get("name")
                    if raw_title:
                        title = self._sanitize_filename(raw_title)

                playback_data = self._get_live_playback(live_id, video_id)
            else:
                secret = self._check_video_auth(video_id)
                raw_title = self._get_video_title(video_id, secret)
                if raw_title:
                    title = self._sanitize_filename(raw_title)
                playback_data = self._get_video_play_address(video_id, secret)

            qualities = self._extract_available_qualities(playback_data)
            best_height = self._extract_best_height(playback_data)

            return {
                "id": video_id,
                "title": title,
                "thumbnail": None,
                "webpage_url": url,
                "duration": 0,
                "duration_string": "未知",
                "file_size": "未知",
                "resolution": f"{best_height}p" if best_height else "未知",
                "qualities": qualities,
            }
        except Exception as e:
            logger.error(f"获取寇享视频信息失败: {e}")
            return None

    def download_video(
        self,
        url: str,
        download_dir: Optional[str] = None,
        quality: str = "best",
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        if not self.is_koushare_url(url):
            return {
                "success": False,
                "error": "不是有效的寇享链接",
                "downloaded_files": [],
            }

        target_dir = download_dir or self.download_dir
        os.makedirs(target_dir, exist_ok=True)

        try:
            self._report_progress(progress_callback, 5, "正在解析链接...")
            live_id, video_id = self._parse_koushare_url(url)
            title = f"koushare_{video_id}"

            self._report_progress(progress_callback, 15, "正在获取视频信息...")
            if live_id:
                video_item = self._get_live_video_info(live_id, video_id)
                raw_title = (video_item or {}).get("title") or (video_item or {}).get("name")
                if raw_title:
                    title = self._sanitize_filename(raw_title)
                else:
                    live_info = self._get_live_info(live_id)
                    raw_title = (live_info or {}).get("title") or (live_info or {}).get("name")
                    if raw_title:
                        title = self._sanitize_filename(raw_title)
                playback_data = self._get_live_playback(live_id, video_id)
            else:
                secret = self._check_video_auth(video_id)
                raw_title = self._get_video_title(video_id, secret)
                if raw_title:
                    title = self._sanitize_filename(raw_title)
                playback_data = self._get_video_play_address(video_id, secret)

            mapped_quality = self._map_quality(quality)
            self._report_progress(progress_callback, 25, f"正在获取{mapped_quality}画质播放地址...")
            m3u8_url = self._select_quality_url(playback_data, mapped_quality)

            output_path = os.path.join(target_dir, f"{title}.mp4")
            self._download_with_ffmpeg(m3u8_url, output_path, progress_callback)

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            resolution = self._extract_resolution_for_quality(playback_data, mapped_quality)

            return {
                "success": True,
                "title": title,
                "downloaded_files": [
                    {
                        "type": "video",
                        "path": output_path,
                        "size": file_size,
                        "format": "MP4",
                        "ext": "mp4",
                        "resolution": resolution,
                    }
                ],
                "info": {
                    "id": video_id,
                    "webpage_url": url,
                    "quality": mapped_quality,
                },
            }
        except Exception as e:
            logger.error(f"寇享视频下载失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "downloaded_files": [],
            }

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.koushare.com/",
                "Origin": "https://www.koushare.com",
                "client": "front_web",
                "Content-Type": "application/json",
            })
            if self._access_token:
                self._session.headers["Authorization"] = self._access_token
        return self._session

    def _generate_ks_sign(self, params: dict, method: str) -> Tuple[str, int]:
        method_name = method.upper()
        timestamp = int(time.time() * 1000)
        filtered = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        parts = []

        for key in sorted(filtered.keys()):
            value = filtered[key]
            if isinstance(value, bool):
                parts.append(f"{key}={'true' if value else 'false'}")
            elif isinstance(value, (list, dict)):
                parts.append(f"{key}={json.dumps(value, separators=(',', ':'))}")
            else:
                parts.append(f"{key}={value}")

        param_string = "&".join(parts)
        salt_md5 = hashlib.md5(self.SALT_KEY.encode("utf-8")).hexdigest()
        suffix = f"method={method_name}&timestamp={timestamp}&saltmd5={salt_md5}"
        message = f"{param_string}&{suffix}" if param_string else suffix
        sign = hashlib.md5(message.encode("utf-8")).hexdigest()
        return sign, timestamp

    def _signed_headers(self, params: dict, method: str) -> Dict[str, str]:
        sign, timestamp = self._generate_ks_sign(params, method)
        return {
            "ks-sign": sign,
            "ks-timestamp": str(timestamp),
        }

    def _parse_koushare_url(self, url: str) -> Tuple[Optional[str], str]:
        parsed = urlparse(url)

        live_match = re.search(r"/live/details/(\d+)", parsed.path)
        if live_match:
            live_id = live_match.group(1)
            query = parse_qs(parsed.query)
            video_id = (query.get("vid") or query.get("videoId") or [None])[0]
            if not video_id:
                raise ValueError(f"无法从 URL 解析 videoId: {url}")
            return live_id, str(video_id)

        video_match = re.search(r"/video/(?:details|videodetail)/(\d+)", parsed.path)
        if video_match:
            return None, video_match.group(1)

        raise ValueError(f"无法识别的寇享 URL 格式: {url}")

    def _get_live_info(self, live_id: str) -> Dict[str, Any]:
        url = f"{self.api_base}/live/v2/live/{live_id}"
        response = self._get_session().get(url, headers=self._signed_headers({}, "get"), timeout=15)
        response.raise_for_status()
        data = response.json()
        if not data.get("success") and str(data.get("code", ""))[:3] != "200":
            raise RuntimeError(f"获取直播信息失败: {data}")
        return data.get("data") or {}

    def _get_live_video_info(self, live_id: str, video_id: str) -> Dict[str, Any]:
        params = {"liveId": int(live_id), "pageNum": 1, "pageSize": 200}
        response = self._get_session().get(
            f"{self.api_base}/live/v1/user/livePlayback/list",
            params=params,
            headers=self._signed_headers(params, "get"),
            timeout=15,
        )
        response.raise_for_status()
        items = response.json().get("data") or []
        if isinstance(items, list):
            for item in items:
                if str(item.get("videoId", "")) == str(video_id):
                    return item
        return {}

    def _get_live_playback(self, live_id: str, video_id: str) -> Dict[str, Any]:
        response = self._get_session().post(
            f"{self.api_base}/live/v2/live/playback/{live_id}",
            params={"videoId": video_id},
            json={},
            headers=self._signed_headers({"videoId": video_id}, "post"),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success") and str(data.get("code", ""))[:3] != "200":
            raise RuntimeError(f"获取播放地址失败: {data}")
        return data.get("data") or {}

    def _check_video_auth(self, video_id: str) -> str:
        body = {"id": video_id}
        response = self._get_session().post(
            f"{self.api_base}/video/v1/video/checkVideoAuth",
            json=body,
            headers=self._signed_headers(body, "post"),
            timeout=15,
        )
        response.raise_for_status()
        secret = (response.json().get("data") or {}).get("secret", "")
        if not secret:
            raise RuntimeError(f"checkVideoAuth 未返回 secret: {response.json()}")
        return secret

    def _get_video_title(self, video_id: str, secret: str) -> str:
        params = {"id": video_id, "secret": secret}
        response = self._get_session().get(
            f"{self.api_base}/video/v1/video/info",
            params=params,
            headers=self._signed_headers(params, "get"),
            timeout=15,
        )
        response.raise_for_status()
        return (response.json().get("data") or {}).get("title", "")

    def _get_video_play_address(self, video_id: str, secret: str) -> Dict[str, Any]:
        params = {"videoId": video_id, "secret": secret}
        response = self._get_session().get(
            f"{self.api_base}/video/v1/video/getVideoPlayAddress",
            params=params,
            headers=self._signed_headers(params, "get"),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("success") and str(data.get("code", ""))[:3] != "200":
            raise RuntimeError(f"getVideoPlayAddress 失败: {data}")
        return {"playbackUrls": data.get("data") or []}

    def _map_quality(self, quality: str) -> str:
        quality_key = (quality or "").strip().lower()
        quality_map = {
            "best": "FHD",
            "最佳质量": "FHD",
            "原画": "FHD",
            "1080p": "FHD",
            "超清(1080p)": "FHD",
            "720p": "HD",
            "高清(720p)": "HD",
            "480p": "SD",
            "标清(480p)": "SD",
            "fhd": "FHD",
            "hd": "HD",
            "sd": "SD",
        }
        return quality_map.get(quality_key, "FHD")

    def _select_quality_url(self, playback_data: Dict[str, Any], quality: str = "FHD") -> str:
        quality = quality.upper()

        def pick_url(item: Dict[str, Any]) -> str:
            for key in ("fileUrl", "preUrl", "url", "playUrl"):
                value = item.get(key) or ""
                if ".m3u8" in value:
                    return value
            return ""

        for url_group in playback_data.get("playbackUrls") or []:
            item_list = url_group.get("list") or []

            for item in item_list:
                if (item.get("labelEn") or "").upper() == quality:
                    selected_url = pick_url(item)
                    if selected_url:
                        return selected_url
                    break

            for fallback_quality in ("FHD", "HD", "SD"):
                for item in item_list:
                    selected_url = pick_url(item)
                    if selected_url and (item.get("labelEn") or "").upper() == fallback_quality:
                        return selected_url

        selected_url = playback_data.get("url") or playback_data.get("playUrl")
        if selected_url:
            return selected_url

        raise RuntimeError("播放数据中未找到可用的视频地址")

    def _extract_available_qualities(self, playback_data: Optional[Dict[str, Any]]) -> list:
        qualities = []
        for url_group in (playback_data or {}).get("playbackUrls") or []:
            for item in url_group.get("list") or []:
                label = item.get("labelEn")
                if label and label not in qualities:
                    qualities.append(label)
        return qualities

    def _extract_best_height(self, playback_data: Optional[Dict[str, Any]]) -> int:
        heights = []
        for url_group in (playback_data or {}).get("playbackUrls") or []:
            for item in url_group.get("list") or []:
                height = item.get("height")
                if isinstance(height, int):
                    heights.append(height)
                elif isinstance(height, str) and height.isdigit():
                    heights.append(int(height))
        return max(heights) if heights else 0

    def _extract_resolution_for_quality(self, playback_data: Dict[str, Any], quality: str) -> str:
        for url_group in playback_data.get("playbackUrls") or []:
            for item in url_group.get("list") or []:
                if (item.get("labelEn") or "").upper() == quality.upper():
                    height = item.get("height")
                    if isinstance(height, int):
                        return f"{height}p"
                    if isinstance(height, str) and height.isdigit():
                        return f"{height}p"

        best_height = self._extract_best_height(playback_data)
        return f"{best_height}p" if best_height else "未知"

    def _get_ffmpeg_executable(self) -> str:
        try:
            from backend.ffmpeg_tools import find_ffmpeg

            ffmpeg_path = find_ffmpeg()
            if ffmpeg_path:
                return ffmpeg_path
        except Exception:
            pass

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_windows_ffmpeg = os.path.join(project_root, "ffmpeg.exe")
        if platform.system() == "Windows" and os.path.exists(local_windows_ffmpeg):
            return local_windows_ffmpeg
        return shutil.which("ffmpeg") or "ffmpeg"

    def _parse_m3u8(self, m3u8_url: str) -> Tuple[int, float]:
        headers = {
            "Referer": "https://www.koushare.com/",
            "Origin": "https://www.koushare.com",
        }
        response = requests.get(m3u8_url, headers=headers, timeout=15)
        response.raise_for_status()
        text = response.text

        if "#EXT-X-STREAM-INF" in text:
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    response = requests.get(urljoin(m3u8_url, line), headers=headers, timeout=15)
                    response.raise_for_status()
                    text = response.text
                    break

        total_segments = 0
        total_duration = 0.0
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#EXTINF:"):
                try:
                    total_duration += float(line.split(":", 1)[1].rstrip(","))
                except ValueError:
                    pass
                total_segments += 1

        return total_segments, total_duration

    def _download_with_ffmpeg(self, m3u8_url: str, output_path: str, progress_callback: Optional[Callable]):
        ffmpeg_executable = self._get_ffmpeg_executable()
        total_duration = 0.0

        if ".m3u8" in m3u8_url:
            self._report_progress(progress_callback, 28, "正在解析视频分片信息...")
            try:
                _, total_duration = self._parse_m3u8(m3u8_url)
            except Exception as e:
                logger.warning(f"解析 m3u8 失败: {e}")
        else:
            self._report_progress(progress_callback, 30, "正在下载视频流...")

        command = [
            ffmpeg_executable,
            "-y",
            "-headers",
            "Referer: https://www.koushare.com/\r\nOrigin: https://www.koushare.com\r\n",
            "-i",
            m3u8_url,
            "-c",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            "-progress",
            "pipe:1",
            "-nostats",
            output_path,
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        out_time_us = 0
        last_percent = 30
        last_message = "正在下载视频流..."
        output_queue: queue.Queue[str | None] = queue.Queue()

        def read_progress() -> None:
            try:
                if process.stdout is not None:
                    for output_line in process.stdout:
                        output_queue.put(output_line)
            finally:
                output_queue.put(None)

        reader = threading.Thread(target=read_progress, name="ffmpeg-progress", daemon=True)
        reader.start()
        next_heartbeat = time.monotonic() + 1
        try:
            while True:
                try:
                    queued_line = output_queue.get(timeout=0.25)
                except queue.Empty:
                    if process.poll() is not None and not reader.is_alive():
                        break
                    if time.monotonic() >= next_heartbeat:
                        self._report_progress(progress_callback, last_percent, last_message)
                        next_heartbeat = time.monotonic() + 1
                    continue
                if queued_line is None:
                    break
                line = queued_line.strip()
                if line.startswith("out_time_us="):
                    try:
                        out_time_us = int(line.split("=", 1)[1])
                    except ValueError:
                        pass
                elif line.startswith("progress=") and total_duration > 0:
                    elapsed_seconds = out_time_us / 1_000_000
                    percent = int(30 + min(elapsed_seconds / total_duration, 1.0) * 67)
                    last_percent = percent
                    last_message = (
                        f"下载中 {self._format_time(elapsed_seconds)} / "
                        f"{self._format_time(total_duration)}"
                    )
                    self._report_progress(
                        progress_callback,
                        percent,
                        last_message,
                    )

            process.wait()
            if process.returncode != 0:
                raise RuntimeError(f"ffmpeg 下载失败（returncode={process.returncode}）")
        except BaseException:
            self._stop_ffmpeg(process)
            try:
                os.unlink(output_path)
            except FileNotFoundError:
                pass
            raise
        finally:
            if process.stdout is not None:
                process.stdout.close()
            reader.join(timeout=1)

        self._report_progress(progress_callback, 100, "下载完成")

    @staticmethod
    def _stop_ffmpeg(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    def _format_time(self, seconds: float) -> str:
        total_seconds = int(seconds) if seconds else 0
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _sanitize_filename(self, name: str) -> str:
        sanitized = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
        return sanitized or "koushare_video"

    def _report_progress(self, callback: Optional[Callable], progress: int, message: str):
        if callback:
            callback(progress, message)
