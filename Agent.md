# Agent.md — 直播解析工具

本文件供 AI Agent（Claude Code）在本项目工作时参考。

---

## 项目定位

Windows 桌面工具：将直播页面 URL 解析为真实流媒体地址，并在 PotPlayer 中播放。
- **语言**：Python 3.11，tkinter GUI
- **平台**：仅 Windows（依赖 PotPlayer、winreg、.bat 脚本）
- **运行环境**：conda 虚拟环境 `livestream`

---

## 架构速览

```
src/main.py          → 入口，设置 ttk 主题，启动 LiveStreamApp
src/gui.py           → 全部 UI 逻辑（LiveStreamApp 类），中英双语
src/stream_parser.py → 解析引擎：streamlink（主）+ yt-dlp（备）
src/potplayer.py     → PotPlayer 自动检测 + 本地 HTTP 反向代理
src/config.py        → JSON 配置读写（~/.livestream_tool/config.json）
```

### 解析流程

```
输入 URL
  ├─ is_direct_url() → True  → 直接传给 PotPlayer（或经代理）
  └─ False
       ├─ streamlink.streams(url)
       │    ├─ 成功 → 返回画质列表 / 流地址
       │    └─ NoPluginError / 失败 → 降级到 yt-dlp
       └─ yt_dlp.extract_info(url)
            ├─ 成功 → 返回画质列表 / 流地址
            └─ 失败 → 报错
```

### 防盗链代理

当用户填写了 Referer 时，`potplayer.py` 在本地启动一个一次性 `HTTPServer`（随机端口，daemon 线程），把 PotPlayer 的请求透明转发到真实 CDN 并附加正确的 `Referer` 和 `User-Agent` 头。

---

## 开发环境

### Python 可执行文件

```
C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe
```

**重要**：本机 `conda run` 有 GBK 编码 bug，执行时会抛 `UnicodeEncodeError`。
始终用上面的绝对路径直接调用 Python，不要用 `conda run -n livestream python`。

### 运行项目

```powershell
& "C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe" src\main.py
```

或双击 `run.bat`（底层同上）。

### 测试单个 URL / 模块

写一个临时脚本，顶部加 `sys.path.insert(0, 'D:/ZZ/LiveStream/src')`，然后直接用 Python 路径运行：

```powershell
& "C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe" test_temp.py
```

临时测试文件命名用 `test_*.py`（已在 `.gitignore` 排除）。

### 打包 exe

```
双击 build.bat
```

输出：`dist\LiveStreamTool.exe`（独立，无需 Python）。
`build.bat` 硬编码了 Tcl/Tk 路径，避免 conda 环境下的版本冲突问题。

---

## 配置文件

持久化位置：`%USERPROFILE%\.livestream_tool\config.json`

```json
{
  "potplayer_path": "C:\\...\\PotPlayerMini64.exe",
  "default_quality": "best",
  "history": [...],
  "window_geometry": "750x600",
  "max_history": 50,
  "language": "zh"
}
```

`language` 字段由 GUI 的中英切换按钮写入，值为 `"zh"` 或 `"en"`。

---

## 关键约定

| 约定 | 说明 |
|------|------|
| 入口是 `main.py` | 不要直接运行 `gui.py`，`main.py` 负责设置 ttk 主题 |
| 双语字符串 | 全部在 `gui.py` 顶部的 `STRINGS` 字典维护，key 相同，`zh`/`en` 两套 |
| 画质 key 映射 | 用户看到的"最佳画质"在内部对应 streamlink key `"best"`，由 `quality_map` 转换 |
| 直链识别 | `is_direct_url()` 通过正则匹配 `.m3u8`、`.flv`、`rtmp://`、`rtsp://`、`mms://` |
| 代理生命周期 | 每次"打开"创建一个新代理进程，daemon 线程，主进程退出自动回收 |

---

## 已知限制

### tv.cctv.com（央视）

streamlink 无插件，yt-dlp 报 `Unsupported URL`。原因：CCTV 播放器使用 AES 加密的频道配置（`encrypted: true`）和动态 Token，必须在浏览器内完整执行才能获取流地址。

**临时方案**：F12 → Network → 筛选 `m3u8` → 复制 URL → 直接粘贴使用。

### run.bat / build.bat 硬编码路径

两个脚本均假设 conda 安装在 `%USERPROFILE%\anaconda3`。如果用户的 conda 装在其他位置，需手动修改路径。

### 仅 Windows

`potplayer.py` 通过 `winreg` 检测 PotPlayer，`find_potplayer()` 在非 Windows 系统上自动跳过注册表查询，只扫描常用路径（通常找不到）。

---

## 常用修改点

| 需求 | 位置 |
|------|------|
| 新增/修改 UI 文字 | `gui.py` → `STRINGS` 字典 |
| 新增平台特殊处理 | `stream_parser.py` → `get_qualities()` / `get_stream_url()` |
| 新增直链格式识别 | `stream_parser.py` → `DIRECT_PATTERNS` |
| 新增 PotPlayer 检测路径 | `potplayer.py` → `COMMON_PATHS` |
| 修改代理转发逻辑 | `potplayer.py` → `_ProxyHandler._forward()` |
| 修改配置默认值 | `config.py` → `DEFAULT_CONFIG` |

---

## Git

- 远程：`https://github.com/ozzyzhou99/livestream-tool.git`，分支 `main`
- `build/`、`dist/`、`*.spec`、`.claude/`、`用户使用手册.docx` 均在 `.gitignore` 中排除
- 提交后用 `git push origin main` 推送
