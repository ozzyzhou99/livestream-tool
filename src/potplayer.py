"""PotPlayer 自动检测与启动模块"""
import os
import socket
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlunparse
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import winreg
    WINREG_OK = True
except ImportError:
    WINREG_OK = False

COMMON_PATHS = [
    r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"C:\Program Files\DAUM\PotPlayer\PotPlayerMini.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"C:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini.exe",
    r"D:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"D:\Program Files (x86)\DAUM\PotPlayer\PotPlayerMini64.exe",
    r"E:\Program Files\DAUM\PotPlayer\PotPlayerMini64.exe",
]

REG_KEYS = [
    r"SOFTWARE\DAUM\PotPlayer64",
    r"SOFTWARE\DAUM\PotPlayer",
    r"SOFTWARE\WOW6432Node\DAUM\PotPlayer64",
    r"SOFTWARE\WOW6432Node\DAUM\PotPlayer",
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# 跳过转发的响应头
_HOP_HEADERS = frozenset([
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
])


def find_potplayer() -> Optional[str]:
    """自动检测 PotPlayer 安装路径"""
    if WINREG_OK:
        for key_path in REG_KEYS:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                for val_name in ("ExePath", "Install_Dir"):
                    try:
                        val, _ = winreg.QueryValueEx(key, val_name)
                        if val_name == "Install_Dir":
                            for exe in ("PotPlayerMini64.exe", "PotPlayerMini.exe"):
                                full = os.path.join(val, exe)
                                if os.path.exists(full):
                                    return full
                        elif os.path.exists(val):
                            return val
                    except Exception:
                        pass
            except Exception:
                pass

    for path in COMMON_PATHS:
        if os.path.exists(path):
            return path

    return None


# ── 本地代理 ──────────────────────────────────────────────────────────────────

class _ProxyHandler(BaseHTTPRequestHandler):
    """把 PotPlayer 的请求加上 Referer 后转发给真实 CDN"""

    target_base: str = ""   # "https://play.gpycvac.com"
    referer: str = ""

    def _forward(self, method: str):
        target_url = self.target_base + self.path
        req_headers = {
            "User-Agent":   UA,
            "Referer":      self.referer,
            "Range":        self.headers.get("Range", ""),
        }
        req_headers = {k: v for k, v in req_headers.items() if v}
        try:
            resp = requests.request(
                method, target_url,
                headers=req_headers,
                stream=True,
                verify=False,
                timeout=30,
            )
            self.send_response(resp.status_code)
            for k, v in resp.headers.items():
                if k.lower() not in _HOP_HEADERS:
                    self.send_header(k, v)
            self.end_headers()
            if method != "HEAD":
                for chunk in resp.iter_content(65536):
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        break
        except Exception:
            self.send_error(502)

    def do_GET(self):  self._forward("GET")
    def do_HEAD(self): self._forward("HEAD")

    def log_message(self, *_): pass  # 静默


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _start_proxy(stream_url: str, referer: str) -> str:
    """
    启动本地代理，返回 PotPlayer 可直接播放的 localhost URL。
    代理线程为守护线程，随主进程退出。
    """
    parsed = urlparse(stream_url)
    target_base = f"{parsed.scheme}://{parsed.netloc}"
    local_path = parsed.path
    if parsed.query:
        local_path += "?" + parsed.query

    port = _free_port()

    # 动态绑定类属性
    handler_cls = type("Handler", (_ProxyHandler,), {
        "target_base": target_base,
        "referer":     referer,
    })

    server = HTTPServer(("127.0.0.1", port), handler_cls)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    return f"http://127.0.0.1:{port}{local_path}"


# ── 公共接口 ──────────────────────────────────────────────────────────────────

def open_stream(potplayer_path: str, stream_url: str,
                referer: str = "") -> tuple[bool, str]:
    """在 PotPlayer 中打开流地址，返回 (成功, 消息)"""
    if not potplayer_path:
        return False, "未配置 PotPlayer 路径，请在设置中指定"
    if not os.path.exists(potplayer_path):
        return False, f"PotPlayer 路径不存在：{potplayer_path}"
    try:
        if referer:
            play_url = _start_proxy(stream_url, referer)
        else:
            play_url = stream_url
        subprocess.Popen([potplayer_path, play_url])
        return True, "已启动 PotPlayer"
    except Exception as e:
        return False, f"启动失败：{e}"
