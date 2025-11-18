#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Twitter/X视频下载模块
基于yt-dlp实现Twitter视频下载功能
"""

import os
import re
import sys
from typing import Optional, Dict, Any, Callable
from loguru import logger


# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import yt_dlp
except ImportError:
    logger.error("yt-dlp未安装，请运行: pip install yt-dlp")
    sys.exit(1)


class TwitterDownloader:
    """Twitter/X视频下载器"""

    def __init__(self, download_dir: str = "twitter_downloads"):
        """
        初始化下载器
        :param download_dir: 下载目录
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self._last_progress = -1  # 记录上次报告的进度

    def is_twitter_url(self, url: str) -> bool:
        """
        检查是否为Twitter/X链接
        :param url: 待检查的URL
        :return: 是否为Twitter/X链接
        """
        twitter_patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'https?://(?:www\.)?twitter\.com/i/web/status/\d+',
            r'https?://(?:www\.)?x\.com/i/web/status/\d+',
            r'https?://t\.co/[a-zA-Z0-9]+',  # 短链接，需要解析
        ]

        for pattern in twitter_patterns:
            if re.match(pattern, url):
                return True
        return False

    def extract_twitter_url_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取Twitter/X链接
        :param text: 包含链接的文本
        :return: 提取的Twitter/X链接
        """
        # 匹配Twitter/X链接的正则表达式
        patterns = [
            r'https?://(?:www\.)?twitter\.com/\w+/status/\d+',
            r'https?://(?:www\.)?x\.com/\w+/status/\d+',
            r'https?://(?:www\.)?twitter\.com/i/web/status/\d+',
            r'https?://(?:www\.)?x\.com/i/web/status/\d+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        # 检查t.co短链接
        tco_pattern = r'https?://t\.co/[a-zA-Z0-9]+'
        match = re.search(tco_pattern, text)
        if match:
            # 短链接需要进一步解析，这里先返回，由上层处理
            return match.group(0)

        return None

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取Twitter/X视频信息
        :param url: Twitter/X视频URL
        :return: 视频信息字典
        """
        if not self.is_twitter_url(url):
            logger.error(f"不是有效的Twitter/X链接: {url}")
            return None

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Twitter/X特有的信息处理
                uploader = info.get('uploader', '') or info.get('channel', '')
                title = info.get('title', '') or f"来自 @{uploader} 的推文"

                return {
                    "id": info.get('id', ''),
                    "title": title,
                    "description": info.get('description', ''),
                    "uploader": uploader,
                    "duration": info.get('duration', 0),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "retweet_count": info.get('retweet_count', 0),
                    "upload_date": info.get('upload_date', ''),
                    "thumbnail": info.get('thumbnail', ''),
                    "webpage_url": info.get('webpage_url', url),
                    "formats": info.get('formats', []),
                    "duration_string": self._format_duration(info.get('duration', 0)),
                    "file_size": self._format_file_size(info.get('filesize', 0)),
                    "tweet_id": self._extract_tweet_id(url)
                }
        except Exception as e:
            import traceback
            logger.error(f"获取Twitter/X视频信息失败: {e}")
            logger.error(f"详细错误: {traceback.format_exc()}")
            return None

    def download_video(self, url: str, download_dir: Optional[str] = None,
                      quality: str = "best", progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        下载Twitter/X视频
        :param url: Twitter/X视频URL
        :param download_dir: 下载目录（可选，默认使用初始化时的目录）
        :param quality: 视频质量 ("best", "worst" 等)
        :param progress_callback: 进度回调函数
        :return: 下载结果字典
        """
        if not self.is_twitter_url(url):
            return {
                "success": False,
                "error": "不是有效的Twitter/X链接",
                "downloaded_files": []
            }

        # 使用指定下载目录或默认目录
        target_dir = download_dir or self.download_dir
        os.makedirs(target_dir, exist_ok=True)

        # 配置下载选项
        ydl_opts = {
            'format': self._get_format_selector(quality),
            'outtmpl': os.path.join(target_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'continuedl': True,
            'noprogress': False,
            'progress_hooks': [lambda d: self._progress_hook(d, progress_callback)] if progress_callback else [],
            # Twitter/X特定选项
            'extract_flat': False,
        }

        try:
            logger.info(f"开始下载Twitter/X视频: {url}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # 获取下载的文件信息
                downloaded_files = []

                # 主视频文件
                if 'requested_downloads' in info:
                    for download_info in info['requested_downloads']:
                        downloaded_files.append({
                            "type": "video",
                            "path": download_info.get('filepath', ''),
                            "size": download_info.get('filesize', 0),
                            "format": download_info.get('format', ''),
                            "ext": download_info.get('ext', ''),
                            "fps": download_info.get('fps', 0),
                            "resolution": f"{download_info.get('width', 0)}x{download_info.get('height', 0)}"
                        })

                # 缩略图
                thumbnail_path = os.path.join(target_dir, f"{info.get('title', 'video')}_thumbnail.jpg")
                if info.get('thumbnail'):
                    downloaded_files.append({
                        "type": "thumbnail",
                        "path": thumbnail_path,
                        "url": info.get('thumbnail', '')
                    })

                logger.info(f"Twitter/X视频下载完成: {info.get('title', 'unknown')}")

                return {
                    "success": True,
                    "title": info.get('title', ''),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', ''),
                    "upload_date": info.get('upload_date', ''),
                    "tweet_id": self._extract_tweet_id(url),
                    "downloaded_files": downloaded_files,
                    "info": info
                }

        except Exception as e:
            logger.error(f"Twitter/X视频下载失败: {e}")
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
            "best": "best[ext=mp4]/best",
            "worst": "worst[ext=mp4]/worst",
            "1080p": "best[height<=1080][ext=mp4]/best[height<=1080]/best",
            "720p": "best[height<=720][ext=mp4]/best[height<=720]/best",
            "480p": "best[height<=480][ext=mp4]/best[height<=480]/best",
            "360p": "best[height<=360][ext=mp4]/best[height<=360]/best",
        }

        return quality_map.get(quality, "best[ext=mp4]/best")

    def _progress_hook(self, d: Dict[str, Any], callback: Optional[Callable] = None):
        """
        下载进度钩子函数
        :param d: yt-dlp进度字典
        :param callback: 进度回调函数
        """
        if callback is None:
            return

        if d['status'] == 'downloading':
            # 确保 total_bytes 不是 None（Twitter/X 视频可能两个都是 None）
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

    def _extract_tweet_id(self, url: str) -> str:
        """
        从URL中提取推文ID
        :param url: Twitter/X URL
        :return: 推文ID
        """
        # 匹配推文ID的正则表达式
        patterns = [
            r'/status/(\d+)',
            r'/web/status/(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return ""

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


class TwitterInfo:
    """Twitter/X视频信息类"""

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
            "retweet_count": self._info.get("retweet_count", 0),
            "upload_date": self._info.get("upload_date", ""),
            "thumbnail": self._info.get("thumbnail", ""),
            "webpage_url": self._info.get("webpage_url", ""),
            "file_size": self._format_file_size(self._info.get("filesize", 0)),
            "resolution": f"{self._info.get('width', 0)}x{self._info.get('height', 0)}",
            "fps": self._info.get('fps', 0),
            "format": self._info.get('format', ''),
            "ext": self._info.get('ext', 'mp4'),
            "tweet_id": self._extract_tweet_id(self._info.get('webpage_url', ''))
        }

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

    def _extract_tweet_id(self, url: str) -> str:
        """
        从URL中提取推文ID
        :param url: Twitter/X URL
        :return: 推文ID
        """
        import re

        patterns = [
            r'/status/(\d+)',
            r'/web/status/(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return ""