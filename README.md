# DouyinGo

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/desktop-Windows%20x64-lightgrey.svg)

**多平台视频下载工具 | Multi-Platform Video Downloader**

基于 React/Tauri 桌面界面与 Python sidecar 的多平台媒体下载工具，支持抖音、YouTube、Twitter/X、寇享（Koushare）。

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
- **🎞️ 多格式支持** - MP4、MKV、MOV 视频，MP3、M4A、WAV 音频及 JPG 封面
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
- **📚 持久任务历史** - sidecar 重启后保留已结束任务，并安全恢复中断状态
- **📁 多任务下载** - 支持多个下载任务并发执行
- **💻 现代 UI** - 简洁美观的图形界面
- **🚀 本地 sidecar** - 下载与媒体处理均在本机 Python sidecar 中完成

## 📸 旧 PyQt 界面对照

以下截图仅用于迁移前后对照；当前桌面界面位于 `src/`。

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118143806888.png)

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118143845131.png)

![](https://raw.githubusercontent.com/cacityfauh-ui/MyPic/master/pic/20251118153424125.png)



## 🛠️ 技术栈

- **桌面界面**: React 19 + Vite + Tauri 2
- **本地后端**: FastAPI + Python sidecar
- **下载引擎**: yt-dlp + 平台定制下载器
- **HTTP 请求**: requests + httpx
- **视频处理**: FFmpeg + ffprobe
- **日志系统**: loguru
- **正则解析**: Python re

## 📦 安装使用

### Windows 安装包

发布版安装包已经包含 Python sidecar、FFmpeg、ffprobe、yt-dlp、Deno 和
`yt-dlp-ejs`，终端用户不需要单独安装 Python 或媒体工具。

### 源码开发要求

- Windows 10/11 x64
- Python 3.10 或更高版本
- Node.js 20 或更高版本
- Rust stable
- FFmpeg 与 ffprobe（打包时强制检查并捆绑）

### 快速开始（源码）

1. **克隆项目**

```bash
git clone <项目地址>
cd DouyinGo
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **安装 FFmpeg 与 ffprobe**

从 [ffmpeg.org](https://ffmpeg.org/download.html) 获取同一发行版的 `ffmpeg.exe`
和 `ffprobe.exe`，并加入 `PATH`。仓库根目录的 `ffmpeg.exe` 也可被构建脚本发现。

4. **安装前端依赖**

```bash
npm install
```

5. **运行桌面开发版**

```bash
npm run package:sidecar
npm run tauri:dev
```

生成完整 NSIS 安装包：

```bash
npm run tauri:build
```

该命令会先重新打包 Python sidecar，避免把旧后端误装进新桌面版本。

旧 PyQt 入口 `python main.py` 仅保留用于迁移对照，不是新桌面版入口。需要
运行旧入口时，另行安装 `requirements-legacy.txt`。

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
- 多格式支持（MP4/MKV/MOV；音频 MP3/M4A/WAV；封面 JPG）
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
DouyinGo/
├── main.py                      # 旧 PyQt 对照入口
├── src/                         # React 桌面界面
├── src-tauri/                   # Tauri 外壳与 sidecar 生命周期
├── backend/                     # FastAPI sidecar API 与任务服务
├── scripts/build_sidecar.py     # PyInstaller sidecar 打包
├── scripts/verify_media_contract.py # 打包媒体与取消契约
├── requirements.txt             # sidecar 与构建依赖
├── requirements-legacy.txt      # 可选旧 PyQt 对照依赖
├── README.md                    # 项目说明文档
├── test_backend_api.py          # sidecar API 与生命周期测试
├── test_core_functions.py       # 核心功能测试
├── core/                        # 核心下载模块
│   ├── __init__.py
│   ├── downloader.py           # 抖音下载器
│   ├── pure_python_extractor.py # 抖音解析器
│   ├── thumbnail_extractor.py  # 缩略图处理
│   ├── youtube_downloader.py   # YouTube下载器
│   ├── twitter_downloader.py   # Twitter下载器
│   └── koushare_downloader.py  # 寇享下载器
├── ui/                         # 旧 PyQt 对照界面
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
- **桌面外壳**: React/Tauri
- **后端边界**: FastAPI Python sidecar
- **网络请求**: requests + httpx
- **视频处理**: FFmpeg
- **日志系统**: loguru

### 关键特性
1. **模块化设计**: 每个平台独立的下载模块
2. **异步下载**: sidecar 线程池实现多任务并发
3. **智能解析**: 自动识别和提取视频链接
4. **进度监控**: 实时显示下载进度和状态
5. **错误处理**: 完善的异常处理和用户提示

### 下载流程
1. **URL识别**: 正则表达式匹配平台URL
2. **信息获取**: 调用平台解析逻辑获取视频元信息
3. **参数配置**: 根据用户选择配置下载参数
4. **异步下载**: sidecar 工作线程执行下载，React 轮询任务状态
5. **结果处理**: 更新界面和文件信息

## ⚙️ 配置说明

### 下载目录

默认按平台分别保存到下载目录中：
- `douyin_downloads/`
- `youtube_downloads/`
- `twitter_downloads/`
- `koushare_downloads/`

可以在桌面版设置中修改下载路径，并选择是否保存元数据。YouTube 与 Twitter/X
可分别设置代理地址，并从 Chrome、Edge、Firefox、Brave 或 Chromium 读取
Cookies。配置写入应用数据目录的 `sidecar-config.json`；代理与 Cookies 来源只在
任务运行时传给 yt-dlp，不会写入任务历史或下载元数据。

### 文件命名规则

- 视频文件：`{视频标题}_no_watermark.mp4`
- 缩略图：`{视频标题}_thumb.jpg`
- 图片集：`{标题}_1.jpg`, `{标题}_2.jpg`, ...

## 🧪 测试

运行核心功能测试：
```bash
python test_core_functions.py
python test_backend_api.py
```

使用本地 HLS 测试源验证源代码与打包 sidecar 的 Koushare/FFmpeg 输出契约：
```bash
npm.cmd run verify:media
```

媒体契约同时验证 MKV/MP3/JPG 输出、活动 HLS 取消、AI manifest runner 和
AI runner 取消后的进程回收。

测试内容：
- URL识别功能
- URL提取功能
- 下载器初始化
- 格式选择功能

## 📝 更新日志

### v2.0.1 (当前版本)
- 🐛 修复打包版 YouTube 403，并捆绑 Deno、yt-dlp-ejs、FFmpeg 与 ffprobe
- 🎵 下载类型与格式真实生效，新增音频、封面和元数据输出
- 🤖 新增可验证的本地 AI 模型运行器清单
- ⚙️ 新增 sidecar 设置持久化与响应式桌面布局修复
- 🌐 新增 YouTube 与 Twitter/X 独立代理及浏览器 Cookies 设置
- ✅ 新增本地 HLS 媒体契约测试，覆盖打包 sidecar 的 MKV、MP3 与 JPG 输出
- 🛑 修复活动下载、FFmpeg 后处理和 AI runner 取消时的状态与进程回收
- 🔒 启用 Tauri CSP，并让桌面构建强制重建完整 sidecar 工具链

### v2.0.0
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

- [Tauri](https://tauri.app/) - 桌面应用外壳
- [React](https://react.dev/) - 桌面界面
- [requests](https://requests.readthedocs.io/) - HTTP 库
- [ffmpeg](https://ffmpeg.org/) - 视频处理工具

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>
