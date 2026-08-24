#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube视频下载模块
基于yt-dlp实现YouTube视频下载功能
"""

import os
import re
import sys
from typing import Optional, Dict, Any, Callable
from loguru import logger

from core.ytdlp_media import collect_media_files, media_options, output_template


# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import yt_dlp
except ImportError:
    logger.error("yt-dlp未安装，请运行: pip install yt-dlp")
    sys.exit(1)


class YouTubeDownloader:
    """YouTube视频下载器"""

    def __init__(
        self,
        download_dir: str = "youtube_downloads",
        ffmpeg_path: Optional[str] = None,
        deno_path: Optional[str] = None,
        proxy_url: Optional[str] = None,
        cookies_from_browser: Optional[str] = None,
    ):
        """
        初始化下载器
        :param download_dir: 下载目录
        """
        self.download_dir = download_dir
        self.ffmpeg_path = ffmpeg_path
        self.deno_path = deno_path
        self.proxy_url = proxy_url
        self.cookies_from_browser = cookies_from_browser
        os.makedirs(download_dir, exist_ok=True)
        self._last_progress = -1  # 记录上次报告的进度

    def is_youtube_url(self, url: str) -> bool:
        """
        检查是否为YouTube链接
        :param url: 待检查的URL
        :return: 是否为YouTube链接
        """
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        ]

        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取YouTube视频信息
        :param url: YouTube视频URL
        :return: 视频信息字典
        """
        if not self.is_youtube_url(url):
            logger.error(f"不是有效的YouTube链接: {url}")
            return None

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            **self._runtime_options(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    "id": info.get('id', ''),
                    "title": info.get('title', ''),
                    "description": info.get('description', ''),
                    "uploader": info.get('uploader', ''),
                    "duration": info.get('duration', 0),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "upload_date": info.get('upload_date', ''),
                    "thumbnail": info.get('thumbnail', ''),
                    "webpage_url": info.get('webpage_url', url),
                    "formats": info.get('formats', []),
                    "duration_string": self._format_duration(info.get('duration', 0)),
                    "file_size": self._format_file_size(info.get('filesize', 0))
                }
        except Exception as e:
            logger.error(f"获取YouTube视频信息失败: {e}")
            return None

    def download_video(
        self,
        url: str,
        download_dir: Optional[str] = None,
        quality: str = "best",
        progress_callback: Optional[Callable] = None,
        download_type: str = "video",
        output_format: str = "mp4",
    ) -> Dict[str, Any]:
        """
        下载YouTube视频
        :param url: YouTube视频URL
        :param download_dir: 下载目录（可选，默认使用初始化时的目录）
        :param quality: 视频质量 ("best", "worst", "720p", "1080p" 等)
        :param progress_callback: 进度回调函数
        :return: 下载结果字典
        """
        if not self.is_youtube_url(url):
            return {
                "success": False,
                "error": "不是有效的YouTube链接",
                "downloaded_files": []
            }

        # 使用指定下载目录或默认目录
        target_dir = download_dir or self.download_dir
        os.makedirs(target_dir, exist_ok=True)

        # 配置下载选项
        download_options = media_options(download_type, output_format)
        ydl_opts = {
            'outtmpl': output_template(target_dir),
            'quiet': False,
            'no_warnings': False,
            'continuedl': True,
            'noprogress': False,
            'retries': 3,
            'fragment_retries': 3,
            'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)] if progress_callback else [],
            **download_options,
            **self._runtime_options(),
        }
        if download_type == "video":
            ydl_opts['format'] = self._get_format_selector(quality)

        try:
            logger.info(f"开始下载YouTube视频: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                downloaded_files = collect_media_files(
                    target_dir,
                    info,
                    download_type,
                    output_format,
                )
                if not downloaded_files:
                    raise RuntimeError("yt-dlp completed without producing the requested output file")

                logger.info(f"YouTube视频下载完成: {info.get('title', 'unknown')}")

                return {
                    "success": True,
                    "title": info.get('title', ''),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', ''),
                    "upload_date": info.get('upload_date', ''),
                    "downloaded_files": downloaded_files,
                    "info": info
                }

        except Exception as e:
            logger.error(f"YouTube视频下载失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "downloaded_files": []
            }

    def _get_format_selector(self, quality: str) -> str:
        """
        根据质量选择器获取yt-dlp格式字符串
        :param quality: 质量字符串
        :return: yt-dlp格式选择器
        """
        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best",
            "worst": "worst[ext=mp4]/worst",
            "4k": self._bounded_format_selector(2160),
            "1440p": self._bounded_format_selector(1440),
            "1080p": self._bounded_format_selector(1080),
            "720p": self._bounded_format_selector(720),
            "480p": self._bounded_format_selector(480),
            "360p": self._bounded_format_selector(360),
        }

        return quality_map.get(quality, quality_map["best"])

    def _bounded_format_selector(self, height: int) -> str:
        limit = f"[height<={height}]"
        return (
            f"bestvideo{limit}[ext=mp4]+bestaudio[ext=m4a]/"
            f"best{limit}[ext=mp4]/bestvideo{limit}+bestaudio/best{limit}"
        )

    def _runtime_options(self) -> Dict[str, Any]:
        options: Dict[str, Any] = {}
        if self.ffmpeg_path:
            options['ffmpeg_location'] = self.ffmpeg_path
        if self.deno_path:
            options['js_runtimes'] = {'deno': {'path': self.deno_path}}
        if self.proxy_url:
            options['proxy'] = self.proxy_url
        if self.cookies_from_browser:
            options['cookiesfrombrowser'] = (self.cookies_from_browser,)
        return options

    def _progress_hook(self, d: Dict[str, Any], callback: Optional[Callable] = None):
        """
        下载进度钩子函数
        :param d: yt-dlp进度字典
        :param callback: 进度回调函数
        """
        if callback is None:
            return

        if d['status'] == 'downloading':
            # 确保 total_bytes 不是 None
            total_bytes = d.get('total_bytes')
            if not total_bytes:
                total_bytes = d.get('total_bytes_estimate')
            if not total_bytes:
                total_bytes = 0
            else:
                total_bytes = int(total_bytes) if isinstance(total_bytes, (int, float)) else 0

            downloaded_bytes = d.get('downloaded_bytes', 0)
            if isinstance(downloaded_bytes, (int, float)):
                downloaded_bytes = int(downloaded_bytes)
            else:
                downloaded_bytes = 0

            if total_bytes and total_bytes > 0:
                progress = int((downloaded_bytes / total_bytes) * 100)

                # 只在进度变化至少1%时才更新（避免频繁更新导致UI闪烁）
                if progress != self._last_progress:
                    self._last_progress = progress
                    speed = d.get('speed', 0)
                    eta = d.get('eta', 0)

                    message = f"下载中 {progress}%"
                    if speed > 0:
                        message += f" ({self._format_speed(speed)})"
                    if eta > 0:
                        message += f" 剩余{self._format_time(eta)}"

                    callback(progress, message)

        elif d['status'] == 'finished':
            self._last_progress = -1  # 重置进度
            callback(100, "下载完成")

        elif d['status'] == 'error':
            self._last_progress = -1  # 重置进度
            callback(0, "下载出错")

    def _format_duration(self, seconds) -> str:
        """格式化时长"""
        # 确保 seconds 是整数（yt-dlp 可能返回 float）
        try:
            seconds = int(seconds) if seconds else 0
        except (ValueError, TypeError):
            return "00:00"

        if seconds <= 0:
            return "00:00"

        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _format_file_size(self, size_bytes) -> str:
        """格式化文件大小"""
        # 确保 size_bytes 是数字（yt-dlp 可能返回 float 或 None）
        try:
            size_bytes = float(size_bytes) if size_bytes else 0
        except (ValueError, TypeError):
            return "未知"

        if size_bytes <= 0:
            return "未知"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} TB"

    def _format_speed(self, speed_bps) -> str:
        """格式化下载速度"""
        # 确保 speed_bps 是数字
        try:
            speed_bps = float(speed_bps) if speed_bps else 0
        except (ValueError, TypeError):
            return "未知"

        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if speed_bps < 1024.0:
                return f"{speed_bps:.1f} {unit}"
            speed_bps /= 1024.0

        return f"{speed_bps:.1f} TB/s"

    def _format_time(self, seconds) -> str:
        """格式化时间"""
        # 确保 seconds 是整数
        try:
            seconds = int(seconds) if seconds else 0
        except (ValueError, TypeError):
            return "0秒"

        if seconds <= 0:
            return "0秒"

        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分钟"
        else:
            hours = seconds // 3600
            return f"{hours}小时"


class YouTubeInfo:
    """YouTube视频信息类"""

    def __init__(self, info_dict: Dict[str, Any]):
        """
        初始化视频信息
        :param info_dict: yt-dlp返回的信息字典
        """
        self._info = info_dict

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self._info.get("id", ""),
            "title": self._info.get("title", ""),
            "description": self._info.get("description", ""),
            "uploader": self._info.get("uploader", ""),
            "duration": self._info.get("duration", 0),
            "duration_string": self._format_duration(self._info.get("duration", 0)),
            "view_count": self._info.get("view_count", 0),
            "like_count": self._info.get("like_count", 0),
            "upload_date": self._info.get("upload_date", ""),
            "thumbnail": self._info.get("thumbnail", ""),
            "webpage_url": self._info.get("webpage_url", ""),
            "file_size": self._format_file_size(self._info.get("filesize", 0)),
            "resolution": f"{self._info.get('width', 0)}x{self._info.get('height', 0)}",
            "fps": self._info.get('fps', 0),
            "format": self._info.get('format', ''),
            "ext": self._info.get('ext', 'mp4')
        }

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds <= 0:
            return "00:00"

        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes <= 0:
            return "未知"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} TB"
