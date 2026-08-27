# DouyinGo

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.2-blue.svg)
![Desktop](https://img.shields.io/badge/desktop-Tauri%202-blue.svg)
![Frontend](https://img.shields.io/badge/frontend-React%2019-61dafb.svg)
![Sidecar](https://img.shields.io/badge/sidecar-Python%203.10+-green.svg)
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
- **🤖 本地 AI 扩展** - 通过受控 runner manifest 对下载结果执行本地后处理

## 🛠️ 技术栈

- **桌面界面**: React 19 + Vite + Tauri 2
- **本地后端**: FastAPI + Python sidecar
- **任务存储**: SQLite
- **下载引擎**: yt-dlp + 平台定制下载器
- **HTTP 请求**: requests + httpx
- **视频处理**: FFmpeg + ffprobe
- **日志系统**: loguru
- **正则解析**: Python re

## 📦 安装使用

### Windows 安装包

运行 `DouyinGo_2.0.2_x64-setup.exe` 完成安装。发布版已经包含 Python
sidecar、FFmpeg、ffprobe、yt-dlp、Deno 和 `yt-dlp-ejs`，终端用户不需要
单独安装 Python、Node.js、Rust 或媒体工具。

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

2. **安装 Python sidecar 与构建依赖**

```powershell
python -m pip install -r requirements.txt
```

3. **安装 FFmpeg 与 ffprobe**

从 [ffmpeg.org](https://ffmpeg.org/download.html) 获取同一发行版的 `ffmpeg.exe`
和 `ffprobe.exe`，并加入 `PATH`。仓库根目录的 `ffmpeg.exe` 也可被构建脚本发现。

4. **安装前端依赖**

```powershell
npm.cmd install
```

5. **运行桌面开发版**

```powershell
npm.cmd run package:sidecar
npm.cmd run tauri:dev
```

生成完整 NSIS 安装包：

```powershell
npm.cmd run tauri:build
```

该命令会先重新打包 Python sidecar，避免把旧后端误装进新桌面版本。

## 📖 使用说明

### 基本使用流程

1. **选择平台** - 在左侧边栏选择要下载的平台（抖音/YouTube/Twitter/寇享）
2. **粘贴内容** - 输入视频链接或平台分享文本
3. **设置参数** - 选择视频、音频或封面，以及画质、格式和 AI 后处理
4. **开始下载** - 点击「开始下载」，sidecar 解析并执行任务
5. **查看进度** - 实时查看下载进度和状态
6. **打开文件** - 下载完成后可直接打开所在文件夹

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
├── src/                         # React 19 桌面界面
│   ├── App.tsx                  # 主工作区与设置界面
│   ├── api.ts                   # sidecar API 客户端
│   └── styles.css               # 响应式桌面样式
├── src-tauri/                   # Tauri 2 外壳
│   ├── src/                     # sidecar 生命周期与原生命令
│   ├── capabilities/            # Tauri 权限配置
│   └── tauri.conf.json          # 桌面与安装包配置
├── backend/                     # FastAPI sidecar、任务与 SQLite 存储
├── core/                        # 平台下载器与媒体处理实现
├── scripts/
│   ├── build_sidecar.py         # PyInstaller sidecar 打包
│   └── verify_media_contract.py # 源码/打包媒体契约验证
├── docs/                        # 架构、迁移与验证记录
├── resources/                   # 应用图标等资源
├── requirements.txt             # Python sidecar 与构建依赖
├── package.json                 # React/Tauri 命令与前端依赖
├── test_backend_api.py          # sidecar API 与生命周期测试
└── test_core_functions.py       # 核心下载功能测试
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

安装版默认按平台保存到 `%USERPROFILE%\Downloads\DouyinGo\<platform>_downloads`。
如果该目录不可写，sidecar 会依次回退到应用数据目录和系统临时目录；不会把
用户文件写入 PyInstaller 的临时解包目录。

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

### v2.0.2 (当前版本)
- 🐛 修复 yt-dlp 在速度或剩余时间为空时导致任务在合并阶段失败
- ✅ 新增 YouTube 与 Twitter/X 空进度字段回归测试

### v2.0.1
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
- 💻 早期 Python 桌面界面

## ⚠️ 注意事项

> 本项目仅供合法用途使用。
> 在使用下载、解析、平台链接处理等功能前，请先阅读 [DISCLAIMER.md](./DISCLAIMER.md)。

1. **网络环境**: 某些地区可能需要代理才能访问YouTube/Twitter
2. **版权声明**: 请尊重视频内容版权，仅在有合法权限的前提下下载和使用内容
3. **存储空间**: 确保有足够的磁盘空间存储下载的视频
4. **法律合规**: 使用本工具请遵守当地法律法规及平台服务条款

## 🔮 未来计划

- [ ] 支持更多视频平台（Bilibili、Instagram等）
- [ ] 扩展视频转码预设
- [ ] 实现批量链接和播放列表下载
- [ ] 集成字幕下载功能
- [ ] 增加应用内自动更新
- [ ] 验证 macOS 与 Linux 打包流程

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
- [FastAPI](https://fastapi.tiangolo.com/) - 本地 sidecar API
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 媒体下载引擎
- [requests](https://requests.readthedocs.io/) - HTTP 库
- [ffmpeg](https://ffmpeg.org/) - 视频处理工具

---

<div align="center">

**DouyinGo 2.0.2 · React/Tauri + Python sidecar**

</div>
