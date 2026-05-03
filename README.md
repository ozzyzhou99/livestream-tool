# 🎬 直播解析工具 / LiveStream Tool

<div align="center">

[中文说明](#中文说明) · [English](#english)

</div>

---

<a name="中文说明"></a>
# 中文说明

将直播页面网址解析为真实流媒体地址，一键在 PotPlayer 中播放。内置本地代理自动处理防盗链，支持 80+ 主流直播平台及小众体育聚合站。

## 目录

- [功能特性](#功能特性)
- [安装与启动](#安装与启动)
- [界面说明](#界面说明)
- [使用场景](#使用场景)
- [防盗链 Referer 说明](#防盗链-referer-说明)
- [支持平台](#支持平台)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 自动解析 | 支持 Bilibili、斗鱼、虎牙、Twitch、YouTube 等 80+ 平台 |
| 双引擎 | streamlink（主）+ yt-dlp（备），提高成功率 |
| 防盗链处理 | 内置本地 HTTP 代理，自动附加 Referer，解决 403 错误 |
| 直链支持 | 粘贴 m3u8 / flv / rtmp / rtsp 直链即可直接播放 |
| 画质选择 | 自动列出所有可用画质供选择 |
| 复制流地址 | 将解析到的真实地址复制到剪贴板，供其他播放器使用 |
| 历史记录 | 保存最近 50 条记录，双击即可重新打开 |
| PotPlayer 自动检测 | 首次启动自动查找 PotPlayer 路径 |
| 中英双语界面 | 右上角可一键切换语言 |

---

## 安装与启动

### 前提条件

- **[PotPlayer](https://potplayer.daum.net/)**（必须安装）
- **[Anaconda 或 Miniconda](https://docs.conda.io/en/latest/miniconda.html)**（用于管理 Python 环境）

### 第一步：配置环境（仅需做一次）

双击运行 `setup_conda.bat`，脚本将自动：

1. 创建名为 `livestream` 的独立 conda 环境（Python 3.11）
2. 安装 streamlink、yt-dlp、PyInstaller 等全部依赖

### 第二步：启动工具

**方式 A — 直接运行（推荐日常使用）**

```
双击 run.bat
```

**方式 B — 打包为独立 exe（一次打包，随处可用）**

```
双击 build.bat
```

打包完成后在 `dist/` 目录下找到 `直播解析工具.exe`，双击即可运行，无需 Python 环境。

---

## 界面说明

```
┌─────────────────────────────────────────────────────────┐
│  🎬 直播解析工具                   由 Ozzy 制作    [EN] │
├──── 直播地址 ───────────────────────────────────────────┤
│  [地址输入框                    ] [粘贴] [清空] [解析]  │
│  支持 Bilibili / 斗鱼 / 虎牙 / Twitch / YouTube…       │
│  防盗链 Referer: [___________] [自动提取] [清空]        │
├──── 播放控制 ───────────────────────────────────────────┤
│  画质: [最佳画质 ▾]  [▶ 在 PotPlayer 中打开] [📋复制]  │
├──── 运行日志 ───────────────────────────────────────────┤
│  (实时显示解析过程和结果)                               │
├──── PotPlayer 路径 ─────────────────────────────────────┤
│  [路径输入框              ] [浏览] [自动检测] [保存]    │
├──── 历史记录 ───────────────────────────────────────────┤
│  最近打开的直播（双击重新解析）：          [清空历史]   │
│  (历史列表)                                             │
└─────────────────────────────────────────────────────────┘
```

### 各区域功能

| 区域 | 说明 |
|------|------|
| **直播地址** | 粘贴直播页面网址或 m3u8/rtmp 直链 |
| **防盗链 Referer** | 解决某些平台报 403 错误时使用（见下文说明）|
| **画质** | 解析成功后显示所有可用画质，点击下拉选择 |
| **▶ 在 PotPlayer 中打开** | 获取流地址并启动 PotPlayer 播放 |
| **📋 复制流地址** | 将真实流地址复制到剪贴板 |
| **运行日志** | 显示每一步的操作结果，出错时查看这里 |
| **PotPlayer 路径** | 通常自动检测，找不到时手动浏览指定 |
| **历史记录** | 保存最近 50 条，双击可重新解析 |

---

## 使用场景

### 场景一：主流平台（Bilibili、斗鱼、虎牙、Twitch、YouTube）

1. 打开直播页面，复制浏览器地址栏的 URL
2. 粘贴到工具的"直播地址"栏（或点"粘贴"按钮）
3. 点击**解析**（或按回车）
4. 解析完成后，在画质下拉框选择画质
5. 点击**在 PotPlayer 中打开**

### 场景二：直播聚合站 / 小众体育直播

这类平台通常没有 streamlink/yt-dlp 插件支持，需要手动获取流地址：

1. 在浏览器打开直播页面，按 `F12` 打开开发者工具
2. 切换到 **Network（网络）** 标签，点击筛选栏的 **Fetch/XHR**
3. 刷新页面，在列表中找到包含 `play_url`、`stream` 等关键词的请求
4. 点开请求，查看响应内容，复制其中的 m3u8 / flv 地址
5. 将复制的地址粘贴到工具的"直播地址"栏
6. 点击"自动提取"自动填写 Referer（或手动填入直播页面的域名）
7. 点击**在 PotPlayer 中打开**

### 场景三：已有 m3u8 / rtmp 直链

直接粘贴直链到地址栏，**无需点解析**，直接点**在 PotPlayer 中打开**即可。

工具会自动识别以下格式的直链：
- `https://example.com/live/stream.m3u8`
- `https://example.com/live/stream.m3u8?token=xxx`
- `rtmp://live.example.com/app/stream`
- `rtsp://camera.example.com/live`

### 场景四：CCTV / 央视等受保护平台

部分平台（如央视 `tv.cctv.com`）使用 DRM 加密或动态 Token，streamlink 和 yt-dlp 均无法自动解析。请使用 F12 手动抓取：

1. 用 Chrome 打开直播页面（如 `https://tv.cctv.com/live/cctv5plus/`）
2. 按 `F12` → **Network** 标签 → 筛选框输入 `m3u8`
3. 点击页面上的视频使其开始播放
4. 在 Network 列表中找到 `.../index.m3u8` 请求，右键 → **Copy URL**
5. 将复制的 URL 直接粘贴到工具，无需解析，直接点**打开**

---

## 防盗链 Referer 说明

某些平台的直播流 URL 在被第三方播放器直接访问时会返回 **403 Forbidden**，这是"防盗链"机制。解决方法：

- 点击 Referer 旁的**"自动提取"**按钮，工具会从地址栏 URL 中自动提取域名填入
- 工具会在本地启动一个 HTTP 代理，PotPlayer 通过代理访问流，代理自动附加 Referer 头

手动填写格式示例：`https://www.huya.com/`（必须带末尾斜线）

---

## 支持平台

| 平台 | 地址格式示例 |
|------|------------|
| Bilibili 直播 | `https://live.bilibili.com/<房间号>` |
| 斗鱼 | `https://www.douyu.com/<房间号>` |
| 虎牙 | `https://www.huya.com/<房间名>` |
| Twitch | `https://www.twitch.tv/<用户名>` |
| YouTube 直播 | `https://www.youtube.com/watch?v=<ID>` |
| 直链 | `https://example.com/stream.m3u8` |

完整插件列表：[streamlink 官方文档](https://streamlink.github.io/plugins.html)

---

## 常见问题

**Q：点解析后一直没反应 / 很慢？**
A：解析过程涉及网络请求，正常需要 3–15 秒。查看运行日志了解进度。

**Q：解析失败，提示"不支持该网站"？**
A：该平台没有 streamlink 插件，yt-dlp 也无法解析。请改用 F12 手动抓取流地址（见场景二/四）。

**Q：打开后 PotPlayer 播放有声音但无画面？**
A：尝试在画质下拉框选择其他画质，或在 PotPlayer 内按 `Tab` 切换解码方式。

**Q：遇到 403 错误？**
A：填写 Referer（点"自动提取"）后重试。

**Q：找不到 PotPlayer？**
A：点"自动检测"；若仍未找到，点"浏览"手动选择 `PotPlayer64.exe` 或 `PotPlayer.exe`，然后点"保存"。

**Q：历史记录双击后解析失败？**
A：直播可能已结束，或平台链接已变化。

---

## 项目结构

```
LiveStream/
├── src/
│   ├── main.py           # 程序入口
│   ├── gui.py            # 界面（tkinter）
│   ├── stream_parser.py  # 解析引擎（streamlink + yt-dlp）
│   ├── potplayer.py      # PotPlayer 启动 + 本地代理
│   └── config.py         # 配置读写
├── setup_conda.bat       # 一键配置 conda 环境
├── run.bat               # 直接运行
├── build.bat             # 打包为 exe
└── requirements.txt
```

---

*仅供个人使用。请勿用于付费或受版权保护的内容。*

*Made by Ozzy*

---
---

<a name="english"></a>
# English

Parse live stream page URLs into real media stream addresses and open them directly in PotPlayer. Features a built-in local HTTP proxy for automatic hotlink protection (Referer) handling. Supports 80+ mainstream streaming platforms.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Interface Overview](#interface-overview)
- [Usage Scenarios](#usage-scenarios)
- [Hotlink Referer Explained](#hotlink-referer-explained)
- [Supported Platforms](#supported-platforms)
- [FAQ](#faq)
- [Project Structure](#project-structure)

---

## Features

| Feature | Description |
|---------|-------------|
| Auto-parse | Supports Bilibili, Douyu, Huya, Twitch, YouTube, and 80+ platforms |
| Dual engine | streamlink (primary) + yt-dlp (fallback) for higher success rate |
| Hotlink bypass | Built-in local HTTP proxy automatically injects Referer headers on 403 errors |
| Direct link support | Paste m3u8 / flv / rtmp / rtsp URLs and play instantly — no parsing needed |
| Quality selection | All available qualities listed automatically |
| Copy stream URL | Copy the real stream address to clipboard for use in other players |
| History | Last 50 entries saved; double-click to reopen |
| Auto-detect PotPlayer | Finds PotPlayer path on first launch |
| Bilingual UI | Toggle Chinese / English from the top-right corner |

---

## Installation

### Prerequisites

- **[PotPlayer](https://potplayer.daum.net/)** (required)
- **[Anaconda or Miniconda](https://docs.conda.io/en/latest/miniconda.html)** (for managing the Python environment)

### Step 1 — Set up the environment (one time only)

Double-click `setup_conda.bat`. The script will automatically:

1. Create an isolated conda environment named `livestream` (Python 3.11)
2. Install all dependencies: streamlink, yt-dlp, PyInstaller, etc.

### Step 2 — Launch the tool

**Option A — Run from source (recommended for regular use)**

```
Double-click run.bat
```

**Option B — Build a standalone exe (run anywhere without Python)**

```
Double-click build.bat
```

After the build finishes, find `LiveStreamTool.exe` in the `dist/` folder. Double-click to run — no Python installation required.

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  🎬 Live Stream Tool                 Made by Ozzy  [中文]│
├──── Stream URL ─────────────────────────────────────────┤
│  [URL input box                 ] [Paste] [Clear] [Parse]│
│  Supports Bilibili / Douyu / Huya / Twitch / YouTube…   │
│  Hotlink Referer: [___________] [Auto Extract] [Clear]  │
├──── Playback ───────────────────────────────────────────┤
│  Quality: [Best ▾]  [▶ Open in PotPlayer] [📋 Copy URL] │
├──── Log ────────────────────────────────────────────────┤
│  (real-time parsing progress and results)               │
├──── PotPlayer Path ─────────────────────────────────────┤
│  [path input box          ] [Browse] [Auto Detect] [Save]│
├──── History ────────────────────────────────────────────┤
│  Recent streams (double-click to reopen):   [Clear All] │
│  (history list)                                         │
└─────────────────────────────────────────────────────────┘
```

### Panel Reference

| Panel | Function |
|-------|----------|
| **Stream URL** | Paste a stream page URL or a direct m3u8/rtmp link |
| **Hotlink Referer** | Fill in when a 403 error occurs (see explanation below) |
| **Quality** | Drop-down appears after a successful parse; select desired quality |
| **▶ Open in PotPlayer** | Fetch the stream URL and launch PotPlayer |
| **📋 Copy Stream URL** | Copy the resolved stream address to clipboard |
| **Log** | Shows step-by-step results; check here when something goes wrong |
| **PotPlayer Path** | Usually auto-detected; browse manually if not found |
| **History** | Last 50 streams; double-click to re-parse |

---

## Usage Scenarios

### Scenario 1 — Major platforms (Bilibili, Douyu, Huya, Twitch, YouTube)

1. Open the live stream page in your browser and copy the URL from the address bar
2. Paste it into the **Stream URL** field (or click **Paste**)
3. Click **Parse** (or press Enter)
4. Once parsing succeeds, select a quality from the drop-down
5. Click **▶ Open in PotPlayer**

### Scenario 2 — Sports aggregator sites / niche live platforms

These sites typically have no streamlink/yt-dlp plugin support. You need to extract the stream URL manually:

1. Open the live page in your browser and press `F12` to open DevTools
2. Go to the **Network** tab, then click the **Fetch/XHR** filter
3. Reload the page; look for a request containing keywords like `play_url`, `stream`, or `hls`
4. Click the request and inspect the **Response** — copy the m3u8 or flv URL from the JSON
5. Paste that URL into the **Stream URL** field
6. Click **Auto Extract** to fill in the Referer, or type the stream page's domain manually
7. Click **▶ Open in PotPlayer**

### Scenario 3 — You already have a direct m3u8 / rtmp link

Paste the link directly into the URL field. **Skip the Parse step** — just click **▶ Open in PotPlayer** right away.

The tool automatically recognises these direct-link formats:

- `https://example.com/live/stream.m3u8`
- `https://example.com/live/stream.m3u8?token=xxx`
- `rtmp://live.example.com/app/stream`
- `rtsp://camera.example.com/live`

### Scenario 4 — DRM-protected platforms (e.g., CCTV)

Some platforms (such as China's `tv.cctv.com`) use DRM encryption or dynamic per-session tokens. Neither streamlink nor yt-dlp can parse them automatically. Use the browser's DevTools to capture the URL instead:

1. Open the stream page in **Chrome** (e.g., `https://tv.cctv.com/live/cctv5plus/`)
2. Press `F12` → **Network** tab → type `m3u8` in the filter box
3. Click the video on the page to start playback
4. Find an `index.m3u8` request in the Network list, right-click → **Copy URL**
5. Paste the copied URL directly into the tool and click **▶ Open in PotPlayer** — no Parse step needed

---

## Hotlink Referer Explained

Some platforms reject direct playback requests from third-party players with a **403 Forbidden** error. This is called hotlinking protection. The tool handles it like this:

1. Fill in the **Referer** field (click **Auto Extract** to populate it automatically from the URL you entered, or type the stream page's origin manually — e.g., `https://www.huya.com/`)
2. The tool starts a local HTTP proxy on your machine
3. PotPlayer fetches the stream through the proxy, which adds the correct `Referer` header to every request

Format for manual entry: `https://www.example.com/` (trailing slash required)

---

## Supported Platforms

| Platform | Example URL |
|----------|-------------|
| Bilibili Live | `https://live.bilibili.com/<room_id>` |
| Douyu | `https://www.douyu.com/<room_id>` |
| Huya | `https://www.huya.com/<username>` |
| Twitch | `https://www.twitch.tv/<username>` |
| YouTube Live | `https://www.youtube.com/watch?v=<id>` |
| Direct link | `https://example.com/stream.m3u8` / `rtmp://...` |

Full plugin list: [streamlink plugins documentation](https://streamlink.github.io/plugins.html)

---

## FAQ

**Q: The Parse button hangs / takes a long time?**
A: Parsing requires network requests and typically takes 3–15 seconds. Watch the Log panel for progress.

**Q: Parse fails with "Unsupported URL" or "no plugin"?**
A: The platform has no streamlink/yt-dlp support. Use F12 DevTools to manually extract the stream URL (see Scenario 2 or 4).

**Q: PotPlayer opens but there is audio and no video?**
A: Try selecting a different quality from the drop-down, or press `Tab` inside PotPlayer to switch the video decoder.

**Q: I get a 403 Forbidden error?**
A: Fill in the Referer field (click **Auto Extract**) and try again.

**Q: PotPlayer is not detected automatically?**
A: Click **Auto Detect**. If it still fails, click **Browse**, navigate to `PotPlayer64.exe` or `PotPlayer.exe`, select it, then click **Save**.

**Q: Double-clicking a history entry fails to parse?**
A: The stream has likely ended, or the platform URL has changed.

**Q: Can I use this with VLC or MPV instead of PotPlayer?**
A: Use the **📋 Copy Stream URL** button to copy the resolved stream address to your clipboard, then open it in any player you prefer.

---

## Project Structure

```
LiveStream/
├── src/
│   ├── main.py           # Entry point
│   ├── gui.py            # UI (tkinter)
│   ├── stream_parser.py  # Parse engine (streamlink + yt-dlp)
│   ├── potplayer.py      # PotPlayer launcher + local proxy
│   └── config.py         # Settings persistence
├── setup_conda.bat       # One-click conda environment setup
├── run.bat               # Run from source
├── build.bat             # Build standalone exe
└── requirements.txt
```

---

*For personal use only. Do not use for paid or copyright-protected content.*

*Made by Ozzy*
