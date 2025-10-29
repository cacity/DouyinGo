#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI 样式定义 - 现代化风格
"""

# 主题色
PRIMARY_COLOR = "#4A9EFF"
SECONDARY_COLOR = "#6C757D"
BACKGROUND_COLOR = "#F5F7FA"
SIDEBAR_COLOR = "#E8EEF5"
WHITE_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"
TEXT_SECONDARY = "#6C757D"
BORDER_COLOR = "#E0E0E0"
HOVER_COLOR = "#F0F4FF"
SUCCESS_COLOR = "#28A745"
ERROR_COLOR = "#DC3545"

# 主窗口样式
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #F5F7FA;
}
"""

# 侧边栏样式
SIDEBAR_STYLE = f"""
QWidget#sidebar {{
    background-color: {SIDEBAR_COLOR};
    border-right: 1px solid {BORDER_COLOR};
}}

QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 15px 10px;
    text-align: center;
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: 500;
    margin: 5px 10px;
}}

QPushButton:hover {{
    background-color: {HOVER_COLOR};
}}

QPushButton:pressed {{
    background-color: {PRIMARY_COLOR};
    color: white;
}}

QPushButton[active="true"] {{
    background-color: {PRIMARY_COLOR};
    color: white;
}}

QLabel#appTitle {{
    color: {PRIMARY_COLOR};
    font-size: 16px;
    font-weight: bold;
    padding: 20px;
}}
"""

# 顶部工具栏样式
TOPBAR_STYLE = f"""
QWidget#topbar {{
    background-color: {WHITE_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 15px 20px;
}}

QPushButton#pasteButton {{
    background-color: {PRIMARY_COLOR};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
}}

QPushButton#pasteButton:hover {{
    background-color: #3D8DE6;
}}

QPushButton#pasteButton:pressed {{
    background-color: #2C7ACC;
}}

QComboBox {{
    background-color: white;
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 15px;
    font-size: 14px;
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {PRIMARY_COLOR};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 10px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {TEXT_COLOR};
    margin-right: 5px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    selection-background-color: {HOVER_COLOR};
    selection-color: {TEXT_COLOR};
    padding: 5px;
}}

QLabel {{
    color: {TEXT_COLOR};
    font-size: 14px;
}}
"""

# 视频列表样式
VIDEO_LIST_STYLE = f"""
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QWidget#contentWidget {{
    background-color: transparent;
}}

QFrame#videoCard {{
    background-color: {WHITE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    margin: 3px 12px;
    padding: 0px;
}}

QFrame#videoCard:hover {{
    border-color: {PRIMARY_COLOR};
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

QLabel#videoTitle {{
    color: {TEXT_COLOR};
    font-size: 14px;
    font-weight: 600;
    line-height: 1.3;
}}

QLabel#videoInfo {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
}}

QLabel#statusLabel {{
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 3px;
}}

QLabel#statusPending {{
    background-color: #FFF3CD;
    color: #856404;
}}

QLabel#statusDownloading {{
    background-color: #D1ECF1;
    color: #0C5460;
}}

QLabel#statusSuccess {{
    background-color: #D4EDDA;
    color: #155724;
}}

QLabel#statusError {{
    background-color: #F8D7DA;
    color: #721C24;
}}

QPushButton#actionButton {{
    background-color: transparent;
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 15px;
    color: {TEXT_COLOR};
    font-size: 13px;
}}

QPushButton#actionButton:hover {{
    background-color: {HOVER_COLOR};
    border-color: {PRIMARY_COLOR};
}}

QProgressBar {{
    border: none;
    border-radius: 3px;
    background-color: {BACKGROUND_COLOR};
    text-align: center;
    height: 6px;
    font-size: 10px;
}}

QProgressBar::chunk {{
    background-color: {PRIMARY_COLOR};
    border-radius: 4px;
}}
"""

# 空状态样式
EMPTY_STATE_STYLE = f"""
QWidget#emptyState {{
    background-color: transparent;
}}

QLabel#emptyIcon {{
    color: {TEXT_SECONDARY};
    font-size: 48px;
}}

QLabel#emptyText {{
    color: {TEXT_SECONDARY};
    font-size: 16px;
}}
"""

# 对话框样式
DIALOG_STYLE = f"""
QDialog {{
    background-color: {WHITE_COLOR};
}}

QLabel {{
    color: {TEXT_COLOR};
    font-size: 14px;
}}

QLineEdit {{
    background-color: white;
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 10px 15px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {PRIMARY_COLOR};
}}

QPushButton {{
    background-color: {PRIMARY_COLOR};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: #3D8DE6;
}}

QPushButton#cancelButton {{
    background-color: transparent;
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
}}

QPushButton#cancelButton:hover {{
    background-color: {BACKGROUND_COLOR};
}}
"""
