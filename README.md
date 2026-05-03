# 直播解析工具 — PotPlayer 助手

将任意公开直播页面 URL 解析为流媒体地址，并一键在 PotPlayer 中打开观看。

---

## 功能特性

- **一键解析** Bilibili 直播、斗鱼、虎牙、Twitch、YouTube 直播等 80+ 个平台
- **画质选择** 自动列出所有可用画质，自由切换
- **直链支持** 直接粘贴 m3u8 / rtmp / flv / rtsp 地址也可直接打开
- **双引擎** streamlink（主）+ yt-dlp（备选），提高解析成功率
- **历史记录** 自动保存最近 50 条记录，双击可重新解析
- **PotPlayer 自动检测** 无需手动填写路径（也可手动指定）
- **复制流地址** 可将解析到的真实流地址复制到剪贴板，用于其他播放器

---

## 使用前提

| 软件 | 说明 |
|------|------|
| [PotPlayer](https://potplayer.daum.net/) | 必须安装，工具会自动检测路径 |
| [Anaconda / Miniconda](https://docs.conda.io/en/latest/miniconda.html) | 首次运行前需要配置环境 |

---

## 快速开始

### 第一步：配置 Python 环境（仅需一次）

双击运行：

```
setup_conda.bat
```

脚本会自动：
1. 创建名为 `livestream` 的独立 conda 环境（Python 3.11）
2. 安装 streamlink、yt-dlp、PyInstaller 等依赖

### 第二步：运行工具

**方式 A — 直接运行（开发/测试用）**

双击 `run.bat`，即可启动工具界面。

**方式 B — 打包为 exe（推荐日常使用）**

双击 `build.bat`，打包完成后在 `dist\` 目录找到 `直播解析工具.exe`，
可以单独复制到任意位置双击使用，**无需安装 Python 或 conda**。

---

## 使用方法

1. **粘贴直播页面 URL**
   - 例：`https://live.bilibili.com/123456`
   - 例：`https://www.douyu.com/123456`
   - 例：`https://www.twitch.tv/username`
   - 或直接粘贴流地址（m3u8/rtmp/flv）

2. **点击「解析」**
   - 工具会自动检测可用画质并填充下拉框
   - 日志区域会显示解析进度

3. **选择画质**
   - 默认选中「最佳画质」
   - 可在下拉框中切换其他分辨率

4. **点击「在 PotPlayer 中打开」**
   - 工具获取真实流地址并自动启动 PotPlayer 播放

5. **首次使用时设置 PotPlayer 路径**
   - 工具会尝试自动检测，如未检测到请点击「浏览」手动选择
   - 点击「保存」后，路径会被记住，下次无需重新配置

---

## 常见问题

**Q：提示「不支持该网站」**  
A：该平台可能没有 streamlink 插件，工具会自动切换到 yt-dlp 备选引擎。  
若两个引擎都不支持，可尝试在浏览器网络面板中手动找到 m3u8 地址后粘贴使用。

**Q：提示「未找到直播流」**  
A：请确认该直播正在进行中，且不是需要付费才能观看的直播。

**Q：PotPlayer 打开了但没有画面/无法播放**  
A：可能是流地址需要特定的 HTTP 头才能访问。可尝试先点击「复制流地址」，  
然后在 PotPlayer 中手动打开（Ctrl+U），或使用 mpv 等播放器。

**Q：打包 exe 后启动很慢**  
A：PyInstaller 单文件模式（--onefile）在每次启动时需要解压，属于正常现象，  
大约需要 5~15 秒。解压完成后正常运行。

**Q：如何更新解析引擎**  
A：打开命令行，执行：
```
conda activate livestream
pip install -U streamlink yt-dlp
```

---

## 项目结构

```
LiveStream\
├── src\
│   ├── main.py          # 程序入口
│   ├── gui.py           # 主界面（tkinter）
│   ├── stream_parser.py # 流地址解析（streamlink + yt-dlp）
│   ├── potplayer.py     # PotPlayer 检测与启动
│   └── config.py        # 配置读写（~/.livestream_tool/config.json）
├── requirements.txt     # Python 依赖
├── setup_conda.bat      # 一键配置 conda 环境
├── run.bat              # 直接运行（不打包）
├── build.bat            # 打包为 exe
└── README.md            # 本说明文件
```

---

## 支持平台示例

| 平台 | URL 示例 |
|------|----------|
| Bilibili 直播 | `https://live.bilibili.com/直播间号` |
| 斗鱼 | `https://www.douyu.com/房间号` |
| 虎牙 | `https://www.huya.com/房间号` |
| Twitch | `https://www.twitch.tv/主播名` |
| YouTube 直播 | `https://www.youtube.com/watch?v=视频ID` |
| 直链（m3u8） | `https://example.com/live/stream.m3u8` |
| 直链（rtmp） | `rtmp://live.example.com/app/stream` |

完整支持列表见 [streamlink 官方文档](https://streamlink.github.io/plugins.html)。
