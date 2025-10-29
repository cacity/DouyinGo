#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DouyinGo - 抖音视频下载工具
主入口文件
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from ui.main_window import MainWindow


def setup_app():
    """设置应用程序"""
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("DouyinGo")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DouyinGo")

    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "icons8-youtube-100.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 设置字体
    font = QFont()
    font.setFamily("Microsoft YaHei UI, Segoe UI, Arial, sans-serif")
    font.setPointSize(10)
    app.setFont(font)

    return app


def main():
    """主函数"""
    print("=" * 60)
    print("DouyinGo - 抖音视频下载工具 v1.0.2")
    print("=" * 60)
    print()
    print("✨ 使用纯 Python 实现，无需额外服务")
    print("🎬 支持无水印视频下载")
    print("📸 支持图片集下载")
    print()

    # 创建应用
    app = setup_app()

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
