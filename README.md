# VideoGo

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

**多平台视频下载工具 | Multi-Platform Video Downloader**

基于 PyQt5 的多平台视频下载工具，支持抖音、YouTube、Twitter/X、寇享（Koushare）视频下载

[功能特性](#-功能特性) • [安装使用](#-安装使用) • [使用说明](#-使用说明) • [项目结构](#-项目结构)

</div>

---

## ✨ 功能特性

### 🎵 抖音下载
- **🎬 无水印下载** - 支持下载无水印高清视频
- **📸 图片集支持** - 完整下载抖音图片集内容
- **🔄 智能解析** - 自动识别和解析抖音链接

### 📺 YouTube下载
- **🎬 高质量下载** - 支持4K、1080p等多种画质
- **🎞️ 多格式支持** - MP4、AVI、MKV、MOV等格式
- **🎞️ Shorts支持** - 支持YouTube Shorts短视频
- **📊 详细信息** - 自动获取标题、时长、缩略图

### 🐦 Twitter/X下载
- **🐦 原画质保持** - 保持Twitter视频原始质量
- **🔗 链接识别** - 自动识别推文中的视频链接
- **⚡ 快速下载** - 优化的下载体验

### 📚 寇享下载
- **📺 回放与视频页支持** - 支持直播回放页和视频详情页下载
- **🎞️ HLS 下载** - 通过 ffmpeg 下载并合并 m3u8 视频流
- **🔽 画质回退** - 优先请求高画质，不可用时自动回退

### 🎨 界面特性
- **🎯 平台切换** - 直观的平台选择界面
- **📊 实时进度** - 下载进度实时显示
- **🖼️ 视频预览** - 自动生成视频缩略图
- **📁 批量下载** - 支持多个视频同时下载
- **💻 现代 UI** - 简洁美观的图形界面
- **🚀 纯 Python 实现** - 无需外部服务，开箱即用

## 📸 界面预览

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118143806888.png)

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118143845131.png)

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118153424125.png)



## 🛠️ 技术栈

- **GUI 框架**: PyQt5
- **下载引擎**: yt-dlp + 平台定制下载器
- **HTTP 请求**: requests + httpx
- **视频处理**: ffmpeg (用于缩略图提取)
- **日志系统**: loguru
- **正则解析**: Python re

## 📦 安装使用

### 环境要求

- Python 3.7 或更高版本
- Windows / macOS / Linux
- FFmpeg (用于视频处理)

### 快速开始

1. **克隆项目**

```bash
git clone <项目地址>
cd douyin_app
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **安装 FFmpeg**

用于视频缩略图提取和视频处理：

- **Windows**: 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载并添加到 PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt-get install ffmpeg`

4. **运行程序**

```bash
python main.py
```

## 📖 使用说明

### 基本使用流程

1. **选择平台** - 在左侧边栏选择要下载的平台（抖音/YouTube/Twitter/寇享）
2. **复制链接** - 复制对应平台的视频链接
3. **粘贴下载** - 点击「粘贴链接」按钮，程序自动识别并下载
4. **查看进度** - 实时查看下载进度和状态
5. **打开文件** - 下载完成后可直接打开所在文件夹

### 支持的链接格式

#### 抖音
- `https://v.douyin.com/xxxxx/`
- `https://www.douyin.com/video/xxxxxxx`
- `https://www.iesdouyin.com/share/video/xxxxxxx`
- `https://dy.tt/xxxxx`

#### YouTube
- `https://www.youtube.com/watch?v=xxxxx`
- `https://youtu.be/xxxxx`
- `https://www.youtube.com/shorts/xxxxx`
- `https://www.youtube.com/embed/xxxxx`

#### Twitter/X
- `https://twitter.com/[用户名]/status/[推文ID]`
- `https://x.com/[用户名]/status/[推文ID]`
- `https://www.twitter.com/i/web/status/[推文ID]`
- `https://www.x.com/i/web/status/[推文ID]`

#### 寇享 / Koushare
- `https://www.koushare.com/live/details/[liveId]?vid=[videoId]`
- `https://www.koushare.com/live/details/[liveId]?videoId=[videoId]`
- `https://www.koushare.com/video/details/[videoId]`
- `https://www.koushare.com/video/videodetail/[videoId]`

### 平台特色功能

#### 抖音平台
- 无水印高清视频下载
- 完整图片集下载
- 自动解析分享文本

#### YouTube平台
- 多画质选择（4K/1080p/720p等）
- 多格式支持（MP4/AVI/MKV/MOV）
- 自动获取视频信息和缩略图
- 支持YouTube Shorts

#### Twitter/X平台
- 保持原始视频质量
- 快速下载体验
- 自动识别推文视频

#### 寇享平台
- 支持直播回放链接与视频详情页链接
- 通过 Koushare 接口获取播放地址
- 使用 ffmpeg 下载 HLS 视频流
- 高画质不可用时自动回退

## 📁 项目结构

```
douyin_app/
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖包列表
├── README.md                   # 项目说明文档
├── test_core_functions.py      # 核心功能测试
├── core/                       # 核心下载模块
│   ├── __init__.py
│   ├── downloader.py           # 抖音下载器
│   ├── pure_python_extractor.py # 抖音解析器
│   ├── thumbnail_extractor.py  # 缩略图处理
│   ├── youtube_downloader.py   # YouTube下载器
│   ├── twitter_downloader.py   # Twitter下载器
│   └── koushare_downloader.py  # 寇享下载器
├── ui/                         # 用户界面模块
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── sidebar.py              # 侧边栏
│   ├── topbar.py               # 顶部工具栏
│   ├── video_list.py           # 视频列表
│   └── styles.py               # 界面样式
├── resources/                  # 资源文件
│   └── icons/                  # 图标文件
│       └── icons8-youtube-100.png
├── douyin_downloads/           # 抖音下载目录
├── youtube_downloads/          # YouTube下载目录
├── twitter_downloads/          # Twitter下载目录
└── koushare_downloads/         # 寇享下载目录
```

## 🔧 技术实现

### 核心架构
- **下载引擎**: yt-dlp + 平台定制下载器
- **GUI框架**: PyQt5 (跨平台桌面应用)
- **网络请求**: requests + httpx
- **视频处理**: FFmpeg
- **日志系统**: loguru

### 关键特性
1. **模块化设计**: 每个平台独立的下载模块
2. **异步下载**: QThread实现多任务并发
3. **智能解析**: 自动识别和提取视频链接
4. **进度监控**: 实时显示下载进度和状态
5. **错误处理**: 完善的异常处理和用户提示

### 下载流程
1. **URL识别**: 正则表达式匹配平台URL
2. **信息获取**: 调用平台解析逻辑获取视频元信息
3. **参数配置**: 根据用户选择配置下载参数
4. **异步下载**: QThread工作线程执行下载
5. **结果处理**: 更新界面和文件信息

## ⚙️ 配置说明

### 下载目录

默认按平台分别保存到下载目录中：
- `douyin_downloads/`
- `youtube_downloads/`
- `twitter_downloads/`
- `koushare_downloads/`

可以在设置中修改下载路径。

### 文件命名规则

- 视频文件：`{视频标题}_no_watermark.mp4`
- 缩略图：`{视频标题}_thumb.jpg`
- 图片集：`{标题}_1.jpg`, `{标题}_2.jpg`, ...

## 🧪 测试

运行核心功能测试：
```bash
python test_core_functions.py
```

测试内容：
- URL识别功能
- URL提取功能
- 下载器初始化
- 格式选择功能

## 📝 更新日志

### v2.0.0 (当前版本)
- ✨ 新增YouTube视频下载支持
- ✨ 新增Twitter/X视频下载支持
- ✨ 新增寇享（Koushare）视频下载支持
- 🎞️ 支持寇享直播回放页与视频详情页链接
- 🔽 支持寇享 HLS 下载与画质自动回退
- 🎨 全新界面设计，支持平台切换
- 🔧 重构下载器架构，支持平台定制下载器
- 📱 优化用户体验和界面交互
- 🚀 升级依赖包，支持最新功能

### v1.0.2
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

## ⚠️ 注意事项

> 本项目仅供合法用途使用。
> 在使用下载、解析、平台链接处理等功能前，请先阅读 [DISCLAIMER.md](./DISCLAIMER.md)。

1. **网络环境**: 某些地区可能需要代理才能访问YouTube/Twitter
2. **版权声明**: 请尊重视频内容版权，仅在有合法权限的前提下下载和使用内容
3. **存储空间**: 确保有足够的磁盘空间存储下载的视频
4. **法律合规**: 使用本工具请遵守当地法律法规及平台服务条款

## 🔮 未来计划

- [ ] 支持更多视频平台（Bilibili、Instagram等）
- [ ] 添加视频格式转换功能
- [ ] 实现批量下载和播放列表支持
- [ ] 集成字幕下载功能
- [ ] 添加下载历史管理
- [ ] 支持代理设置
- [ ] 开发命令行版本

## ⚠️ 免责声明

详细使用与免责说明请见 [DISCLAIMER.md](./DISCLAIMER.md)。

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
