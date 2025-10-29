#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频列表组件
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                            QFrame, QLabel, QPushButton, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap
from ui.styles import VIDEO_LIST_STYLE, EMPTY_STATE_STYLE
from typing import Dict, Any, List


class VideoCard(QFrame):
    """视频卡片组件"""

    # 定义信号
    download_clicked = pyqtSignal(str)  # 下载按钮点击
    open_folder_clicked = pyqtSignal(str)  # 打开文件夹
    refresh_clicked = pyqtSignal(str)  # 刷新
    delete_clicked = pyqtSignal(str)  # 删除

    def __init__(self, video_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.video_id = video_data.get("id", "")
        self.setObjectName("videoCard")
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # 进一步减小内边距：10→8
        layout.setSpacing(10)  # 减小间距：12→10
        layout.setAlignment(Qt.AlignTop)  # 设置整体顶部对齐

        # 左侧：缩略图（减小尺寸）
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(QSize(120, 68))  # 从160x90减小到120x68（保持16:9比例）
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setText("🎬")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("border-radius: 6px; background-color: #E0E0E0; font-size: 28px;")

        # 添加缩略图，固定宽度，顶部对齐
        layout.addWidget(self.thumbnail_label, 0, Qt.AlignTop)  # 拉伸因子为0，顶部对齐

        # 中间：视频信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)  # 进一步减小间距：6→4

        # 标题
        title_label = QLabel(self.video_data.get("title", "未知标题"))
        title_label.setObjectName("videoTitle")
        title_label.setWordWrap(True)
        title_label.setMaximumWidth(600)
        info_layout.addWidget(title_label)

        # 视频信息行
        info_row = QHBoxLayout()
        info_row.setSpacing(10)  # 减小间距：15→10

        # 格式
        format_icon = QLabel("📄")
        format_label = QLabel(self.video_data.get("format", "MP4"))
        format_label.setObjectName("videoInfo")
        info_row.addWidget(format_icon)
        info_row.addWidget(format_label)

        # 大小
        size_icon = QLabel("💾")
        self.size_label = QLabel(self.video_data.get("size", "未知"))
        self.size_label.setObjectName("videoInfo")
        info_row.addWidget(size_icon)
        info_row.addWidget(self.size_label)

        # 分辨率
        resolution_icon = QLabel("📺")
        resolution_label = QLabel(self.video_data.get("resolution", "未知"))
        resolution_label.setObjectName("videoInfo")
        info_row.addWidget(resolution_icon)
        info_row.addWidget(resolution_label)

        # 时长
        duration_icon = QLabel("⏱️")
        self.duration_label = QLabel(self.video_data.get("duration", "未知"))
        self.duration_label.setObjectName("videoInfo")
        info_row.addWidget(duration_icon)
        info_row.addWidget(self.duration_label)

        info_row.addStretch()

        info_layout.addLayout(info_row)

        # 状态和进度条放在同一行
        status_progress_layout = QHBoxLayout()
        status_progress_layout.setSpacing(10)

        # 状态标签
        self.status_label = QLabel()
        self.status_label.setMinimumWidth(80)  # 设置最小宽度，确保状态文字不被挤压
        status_progress_layout.addWidget(self.status_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self.video_data.get("progress", 0))
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumWidth(300)  # 设置最小宽度，确保进度条足够长
        self.progress_bar.setVisible(self.video_data.get("status") == "downloading")
        status_progress_layout.addWidget(self.progress_bar)

        status_progress_layout.addStretch()

        info_layout.addLayout(status_progress_layout)

        # 更新状态（在进度条创建之后）
        self.update_status(self.video_data.get("status", "pending"))

        # 移除 addStretch() - 这是导致卡片高度过大的主要原因

        # 添加信息布局到主布局，设置拉伸因子
        layout.addLayout(info_layout, 1)  # 拉伸因子为1，占据剩余空间

        # 右侧：操作按钮
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(4)  # 进一步减小间距：6→4

        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.setFixedSize(QSize(28, 28))  # 减小按钮尺寸
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(lambda: self.refresh_clicked.emit(self.video_id))
        actions_layout.addWidget(refresh_btn)

        # 打开文件夹按钮
        folder_btn = QPushButton("📁")
        folder_btn.setObjectName("actionButton")
        folder_btn.setFixedSize(QSize(28, 28))  # 减小按钮尺寸
        folder_btn.setCursor(Qt.PointingHandCursor)
        folder_btn.clicked.connect(lambda: self.open_folder_clicked.emit(self.video_id))
        actions_layout.addWidget(folder_btn)

        # 删除按钮
        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("actionButton")
        delete_btn.setFixedSize(QSize(28, 28))  # 减小按钮尺寸
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setToolTip("删除任务")
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.video_id))
        actions_layout.addWidget(delete_btn)

        # 更多选项按钮
        more_btn = QPushButton("⋮")
        more_btn.setObjectName("actionButton")
        more_btn.setFixedSize(QSize(28, 28))  # 减小按钮尺寸
        more_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(more_btn)

        # 移除 addStretch() - 避免按钮区域占据过多垂直空间

        # 添加操作按钮布局，固定宽度，顶部对齐
        layout.addLayout(actions_layout, 0)  # 拉伸因子为0，固定宽度

    def update_status(self, status: str):
        """
        更新状态
        :param status: pending, downloading, success, error
        """
        status_map = {
            "pending": ("⏳ 等待中", "statusPending"),
            "downloading": ("⬇️ 下载中", "statusDownloading"),
            "success": ("✅ 已完成", "statusSuccess"),
            "error": ("❌ 失败", "statusError")
        }

        text, style_class = status_map.get(status, ("❓ 未知", "statusPending"))
        self.status_label.setText(text)
        self.status_label.setObjectName(style_class)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        # 显示或隐藏进度条（检查是否存在）
        if hasattr(self, 'progress_bar'):
            if status == "downloading":
                self.progress_bar.setVisible(True)
            else:
                self.progress_bar.setVisible(False)

    def update_progress(self, progress: int):
        """更新进度"""
        self.progress_bar.setValue(progress)

    def update_thumbnail(self, thumbnail_path: str):
        """更新缩略图"""
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    self.thumbnail_label.setPixmap(pixmap)
                    print(f"✅ 缩略图已更新: {thumbnail_path}")
            except Exception as e:
                print(f"⚠️ 加载缩略图失败: {e}")

    def update_file_size(self, size_bytes: int):
        """更新文件大小"""
        if size_bytes > 0:
            # 格式化文件大小
            size_str = self._format_size(size_bytes)
            self.size_label.setText(size_str)
            print(f"✅ 文件大小已更新: {size_str}")

    def update_duration(self, duration_str: str):
        """更新视频时长"""
        if duration_str:
            self.duration_label.setText(duration_str)
            print(f"✅ 视频时长已更新: {duration_str}")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "未知"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} TB"


class EmptyState(QWidget):
    """空状态组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("emptyState")
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setStyleSheet(EMPTY_STATE_STYLE)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 图标
        icon_label = QLabel("📋")
        icon_label.setObjectName("emptyIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # 文本
        text_label = QLabel("暂无视频任务")
        text_label.setObjectName("emptyText")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        # 提示
        hint_label = QLabel("点击上方「粘贴链接」按钮添加下载任务")
        hint_label.setObjectName("emptyText")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(hint_label)


class VideoList(QWidget):
    """视频列表组件"""

    # 定义信号
    download_clicked = pyqtSignal(str)
    open_folder_clicked = pyqtSignal(str)
    refresh_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)  # 删除

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_cards: Dict[str, VideoCard] = {}
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(VIDEO_LIST_STYLE)

        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setObjectName("contentWidget")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 10, 0, 10)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignTop)

        # 空状态
        self.empty_state = EmptyState()
        self.content_layout.addWidget(self.empty_state)

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)

    def add_video(self, video_data: Dict[str, Any]):
        """添加视频"""
        # 隐藏空状态
        self.empty_state.setVisible(False)

        # 创建视频卡片
        video_card = VideoCard(video_data)
        video_card.download_clicked.connect(self.download_clicked)
        video_card.open_folder_clicked.connect(self.open_folder_clicked)
        video_card.refresh_clicked.connect(self.refresh_clicked)
        video_card.delete_clicked.connect(self.delete_clicked)

        # 添加到布局
        self.content_layout.addWidget(video_card)

        # 保存引用
        video_id = video_data.get("id", "")
        self.video_cards[video_id] = video_card

    def update_video_status(self, video_id: str, status: str):
        """更新视频状态"""
        if video_id in self.video_cards:
            self.video_cards[video_id].update_status(status)

    def update_video_progress(self, video_id: str, progress: int):
        """更新视频进度"""
        if video_id in self.video_cards:
            self.video_cards[video_id].update_progress(progress)

    def update_video_thumbnail(self, video_id: str, thumbnail_path: str):
        """更新视频缩略图"""
        if video_id in self.video_cards:
            self.video_cards[video_id].update_thumbnail(thumbnail_path)

    def update_video_file_size(self, video_id: str, size_bytes: int):
        """更新视频文件大小"""
        if video_id in self.video_cards:
            self.video_cards[video_id].update_file_size(size_bytes)

    def update_video_duration(self, video_id: str, duration_str: str):
        """更新视频时长"""
        if video_id in self.video_cards:
            self.video_cards[video_id].update_duration(duration_str)

    def remove_video(self, video_id: str):
        """删除视频卡片"""
        if video_id in self.video_cards:
            video_card = self.video_cards[video_id]
            # 从布局中移除
            self.content_layout.removeWidget(video_card)
            # 删除控件
            video_card.deleteLater()
            # 从字典中删除
            del self.video_cards[video_id]
            print(f"✅ 已删除视频卡片: {video_id}")

            # 如果没有视频了，显示空状态
            if len(self.video_cards) == 0:
                self.empty_state.setVisible(True)

    def clear_videos(self):
        """清空视频列表"""
        # 移除所有视频卡片
        for video_card in self.video_cards.values():
            self.content_layout.removeWidget(video_card)
            video_card.deleteLater()

        self.video_cards.clear()

        # 显示空状态
        self.empty_state.setVisible(True)

    def get_video_count(self) -> int:
        """获取视频数量"""
        return len(self.video_cards)
