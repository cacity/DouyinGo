# DouyinGo

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.2-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**轻量级抖音视频下载工具 | Lightweight Douyin Video Downloader**

一款基于 PyQt5 的抖音视频下载工具，支持无水印视频和图片集下载

[功能特性](#-功能特性) • [安装使用](#-安装使用) • [使用说明](#-使用说明) • [常见问题](#-常见问题)

</div>

---

## ✨ 功能特性

- **🎬 无水印下载** - 支持下载无水印高清视频
- **📸 图片集支持** - 完整下载抖音图片集内容
- **🚀 纯 Python 实现** - 无需外部服务，开箱即用
- **💻 现代 UI** - 简洁美观的图形界面
- **📊 实时进度** - 下载进度实时显示
- **🖼️ 视频预览** - 自动生成视频缩略图
- **📁 批量下载** - 支持多个视频同时下载
- **🔄 智能解析** - 自动识别和解析抖音链接

## 📸 界面预览

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251029115741506.png)

## 🛠️ 技术栈

- **GUI 框架**: PyQt5
- **HTTP 请求**: requests
- **视频处理**: ffmpeg (可选)
- **正则解析**: Python re

## 📦 安装使用

### 环境要求

- Python 3.7 或更高版本
- Windows / macOS / Linux

### 快速开始

1. **克隆项目**

```bash
git clone https://github.com/cacity/DouyinGo.git
cd DouyinGo
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **（可选）安装 ffmpeg**

用于视频缩略图提取：

- **Windows**: 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载并添加到 PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

4. **运行程序**

```bash
python main.py
```

## 📖 使用说明

### 方法一：粘贴链接下载

1. 打开抖音 APP，找到想下载的视频
2. 点击分享 → 复制链接
3. 在 DouyinGo 中点击「粘贴链接」按钮
4. 程序自动开始下载

### 方法二：手动输入链接

1. 复制抖音视频链接（如：`https://v.douyin.com/xxxxx/`）
2. 在输入框中粘贴链接
3. 点击下载按钮

### 支持的链接格式

- `https://v.douyin.com/xxxxx/`
- `https://www.douyin.com/video/xxxxxxx`
- `https://www.iesdouyin.com/share/video/xxxxxxx`
- `https://dy.tt/xxxxx`

## 📁 项目结构

```
douyin_app/
├── main.py                      # 程序入口
├── requirements.txt             # 依赖列表
├── ui/                          # UI 组件
│   ├── main_window.py          # 主窗口
│   ├── sidebar.py              # 侧边栏
│   ├── topbar.py               # 顶部栏
│   ├── video_list.py           # 视频列表
│   └── styles.py               # 样式定义
├── core/                        # 核心功能
│   ├── downloader.py           # 下载管理器
│   ├── pure_python_extractor.py # 视频解析器
│   └── thumbnail_extractor.py  # 缩略图提取
└── resources/                   # 资源文件
    └── icons/                  # 图标资源
```

## ⚙️ 配置说明

### 下载目录

默认下载目录：`douyin_downloads/`

可以在设置中修改下载路径。

### 文件命名规则

- 视频文件：`{视频标题}_no_watermark.mp4`
- 缩略图：`{视频标题}_thumb.jpg`
- 图片集：`{标题}_1.jpg`, `{标题}_2.jpg`, ...

## 📝 更新日志

### v1.0.2 (当前版本)
- ✨ 优化下载进度显示
- 🐛 修复文件命名问题
- 📝 完善文档说明

### v1.0.1
- ✨ 添加图片集下载支持
- 🎨 优化 UI 界面
- 🐛 修复已知 bug

### v1.0.0
- 🎉 首次发布
- ✨ 基础下载功能
- 💻 PyQt5 GUI 界面

## ⚠️ 免责声明

本工具仅供学习交流使用，请勿用于商业用途。

- 下载的内容版权归原作者所有
- 请尊重原创，合理使用下载内容
- 使用本工具产生的一切后果由使用者自行承担

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [requests](https://requests.readthedocs.io/) - HTTP 库
- [ffmpeg](https://ffmpeg.org/) - 视频处理工具

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>
