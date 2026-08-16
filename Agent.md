# Agent.md — Arena Stream 3.0

## 项目定位

本地 Web 体育直播搜索、深度解析与播放工具。Python 3.11 标准库 HTTP 服务提供 API 和静态页面；搜索使用 yt-dlp、DDGS 和中文站点定向查询；解析使用 Streamlink、yt-dlp、静态媒体扫描与可选 Playwright 网络观察；播放使用浏览器 HTML5、hls.js 和 mpegts.js。

项目只处理公开、无 DRM 且用户有权访问的内容。不得实现登录、付费墙、地域限制或 DRM 绕过。

## 运行与测试

本机首选解释器：

```text
C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe
```

```powershell
& "C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe" src\main.py --no-browser
& "C:\Users\OzzyZ\anaconda3\envs\livestream\python.exe" -m unittest discover -s tests -v
```

不要使用本机有编码问题的 `conda run`。

## 模块边界

- `search.py`：搜索 Provider、体育关键词扩展、结果归一化和去重
- `resolver.py`：分层播放方式判定、DRM 停止策略
- `discovery.py`：HTML/JSON/iframe 媒体扫描、隔离 Chromium 网络观察
- `proxy.py`：公开目标校验、上游请求、HLS 清单 URI 重写
- `server.py`：`/api/search`、`/api/resolve`、`/api/proxy` 和静态资源
- `web/`：无构建步骤的原生 HTML/CSS/JS 前端

## 关键约定

- HTTP 默认只监听 `127.0.0.1`。
- `/api/proxy` 必须在每次请求和每次重定向前验证公网目标，不能放宽私网限制。
- Playwright 上下文必须是临时无 Cookie 上下文；所有 HTTP(S) 子请求均须阻止本机、私网和保留地址。
- 检测到 Widevine、PlayReady、FairPlay、SAMPLE-AES 或许可证请求时停止，不能添加 DRM 或访问控制绕过。
- 前端不把未信任字符串写入 `innerHTML`；结果字段使用 `textContent`。
- 新增播放站点优先走官方嵌入或公开 API，然后才使用通用解析器。
- 不提交搜索结果、带 Token 的媒体地址、Cookie 或用户配置。
- 打包时必须包含 `src/web`，包括本地 `vendor/hls.min.js`、`vendor/mpegts.min.js` 和许可证。

## Git

远程仓库为 `https://github.com/ozzyzhou99/livestream-tool.git`，默认分支 `main`。
