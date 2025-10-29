#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
下载管理器 - 使用纯 Python 实现
"""

import os
import sys
from typing import Optional, Callable, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.pure_python_extractor import PurePythonExtractor


class DownloadWorker(QThread):
    """下载工作线程"""

    # 信号
    progress_updated = pyqtSignal(str, int, str)  # video_id, progress, message
    status_changed = pyqtSignal(str, str)  # video_id, status
    download_completed = pyqtSignal(str, dict)  # video_id, result
    error_occurred = pyqtSignal(str, str)  # video_id, error_message

    def __init__(self, video_id: str, url: str, download_dir: str):
        super().__init__()
        self.video_id = video_id
        self.url = url
        self.download_dir = download_dir
        self.extractor = PurePythonExtractor()

    def run(self):
        """执行下载"""
        try:
            # 更新状态为下载中
            self.status_changed.emit(self.video_id, "downloading")

            # 发送进度
            self.progress_updated.emit(self.video_id, 10, "正在解析视频...")

            # 定义进度回调函数
            def progress_callback(progress, message):
                self.progress_updated.emit(self.video_id, progress, message)

            # 开始下载，传递进度回调
            result = self.extractor.download_video(self.url, self.download_dir, progress_callback)

            if result.get("success"):
                # 下载成功
                self.progress_updated.emit(self.video_id, 100, "下载完成")
                self.status_changed.emit(self.video_id, "success")
                self.download_completed.emit(self.video_id, result)
            else:
                # 下载失败
                error = result.get("error", "未知错误")
                self.status_changed.emit(self.video_id, "error")
                self.error_occurred.emit(self.video_id, error)

        except Exception as e:
            # 异常处理
            self.status_changed.emit(self.video_id, "error")
            self.error_occurred.emit(self.video_id, str(e))


class DownloadManager(QObject):
    """下载管理器"""

    # 信号
    video_added = pyqtSignal(dict)  # 添加视频
    progress_updated = pyqtSignal(str, int, str)  # 进度更新
    status_changed = pyqtSignal(str, str)  # 状态改变
    download_completed = pyqtSignal(str, dict)  # 下载完成
    error_occurred = pyqtSignal(str, str)  # 错误发生

    def __init__(self, download_dir: str = "douyin_downloads"):
        super().__init__()
        self.download_dir = download_dir
        self.workers: Dict[str, DownloadWorker] = {}
        self.extractor = PurePythonExtractor()

        # 确保下载目录存在
        os.makedirs(download_dir, exist_ok=True)

    def add_download(self, url: str, video_id: Optional[str] = None) -> Dict[str, Any]:
        """
        添加下载任务
        :param url: 视频URL
        :param video_id: 视频ID（可选，自动生成）
        :return: 视频信息
        """
        # 生成视频ID
        if not video_id:
            import hashlib
            video_id = hashlib.md5(url.encode()).hexdigest()[:16]

        # 先获取视频信息
        try:
            print(f"🔍 正在获取视频信息: {url}")
            video_info_obj = self.extractor.get_video_info(url)

            if not video_info_obj:
                # 如果获取信息失败，使用默认信息
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": "抖音视频",
                    "format": "MP4",
                    "size": "未知",
                    "resolution": "未知",
                    "duration": "未知",
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": None
                }
            else:
                # 使用获取到的信息
                video_info = video_info_obj.to_dict()
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": video_info.get("desc", "抖音视频")[:50],
                    "format": "MP4" if video_info.get("type") == "video" else "图片集",
                    "size": "未知",
                    "resolution": "1080p" if video_info.get("type") == "video" else "未知",
                    "duration": "未知",
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": None
                }

            # 发送信号
            self.video_added.emit(video_data)

            # 立即开始下载
            self.start_download(video_id, url)

            return video_data

        except Exception as e:
            print(f"❌ 添加下载任务失败: {e}")
            import traceback
            traceback.print_exc()

            # 返回基本信息
            video_data = {
                "id": video_id,
                "url": url,
                "title": "抖音视频",
                "format": "MP4",
                "size": "未知",
                "resolution": "未知",
                "duration": "未知",
                "status": "error",
                "progress": 0,
                "thumbnail": None
            }
            self.video_added.emit(video_data)
            self.error_occurred.emit(video_id, str(e))
            return video_data

    def start_download(self, video_id: str, url: str):
        """
        开始下载
        :param video_id: 视频ID
        :param url: 视频URL
        """
        # 创建下载工作线程
        worker = DownloadWorker(video_id, url, self.download_dir)

        # 连接信号
        worker.progress_updated.connect(self.progress_updated)
        worker.status_changed.connect(self.status_changed)
        worker.download_completed.connect(self.download_completed)
        worker.error_occurred.connect(self.error_occurred)

        # 线程完成后清理
        worker.finished.connect(lambda: self._cleanup_worker(video_id))

        # 保存引用并启动
        self.workers[video_id] = worker
        worker.start()

    def _cleanup_worker(self, video_id: str):
        """清理工作线程"""
        if video_id in self.workers:
            worker = self.workers[video_id]
            worker.deleteLater()
            del self.workers[video_id]

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "未知"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} TB"

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds == 0:
            return "未知"

        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def get_download_dir(self) -> str:
        """获取下载目录"""
        return self.download_dir

    def set_download_dir(self, directory: str):
        """设置下载目录"""
        self.download_dir = directory
        os.makedirs(directory, exist_ok=True)
