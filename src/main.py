"""Arena Stream application entry point."""

from __future__ import annotations

import argparse
import threading
import webbrowser

from server import create_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="搜索并播放公开体育直播")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认仅本机）")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    parser.add_argument("--no-browser", action="store_true", help="启动时不自动打开浏览器")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        server = create_server(args.host, args.port)
    except OSError:
        if args.port == 8765:
            server = create_server(args.host, 0)
        else:
            raise
    host, port = server.server_address[:2]
    browser_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    url = f"http://{browser_host}:{port}"
    print(f"Arena Stream 已启动：{url}")
    print("按 Ctrl+C 停止服务。")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
