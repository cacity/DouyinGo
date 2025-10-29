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
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from ui.sidebar import Sidebar
from ui.topbar import TopBar
from ui.video_list import VideoList
from ui.styles import MAIN_WINDOW_STYLE
from core.downloader import DownloadManager
from core.thumbnail_extractor import get_video_duration, format_duration


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.download_manager = DownloadManager()
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("DouyinGo - 抖音视频下载工具")
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

    def on_paste_clicked(self):
        """粘贴按钮点击"""
        # 获取剪贴板内容
        clipboard_text = self.topbar.get_clipboard_text()

        if not clipboard_text:
            QMessageBox.warning(self, "提示", "剪贴板为空，请先复制抖音视频链接")
            return

        # 从文本中提取 URL
        url = self.extract_douyin_url(clipboard_text)

        # 验证是否为抖音链接
        if not self.is_douyin_url(url):
            QMessageBox.warning(self, "提示",
                              f"未找到有效的抖音链接\n\n支持的格式：\n- https://v.douyin.com/xxxxx/\n- https://www.douyin.com/video/xxxxx\n\n剪贴板内容：\n{clipboard_text[:100]}...")
            return

        # 添加下载任务
        try:
            self.topbar.set_status("正在解析链接...")
            self.download_manager.add_download(url)
            self.topbar.set_status(f"已添加下载任务 (共 {self.video_list.get_video_count()} 个)")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加下载任务失败：{str(e)}")
            self.topbar.set_status("")

    def is_douyin_url(self, url: str) -> bool:
        """验证是否为抖音链接"""
        return "douyin.com" in url or "dy.tt" in url

    def on_download_type_changed(self, download_type: str):
        """下载类型改变"""
        print(f"下载类型改变: {download_type}")
        # TODO: 实现下载类型切换逻辑

    def on_quality_changed(self, quality: str):
        """质量改变"""
        print(f"质量改变: {quality}")
        # TODO: 实现质量切换逻辑

    def on_format_changed(self, format_type: str):
        """格式改变"""
        print(f"格式改变: {format_type}")
        # TODO: 实现格式切换逻辑

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
        """下载完成"""
        # 更新状态栏
        success_count = sum(1 for card in self.video_list.video_cards.values()
                          if card.video_data.get("status") == "success")
        self.topbar.set_status(f"已完成 {success_count} 个下载")

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
