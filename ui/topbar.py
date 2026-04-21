#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
顶部操作栏组件
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QComboBox,
                            QLabel, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.styles import TOPBAR_STYLE


class TopBar(QWidget):
    """顶部操作栏组件"""

    # 定义信号
    paste_clicked = pyqtSignal()
    download_type_changed = pyqtSignal(str)
    quality_changed = pyqtSignal(str)
    format_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setFixedHeight(70)
        self.setStyleSheet(TOPBAR_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # 平台显示标签
        self.platform_label = QLabel("🎵 抖音")
        self.platform_label.setObjectName("platformLabel")
        layout.addWidget(self.platform_label)

        # 粘贴链接按钮
        self.paste_btn = QPushButton("🔗 粘贴链接")
        self.paste_btn.setObjectName("pasteButton")
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        self.paste_btn.clicked.connect(self.on_paste_clicked)
        layout.addWidget(self.paste_btn)

        # 分隔符
        layout.addSpacing(10)

        # 下载类型选择
        type_label = QLabel("下载")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["视频", "音频", "封面"])
        self.type_combo.setCurrentText("视频")
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)

        # 质量选择
        quality_label = QLabel("质量")
        layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["原画", "2K(1440p)", "超清(1080p)", "高清(720p)", "标清(480p)"])
        self.quality_combo.setCurrentText("原画")
        self.quality_combo.currentTextChanged.connect(self.on_quality_changed)
        layout.addWidget(self.quality_combo)

        # 格式选择
        format_label = QLabel("格式")
        layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "MOV"])
        self.format_combo.setCurrentText("MP4")
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        layout.addWidget(self.format_combo)

        # 添加弹性空间
        layout.addStretch()

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6C757D; font-size: 13px; min-width: 200px;")
        layout.addWidget(self.status_label)

    def on_paste_clicked(self):
        """粘贴按钮点击事件"""
        self.paste_clicked.emit()

    def on_type_changed(self, text):
        """下载类型改变事件"""
        self.download_type_changed.emit(text)

    def on_quality_changed(self, text):
        """质量改变事件"""
        self.quality_changed.emit(text)

    def on_format_changed(self, text):
        """格式改变事件"""
        self.format_changed.emit(text)

    def set_status(self, text: str):
        """设置状态文本"""
        self.status_label.setText(text)

    def set_platform(self, platform: str):
        """设置当前平台"""
        platform_map = {
            "douyin": "🎵 抖音",
            "youtube": "📺 YouTube",
            "twitter": "🐦 Twitter/X",
            "koushare": "📚 寇享"
        }
        platform_text = platform_map.get(platform, "🎵 抖音")
        self.platform_label.setText(platform_text)

    def get_clipboard_text(self) -> str:
        """获取剪贴板文本"""
        clipboard = QApplication.clipboard()
        return clipboard.text().strip()

    def update_quality_options(self, platform: str):
        """根据平台更新质量选项"""
        self.quality_combo.clear()

        if platform == "youtube":
            self.quality_combo.addItems([
                "最佳质量", "4K", "1440p", "1080p", "720p", "480p", "360p"
            ])
        elif platform == "twitter":
            self.quality_combo.addItems([
                "最佳质量", "1080p", "720p", "480p", "360p"
            ])
        elif platform == "koushare":
            self.quality_combo.addItems([
                "最佳质量", "1080p", "720p", "480p"
            ])
        else:  # douyin
            self.quality_combo.addItems([
                "原画", "超清(1080p)", "高清(720p)", "标清(480p)"
            ])

        # 设置默认选项
        self.quality_combo.setCurrentIndex(0)

