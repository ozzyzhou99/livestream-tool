# Arena Stream

<div align="center">

[中文](#中文) · [English](#english)

</div>

---

<a id="中文"></a>

# 中文

面向体育赛事的本地直播搜索、深度解析与浏览器播放工具。输入中文或英文的球队、联赛、车手和赛事关键词，应用会并行检索公开视频平台与中文直播站点，再按层级分析页面中的公开媒体流。

> 本项目只处理公开、无 DRM 且用户有权访问的内容。它不会绕过登录、付费墙、地域限制或 DRM。

## 为什么使用浏览器播放

3.0 版完全采用本地 Web 架构，不再把 PotPlayer 作为主播放器。浏览器路线更适合搜索、筛选、官方嵌入和多种流格式统一播放；`hls.js` 负责 HLS，`mpegts.js` 负责 HTTP-FLV，本地 Python 代理处理合法来源常见的跨域、相对分片路径和 Referer 请求头。对于无法在浏览器播放的内容，界面仍可打开原页面或复制解析后的媒体地址。

## 功能

- 关键词搜索：足球、篮球、F1、橄榄球及综合体育
- 中文关键词扩展、YouTube 视频检索、DuckDuckGo 视频/网页检索和中文站点定向搜索并行执行
- 定向覆盖哔哩哔哩直播、斗鱼、虎牙、抖音直播、央视频、央视网、微博和快手等公开页面
- “深度模式”扩大搜索范围，并在播放前启用动态网络观察
- 支持直接粘贴直播页面、`.m3u8`、`.flv`、`.mp4` 或 `.webm` 地址
- YouTube 使用隐私增强型官方嵌入播放器
- 分层解析：Streamlink → yt-dlp → HTML/内嵌 JSON 扫描 → 隔离 Chromium 网络观察
- 浏览器内 HLS、HTTP-FLV 和原生 HTML5 视频播放
- 识别 DASH/HLS 中常见 DRM 标记；检测到保护时停止解析并提示回到授权平台
- 本地 HLS 清单重写代理，自动处理分片、密钥和子清单相对地址
- 代理拒绝本机和私网目标，降低 SSRF 风险
- 响应式体育界面，可按项目和直播状态筛选

## 启动

### Windows 一键环境

首次运行：

```text
setup_conda.bat
```

之后双击：

```text
run.bat
```

应用默认监听 `127.0.0.1:8765` 并自动打开浏览器。如果端口已占用，会自动选择一个空闲端口。

### 普通 Python 环境

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python src\main.py
```

可用参数：

```text
python src/main.py --port 9000 --no-browser
```

## 使用

1. 输入球队、联赛或赛事，例如 `Arsenal`、`NBA Finals`、`Monaco GP`。
2. 选择左侧体育类别，点击搜索结果。
3. 可勾选“深度模式”。应用会在播放前验证目标，并依次尝试站点插件、通用提取、静态页面扫描和隔离浏览器网络观察；YouTube 使用官方嵌入。
4. 如果搜索框里输入完整 `https://` 地址，会直接生成可解析的结果卡片。

搜索结果受平台可用性、直播状态和网络环境影响。付费体育平台通常要求在其原站或官方 App 中观看，本项目不会尝试提取其受保护媒体。

## 架构

```text
src/
├── main.py              # 命令行入口与浏览器启动
├── server.py            # 本地 HTTP/API 与静态资源服务
├── search.py            # 可扩展搜索 Provider 与体育分类
├── resolver.py          # 分层解析、格式选择与 DRM 停止策略
├── discovery.py         # HTML/JSON 扫描和隔离浏览器网络观察
├── proxy.py             # 安全媒体代理与 HLS 清单重写
├── domain.py            # 搜索/播放数据对象
└── web/
    ├── index.html       # 搜索与播放器界面
    ├── styles.css
    ├── app.js
    └── vendor/          # 本地 hls.js、mpegts.js 及许可证
tests/                   # 标准库 unittest 测试
```

搜索层通过 `SearchService.providers` 扩展。接入官方赛事 API、拥有授权的私有目录或其他公开视频平台时，实现与 `YouTubeSearchProvider.search()` 相同的返回接口即可。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 打包

双击 `build.bat`，输出为 `dist\ArenaStream.exe`。Web 资源、`hls.js`、`mpegts.js` 与 Playwright Python 运行库会一并打包。Chromium 浏览器文件仍由 `setup_conda.bat` 安装在本机；若未安装，应用会自动退回静态扫描和通用解析。

## 技术参考

- [hls.js](https://github.com/video-dev/hls.js)：浏览器 HLS/MSE 播放
- [mpegts.js](https://github.com/xqq/mpegts.js)：浏览器 HTTP-FLV/MPEG-TS 播放
- [Streamlink](https://github.com/streamlink/streamlink)：直播站点解析
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)：公共视频搜索与媒体信息提取
- [DDGS](https://github.com/deedy5/duckduckgo_search)：无密钥网页与视频元搜索
- [Playwright](https://playwright.dev/python/)：隔离浏览器网络观察

第三方前端库的许可证文件保存在 `src/web/vendor/`。

---

<a id="english"></a>

# English

Arena Stream is a local sports stream search, resolution, and browser playback tool. Enter a team, league, driver, or event name in Chinese or English. The app searches public video platforms and Chinese streaming sites in parallel, then analyzes public media streams through a layered resolution pipeline.

> This project handles public, DRM-free content that you have the right to access. It does not bypass authentication, paywalls, geographic restrictions, or DRM.

## Why Browser Playback

Version 3.0 uses a local web architecture and removes PotPlayer as the primary player. The browser interface combines search, filtering, official embeds, and several stream formats. `hls.js` handles HLS, `mpegts.js` handles HTTP-FLV, and the local Python proxy supplies cross-origin access, relative segment paths, and Referer headers for permitted sources. You can open the source page or copy the resolved media URL when the browser cannot play a stream.

## Features

- Keyword search for football, basketball, Formula 1, American football, and other sports
- Parallel Chinese query expansion, YouTube video search, DuckDuckGo video and web search, and targeted Chinese site search
- Targeted coverage for public pages on Bilibili Live, Douyu, Huya, Douyin Live, Yangshipin, CCTV, Weibo, and Kuaishou
- Deep Mode expands the search scope and observes browser network traffic before playback
- Accepts live page URLs and direct `.m3u8`, `.flv`, `.mp4`, or `.webm` URLs
- YouTube playback through the privacy-enhanced official embed player
- Layered resolution: Streamlink → yt-dlp → HTML and embedded JSON scan → isolated Chromium network observation
- Browser playback for HLS, HTTP-FLV, and native HTML5 video
- Detection for common DRM markers in DASH and HLS; the resolver stops and sends you back to the authorized platform when it finds protected media
- Local HLS manifest rewriting for relative segments, keys, and child playlists
- Proxy protection against loopback and private network targets to reduce SSRF risk
- Responsive sports interface with category and live-status filters

## Getting Started

### Windows Setup

Run this file once:

```text
setup_conda.bat
```

Then double-click:

```text
run.bat
```

The app listens on `127.0.0.1:8765` and opens your browser. If another process uses that port, Arena Stream selects an available port.

### Standard Python Environment

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python src\main.py
```

Available options:

```text
python src/main.py --port 9000 --no-browser
```

## Usage

1. Enter a team, league, or event, such as `Arsenal`, `NBA Finals`, or `Monaco GP`.
2. Select a sport from the sidebar and choose a search result.
3. Enable Deep Mode to validate the target before playback. The resolver tries site plugins, generic extraction, static page scanning, and isolated browser network observation in order. YouTube uses the official embed player.
4. Paste a full `https://` URL into the search box to create a resolvable result card.

Results depend on platform availability, live status, and your network. Paid sports platforms often require their website or official app. Arena Stream does not extract protected media from those services.

## Architecture

```text
src/
├── main.py              # Command-line entry point and browser launch
├── server.py            # Local HTTP/API and static asset server
├── search.py            # Extensible search providers and sport categories
├── resolver.py          # Layered resolution, format selection, and DRM stop policy
├── discovery.py         # HTML/JSON scan and isolated browser network observation
├── proxy.py             # Safe media proxy and HLS manifest rewriting
├── domain.py            # Search and playback data objects
└── web/
    ├── index.html       # Search and player interface
    ├── styles.css
    ├── app.js
    └── vendor/          # Local hls.js, mpegts.js, and license files
tests/                   # Standard library unittest suite
```

Add providers through `SearchService.providers`. A provider for an official sports API, a licensed private catalog, or another public video platform can follow the return interface used by `YouTubeSearchProvider.search()`.

## Testing

```powershell
python -m unittest discover -s tests -v
```

## Packaging

Double-click `build.bat` to create `dist\ArenaStream.exe`. The package includes the web assets, `hls.js`, `mpegts.js`, and the Playwright Python runtime. `setup_conda.bat` installs the Chromium browser files on your computer. Without Chromium, Arena Stream uses static scanning and generic resolution.

## Technical References

- [hls.js](https://github.com/video-dev/hls.js): HLS/MSE playback in the browser
- [mpegts.js](https://github.com/xqq/mpegts.js): HTTP-FLV/MPEG-TS playback in the browser
- [Streamlink](https://github.com/streamlink/streamlink): live streaming site resolution
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): public video search and media information extraction
- [DDGS](https://github.com/deedy5/duckduckgo_search): web and video metasearch without an API key
- [Playwright](https://playwright.dev/python/): isolated browser network observation

You can find the third-party frontend licenses in `src/web/vendor/`.
