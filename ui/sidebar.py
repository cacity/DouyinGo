#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
侧边栏组件
"""

import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from ui.styles import SIDEBAR_STYLE


class Sidebar(QWidget):
    """侧边栏组件"""

    # 定义信号
    page_changed = pyqtSignal(str)  # 页面切换信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.current_page = "download"
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setFixedWidth(160)
        self.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 应用标题
        title_label = QLabel("DouyinGo")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 分隔线
        layout.addSpacing(10)

        # 导航按钮
        self.download_btn = self.create_nav_button("📥\n链接下载", "download")
        self.download_btn.setProperty("active", "true")
        layout.addWidget(self.download_btn)

        # 暂时禁用其他功能
        # self.browser_btn = self.create_nav_button("🌐\n浏览器嗅探", "browser")
        # layout.addWidget(self.browser_btn)

        # self.convert_btn = self.create_nav_button("🔄\n格式转换", "convert")
        # layout.addWidget(self.convert_btn)

        # self.merge_btn = self.create_nav_button("🎬\n音视频合并", "merge")
        # layout.addWidget(self.merge_btn)

        # 添加弹性空间
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 设置按钮
        settings_btn = self.create_nav_button("⚙️\n设置", "settings")
        layout.addWidget(settings_btn)

        # 底部版本信息
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #999; font-size: 11px; padding: 10px;")
        layout.addWidget(version_label)

    def create_nav_button(self, text: str, page_id: str) -> QPushButton:
        """
        创建导航按钮
        :param text: 按钮文本
        :param page_id: 页面ID
        """
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setProperty("page_id", page_id)
        btn.clicked.connect(lambda: self.on_button_clicked(page_id))
        return btn

    def on_button_clicked(self, page_id: str):
        """处理按钮点击事件"""
        if page_id == self.current_page:
            return

        # 更新按钮状态
        self.current_page = page_id
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget_page_id = widget.property("page_id")
                if widget_page_id:
                    widget.setProperty("active", "true" if widget_page_id == page_id else "false")
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)

        # 发送信号
        self.page_changed.emit(page_id)
