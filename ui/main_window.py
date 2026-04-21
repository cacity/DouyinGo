#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主窗口
"""

import os
import sys
import subprocess
import platform

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from ui.sidebar import Sidebar
from ui.topbar import TopBar
from ui.video_list import VideoList
from ui.styles import MAIN_WINDOW_STYLE
from core.downloader import DownloadManager
from core.youtube_downloader import YouTubeDownloader
from core.twitter_downloader import TwitterDownloader
from core.koushare_downloader import KoushareDownloader
from core.thumbnail_extractor import get_video_duration, format_duration


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.current_platform = "douyin"
        self.download_manager = DownloadManager()
        self.youtube_downloader = YouTubeDownloader()
        self.twitter_downloader = TwitterDownloader()
        self.koushare_downloader = KoushareDownloader()
        self.current_quality = "原画"
        self.download_workers = {}  # 保存活跃的下载工作线程
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("VideoGo - 多平台视频下载工具")
        self.setMinimumSize(QSize(1200, 700))
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "icons8-youtube-100.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 侧边栏
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 右侧内容区域
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 顶部工具栏
        self.topbar = TopBar()
        content_layout.addWidget(self.topbar)

        # 视频列表
        self.video_list = VideoList()
        content_layout.addWidget(self.video_list)

        main_layout.addLayout(content_layout)

    def connect_signals(self):
        """连接信号槽"""
        # 顶部工具栏信号
        self.topbar.paste_clicked.connect(self.on_paste_clicked)
        self.topbar.download_type_changed.connect(self.on_download_type_changed)
        self.topbar.quality_changed.connect(self.on_quality_changed)
        self.topbar.format_changed.connect(self.on_format_changed)

        # 侧边栏信号
        self.sidebar.page_changed.connect(self.on_page_changed)
        self.sidebar.platform_changed.connect(self.on_platform_changed)

        # 视频列表信号
        self.video_list.download_clicked.connect(self.on_download_clicked)
        self.video_list.open_folder_clicked.connect(self.on_open_folder_clicked)
        self.video_list.refresh_clicked.connect(self.on_refresh_clicked)
        self.video_list.delete_clicked.connect(self.on_delete_clicked)

        # 下载管理器信号
        self.download_manager.video_added.connect(self.on_video_added)
        self.download_manager.progress_updated.connect(self.on_progress_updated)
        self.download_manager.status_changed.connect(self.on_status_changed)
        self.download_manager.download_completed.connect(self.on_download_completed)
        self.download_manager.error_occurred.connect(self.on_error_occurred)

    def extract_url_by_platform(self, text: str, platform: str) -> str:
        """
        根据平台从文本中提取对应的URL
        """
        import re

        if platform == "douyin":
            return self.extract_douyin_url(text)
        elif platform == "youtube":
            return self.extract_youtube_url(text)
        elif platform == "twitter":
            return self.extract_twitter_url(text)
        elif platform == "koushare":
            return self.extract_koushare_url(text)
        else:
            return text

    def extract_douyin_url(self, text: str) -> str:
        """
        从文本中提取抖音链接
        支持从分享文本中提取 URL
        """
        import re

        # 匹配抖音链接的正则表达式
        patterns = [
            r'https?://v\.douyin\.com/[a-zA-Z0-9]+/?',
            r'https?://www\.douyin\.com/video/\d+',
            r'https?://www\.iesdouyin\.com/share/video/\d+',
            r'https?://dy\.tt/[a-zA-Z0-9]+'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        # 如果没有找到 URL，但文本本身看起来像 URL
        text = text.strip()
        if text.startswith('http') and ('douyin.com' in text or 'dy.tt' in text):
            # 提取第一个空格之前的部分
            return text.split()[0]

        return text

    def extract_youtube_url(self, text: str) -> str:
        """
        从文本中提取YouTube链接
        """
        import re

        # 匹配YouTube链接的正则表达式
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/v/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        # 如果文本本身是YouTube链接
        text = text.strip()
        if text.startswith('http') and ('youtube.com' in text or 'youtu.be' in text):
            return text.split()[0]

        return text

    def extract_twitter_url(self, text: str) -> str:
        """
        从文本中提取Twitter/X链接
        """
        import re

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

        # 如果文本本身是Twitter/X链接
        text = text.strip()
        if text.startswith('http') and ('twitter.com' in text or 'x.com' in text):
            return text.split()[0]

        return text

    def extract_koushare_url(self, text: str) -> str:
        """
        从文本中提取寇享链接
        """
        extracted_url = self.koushare_downloader.extract_koushare_url_from_text(text)
        return extracted_url or text.strip()

    def on_paste_clicked(self):
        """粘贴按钮点击"""
        # 获取剪贴板内容
        clipboard_text = self.topbar.get_clipboard_text()

        if not clipboard_text:
            QMessageBox.warning(self, "提示", "剪贴板为空，请先复制视频链接")
            return

        # 根据当前平台提取对应的URL
        url = self.extract_url_by_platform(clipboard_text, self.current_platform)

        # 验证链接
        if not self.validate_platform_url(url, self.current_platform):
            platform_names = {
                "douyin": "抖音",
                "youtube": "YouTube",
                "twitter": "Twitter/X",
                "koushare": "寇享"
            }
            platform_name = platform_names.get(self.current_platform, "当前平台")

            supported_formats = self.get_supported_formats(self.current_platform)
            QMessageBox.warning(self, "提示",
                              f"未找到有效的{platform_name}链接\n\n支持的格式：\n{supported_formats}\n\n剪贴板内容：\n{clipboard_text[:100]}...")
            return

        # 添加下载任务
        try:
            self.topbar.set_status("正在解析链接...")

            if self.current_platform == "douyin":
                self.download_manager.add_download(url)
            elif self.current_platform == "youtube":
                self.add_youtube_download(url)
            elif self.current_platform == "twitter":
                self.add_twitter_download(url)
            elif self.current_platform == "koushare":
                self.add_koushare_download(url)

            self.topbar.set_status(f"已添加下载任务 (共 {self.video_list.get_video_count()} 个)")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加下载任务失败：{str(e)}")
            self.topbar.set_status("")

    def validate_platform_url(self, url: str, platform: str) -> bool:
        """验证URL是否属于指定平台"""
        if platform == "douyin":
            return "douyin.com" in url or "dy.tt" in url
        elif platform == "youtube":
            return "youtube.com" in url or "youtu.be" in url
        elif platform == "twitter":
            return "twitter.com" in url or "x.com" in url
        elif platform == "koushare":
            return self.koushare_downloader.is_koushare_url(url)
        return False

    def get_supported_formats(self, platform: str) -> str:
        """获取平台支持的链接格式"""
        formats = {
            "douyin": "- https://v.douyin.com/xxxxx/\n- https://www.douyin.com/video/xxxxx",
            "youtube": "- https://www.youtube.com/watch?v=xxxxx\n- https://youtu.be/xxxxx\n- https://www.youtube.com/shorts/xxxxx",
            "twitter": "- https://twitter.com/user/status/xxxxx\n- https://x.com/user/status/xxxxx",
            "koushare": "- https://www.koushare.com/live/details/xxxxx?vid=xxxxx\n- https://www.koushare.com/video/details/xxxxx"
        }
        return formats.get(platform, "未知格式")

    def is_douyin_url(self, url: str) -> bool:
        """验证是否为抖音链接"""
        return "douyin.com" in url or "dy.tt" in url

    def on_download_type_changed(self, download_type: str):
        """下载类型改变"""
        print(f"下载类型改变: {download_type}")
        # TODO: 实现下载类型切换逻辑

    def on_quality_changed(self, quality: str):
        """质量改变"""
        self.current_quality = quality
        print(f"质量改变: {quality}")

    def on_format_changed(self, format_type: str):
        """格式改变"""
        print(f"格式改变: {format_type}")
        # TODO: 实现格式切换逻辑

    def on_platform_changed(self, platform: str):
        """平台切换"""
        print(f"平台切换: {platform}")
        self.current_platform = platform

        # 更新顶部工具栏显示
        self.topbar.set_platform(platform)
        self.topbar.update_quality_options(platform)

    def on_page_changed(self, page_id: str):
        """页面切换"""
        print(f"页面切换: {page_id}")
        if page_id == "settings":
            QMessageBox.information(self, "设置", "设置功能开发中...")

    def on_download_clicked(self, video_id: str):
        """下载按钮点击"""
        print(f"下载视频: {video_id}")

    def on_open_folder_clicked(self, video_id: str):
        """打开文件夹"""
        download_dir = self.download_manager.get_download_dir()
        self.open_directory(download_dir)

    def on_refresh_clicked(self, video_id: str):
        """刷新按钮点击"""
        print(f"刷新视频: {video_id}")
        # TODO: 实现刷新逻辑

    def add_youtube_download(self, url: str):
        """添加YouTube下载任务"""
        import hashlib

        # 生成视频ID
        video_id = hashlib.md5(f"youtube_{url}".encode()).hexdigest()[:16]

        try:
            # 获取视频信息
            video_info = self.youtube_downloader.get_video_info(url)

            if video_info:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": video_info.get("title", "YouTube视频")[:50],
                    "format": "MP4",
                    "size": video_info.get("file_size", "未知"),
                    "resolution": video_info.get("resolution", "未知"),
                    "duration": video_info.get("duration_string", "未知"),
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": video_info.get("thumbnail"),
                    "platform": "youtube"
                }
            else:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": "YouTube视频",
                    "format": "MP4",
                    "size": "未知",
                    "resolution": "未知",
                    "duration": "未知",
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": None,
                    "platform": "youtube"
                }

            # 添加到视频列表
            self.video_list.add_video(video_data)

            # 开始下载
            self.start_youtube_download(video_id, url)

        except Exception as e:
            raise Exception(f"YouTube下载失败: {str(e)}")

    def add_twitter_download(self, url: str):
        """添加Twitter下载任务"""
        import hashlib

        # 生成视频ID
        video_id = hashlib.md5(f"twitter_{url}".encode()).hexdigest()[:16]

        try:
            # 获取视频信息
            video_info = self.twitter_downloader.get_video_info(url)

            if video_info:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": video_info.get("title", "Twitter视频")[:50],
                    "format": "MP4",
                    "size": video_info.get("file_size", "未知"),
                    "resolution": video_info.get("resolution", "未知"),
                    "duration": video_info.get("duration_string", "未知"),
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": video_info.get("thumbnail"),
                    "platform": "twitter"
                }
            else:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": "Twitter视频",
                    "format": "MP4",
                    "size": "未知",
                    "resolution": "未知",
                    "duration": "未知",
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": None,
                    "platform": "twitter"
                }

            # 添加到视频列表
            self.video_list.add_video(video_data)

            # 开始下载
            self.start_twitter_download(video_id, url)

        except Exception as e:
            raise Exception(f"Twitter下载失败: {str(e)}")

    def add_koushare_download(self, url: str):
        """添加寇享下载任务"""
        import hashlib

        video_id = hashlib.md5(f"koushare_{url}".encode()).hexdigest()[:16]

        try:
            video_info = self.koushare_downloader.get_video_info(url)

            if video_info:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": video_info.get("title", "寇享视频")[:50],
                    "format": "MP4",
                    "size": video_info.get("file_size", "未知"),
                    "resolution": video_info.get("resolution", "未知"),
                    "duration": video_info.get("duration_string", "未知"),
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": video_info.get("thumbnail"),
                    "platform": "koushare"
                }
            else:
                video_data = {
                    "id": video_id,
                    "url": url,
                    "title": "寇享视频",
                    "format": "MP4",
                    "size": "未知",
                    "resolution": "未知",
                    "duration": "未知",
                    "status": "pending",
                    "progress": 0,
                    "thumbnail": None,
                    "platform": "koushare"
                }

            self.video_list.add_video(video_data)
            self.start_koushare_download(video_id, url)

        except Exception as e:
            raise Exception(f"寇享下载失败: {str(e)}")

    def _cleanup_worker(self, video_id: str):
        """清理完成的工作线程"""
        if video_id in self.download_workers:
            worker = self.download_workers[video_id]
            worker.deleteLater()
            del self.download_workers[video_id]

    def start_youtube_download(self, video_id: str, url: str):
        """开始YouTube下载"""
        class YouTubeDownloadWorker(QThread):
            progress_updated = pyqtSignal(str, int, str)
            status_changed = pyqtSignal(str, str)
            download_completed = pyqtSignal(str, dict)
            error_occurred = pyqtSignal(str, str)

            def __init__(self, video_id, url, downloader):
                super().__init__()
                self.video_id = video_id
                self.url = url
                self.downloader = downloader

            def run(self):
                try:
                    self.status_changed.emit(self.video_id, "downloading")
                    self.progress_updated.emit(self.video_id, 10, "正在解析视频...")

                    def progress_callback(progress, message):
                        self.progress_updated.emit(self.video_id, progress, message)

                    result = self.downloader.download_video(self.url, progress_callback=progress_callback)

                    if result.get("success"):
                        self.progress_updated.emit(self.video_id, 100, "下载完成")
                        self.status_changed.emit(self.video_id, "success")
                        self.download_completed.emit(self.video_id, result)
                    else:
                        error = result.get("error", "未知错误")
                        self.status_changed.emit(self.video_id, "error")
                        self.error_occurred.emit(self.video_id, error)

                except Exception as e:
                    self.status_changed.emit(self.video_id, "error")
                    self.error_occurred.emit(self.video_id, str(e))

        # 创建并启动工作线程
        worker = YouTubeDownloadWorker(video_id, url, self.youtube_downloader)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.download_completed.connect(self.on_youtube_download_completed)
        worker.error_occurred.connect(self.on_error_occurred)
        worker.finished.connect(lambda: self._cleanup_worker(video_id))

        # 保存工作线程引用
        self.download_workers[video_id] = worker
        worker.start()

    def start_twitter_download(self, video_id: str, url: str):
        """开始Twitter下载"""
        class TwitterDownloadWorker(QThread):
            progress_updated = pyqtSignal(str, int, str)
            status_changed = pyqtSignal(str, str)
            download_completed = pyqtSignal(str, dict)
            error_occurred = pyqtSignal(str, str)

            def __init__(self, video_id, url, downloader):
                super().__init__()
                self.video_id = video_id
                self.url = url
                self.downloader = downloader

            def run(self):
                try:
                    self.status_changed.emit(self.video_id, "downloading")
                    self.progress_updated.emit(self.video_id, 10, "正在解析视频...")

                    def progress_callback(progress, message):
                        self.progress_updated.emit(self.video_id, progress, message)

                    result = self.downloader.download_video(self.url, progress_callback=progress_callback)

                    if result.get("success"):
                        self.progress_updated.emit(self.video_id, 100, "下载完成")
                        self.status_changed.emit(self.video_id, "success")
                        self.download_completed.emit(self.video_id, result)
                    else:
                        error = result.get("error", "未知错误")
                        self.status_changed.emit(self.video_id, "error")
                        self.error_occurred.emit(self.video_id, error)

                except Exception as e:
                    self.status_changed.emit(self.video_id, "error")
                    self.error_occurred.emit(self.video_id, str(e))

        # 创建并启动工作线程
        worker = TwitterDownloadWorker(video_id, url, self.twitter_downloader)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.download_completed.connect(self.on_twitter_download_completed)
        worker.error_occurred.connect(self.on_error_occurred)
        worker.finished.connect(lambda: self._cleanup_worker(video_id))

        # 保存工作线程引用
        self.download_workers[video_id] = worker
        worker.start()

    def start_koushare_download(self, video_id: str, url: str):
        """开始寇享下载"""
        class KoushareDownloadWorker(QThread):
            progress_updated = pyqtSignal(str, int, str)
            status_changed = pyqtSignal(str, str)
            download_completed = pyqtSignal(str, dict)
            error_occurred = pyqtSignal(str, str)

            def __init__(self, video_id, url, downloader, quality):
                super().__init__()
                self.video_id = video_id
                self.url = url
                self.downloader = downloader
                self.quality = quality

            def run(self):
                try:
                    self.status_changed.emit(self.video_id, "downloading")
                    self.progress_updated.emit(self.video_id, 10, "正在解析视频...")

                    def progress_callback(progress, message):
                        self.progress_updated.emit(self.video_id, progress, message)

                    result = self.downloader.download_video(
                        self.url,
                        quality=self.quality,
                        progress_callback=progress_callback
                    )

                    if result.get("success"):
                        self.progress_updated.emit(self.video_id, 100, "下载完成")
                        self.status_changed.emit(self.video_id, "success")
                        self.download_completed.emit(self.video_id, result)
                    else:
                        error = result.get("error", "未知错误")
                        self.status_changed.emit(self.video_id, "error")
                        self.error_occurred.emit(self.video_id, error)

                except Exception as e:
                    self.status_changed.emit(self.video_id, "error")
                    self.error_occurred.emit(self.video_id, str(e))

        worker = KoushareDownloadWorker(video_id, url, self.koushare_downloader, self.current_quality)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.download_completed.connect(self.on_koushare_download_completed)
        worker.error_occurred.connect(self.on_error_occurred)
        worker.finished.connect(lambda: self._cleanup_worker(video_id))

        self.download_workers[video_id] = worker
        worker.start()

    def on_youtube_download_completed(self, video_id: str, result: dict):
        """YouTube下载完成处理"""
        # 显示状态
        self.topbar.set_status(f"✅ YouTube下载完成")

        # 记录日志
        total_videos = len(self.video_list.video_cards)
        print(f"📊 YouTube下载完成 - 视频ID: {video_id}, 总视频数: {total_videos}")

        self.handle_download_completed(video_id, result, "YouTube")

    def on_twitter_download_completed(self, video_id: str, result: dict):
        """Twitter下载完成处理"""
        # 显示状态
        self.topbar.set_status(f"✅ Twitter/X下载完成")

        # 记录日志
        total_videos = len(self.video_list.video_cards)
        print(f"📊 Twitter/X下载完成 - 视频ID: {video_id}, 总视频数: {total_videos}")

        self.handle_download_completed(video_id, result, "Twitter/X")

    def on_koushare_download_completed(self, video_id: str, result: dict):
        """寇享下载完成处理"""
        self.topbar.set_status("✅ 寇享下载完成")

        total_videos = len(self.video_list.video_cards)
        print(f"📊 寇享下载完成 - 视频ID: {video_id}, 总视频数: {total_videos}")

        self.handle_download_completed(video_id, result, "寇享")

    def handle_download_completed(self, video_id: str, result: dict, platform: str):
        """通用下载完成处理"""
        # 不在这里更新状态栏，避免与on_download_completed重复

        # 更新缩略图、文件大小和时长
        downloaded_files = result.get("downloaded_files", [])
        for file_info in downloaded_files:
            if file_info.get("type") == "video":
                # 更新缩略图
                thumbnail_path = file_info.get("thumbnail")
                if thumbnail_path:
                    self.video_list.update_video_thumbnail(video_id, thumbnail_path)
                    print(f"📸 已更新{platform}视频 {video_id} 的缩略图")

                # 更新文件大小
                video_path = file_info.get("path")
                if video_path and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    self.video_list.update_video_file_size(video_id, file_size)
                    print(f"💾 已更新{platform}视频 {video_id} 的文件大小")

                    # 更新视频时长
                    duration_seconds = get_video_duration(video_path)
                    if duration_seconds > 0:
                        duration_str = format_duration(duration_seconds)
                        self.video_list.update_video_duration(video_id, duration_str)
                        print(f"⏱️ 已更新{platform}视频 {video_id} 的时长: {duration_str}")

        # 显示通知
        file_count = len(downloaded_files)
        QMessageBox.information(self, "下载完成",
                              f"{platform}视频下载完成！\n共下载 {file_count} 个文件")

    def on_delete_clicked(self, video_id: str):
        """删除按钮点击"""
        # 获取视频卡片信息
        if video_id not in self.video_list.video_cards:
            return

        video_card = self.video_list.video_cards[video_id]
        video_title = video_card.video_data.get("title", "未知视频")

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除这个任务吗？\n\n标题: {video_title}\n\n注意：这只会删除任务卡片，不会删除已下载的文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 删除视频卡片
            self.video_list.remove_video(video_id)

            # 更新状态栏
            remaining_count = self.video_list.get_video_count()
            if remaining_count > 0:
                self.topbar.set_status(f"剩余 {remaining_count} 个任务")
            else:
                self.topbar.set_status("已删除下载任务")

    def on_video_added(self, video_data: dict):
        """视频添加完成"""
        self.video_list.add_video(video_data)

    def on_progress_updated(self, video_id: str, progress: int, message: str):
        """进度更新"""
        self.video_list.update_video_progress(video_id, progress)

    def on_status_changed(self, video_id: str, status: str):
        """状态改变"""
        self.video_list.update_video_status(video_id, status)

    def on_download_completed(self, video_id: str, result: dict):
        """下载完成 - 抖音下载"""
        # 计算已完成的下载数（只统计当前视频）
        if video_id in self.video_list.video_cards:
            self.topbar.set_status(f"✅ 下载完成")

        # 记录日志
        total_videos = len(self.video_list.video_cards)
        success_count = sum(1 for card in self.video_list.video_cards.values()
                          if card.video_data.get("status") == "success")
        print(f"📊 下载完成统计 - 总视频数: {total_videos}, 成功: {success_count}")

        # 更新缩略图、文件大小和时长
        downloaded_files = result.get("downloaded_files", [])
        for file_info in downloaded_files:
            if file_info.get("type") == "video":
                # 更新缩略图
                thumbnail_path = file_info.get("thumbnail")
                if thumbnail_path:
                    self.video_list.update_video_thumbnail(video_id, thumbnail_path)
                    print(f"📸 已更新视频 {video_id} 的缩略图")

                # 更新文件大小
                video_path = file_info.get("path")
                if video_path and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    self.video_list.update_video_file_size(video_id, file_size)
                    print(f"💾 已更新视频 {video_id} 的文件大小")

                    # 更新视频时长
                    duration_seconds = get_video_duration(video_path)
                    if duration_seconds > 0:
                        duration_str = format_duration(duration_seconds)
                        self.video_list.update_video_duration(video_id, duration_str)
                        print(f"⏱️ 已更新视频 {video_id} 的时长: {duration_str}")

        # 显示通知
        file_count = len(downloaded_files)
        QMessageBox.information(self, "下载完成",
                              f"视频下载完成！\n共下载 {file_count} 个文件")

    def on_error_occurred(self, video_id: str, error_message: str):
        """错误发生"""
        self.topbar.set_status(f"❌ 下载失败：{error_message[:50]}")
        QMessageBox.warning(self, "下载失败", f"视频下载失败：\n{error_message}")

    def open_directory(self, path: str):
        """打开目录"""
        if not os.path.exists(path):
            QMessageBox.warning(self, "提示", f"目录不存在：{path}")
            return

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录：{str(e)}")

    def closeEvent(self, event):
        """关闭事件"""
        # 检查是否有正在下载的任务
        has_downloading = any(card.video_data.get("status") == "downloading"
                            for card in self.video_list.video_cards.values())

        if has_downloading:
            reply = QMessageBox.question(self, "确认退出",
                                        "还有下载任务正在进行，确定要退出吗？",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()
