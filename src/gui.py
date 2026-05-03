"""主界面 — 直播解析工具"""
import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config, save_config
from stream_parser import get_qualities, get_stream_url, available_engines
from potplayer import find_potplayer, open_stream

# ─── 样式常量 ────────────────────────────────────────────────────────────────
BG = "#f4f6f8"
ACCENT = "#1565c0"
ACCENT_HOVER = "#1976d2"
LOG_BG = "#1e1e1e"
LOG_FG = "#d4d4d4"
LOG_OK = "#4caf50"
LOG_ERR = "#f44336"
LOG_INFO = "#64b5f6"
FONT = ("Microsoft YaHei UI", 9)
FONT_BOLD = ("Microsoft YaHei UI", 9, "bold")
FONT_TITLE = ("Microsoft YaHei UI", 13, "bold")


class LiveStreamApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("直播解析工具  |  PotPlayer 助手")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.cfg = load_config()
        self._qualities: list[str] = []
        self._parsed_url: str = ""

        self._build_ui()
        self._restore_geometry()
        self._auto_find_potplayer()
        self._log_info(f"就绪  •  解析引擎：{', '.join(available_engines()) or '未检测到，请配置环境'}")

    # ─── UI 构建 ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=14)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)  # log 区可伸缩

        # 标题行
        title_row = ttk.Frame(main)
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_row.columnconfigure(0, weight=1)
        ttk.Label(title_row, text="🎬  直播解析工具", font=FONT_TITLE,
                  foreground=ACCENT, background=BG).grid(row=0, column=0, sticky="w")
        ttk.Label(title_row, text="由 Ozzy 制作",
                  font=("Microsoft YaHei UI", 8), foreground="#aaaaaa",
                  background=BG).grid(row=0, column=1, sticky="e")

        self._build_input_frame(main)
        self._build_action_frame(main)
        self._build_log_frame(main)
        self._build_settings_frame(main)
        self._build_history_frame(main)

    def _build_input_frame(self, parent):
        f = ttk.LabelFrame(parent, text="  直播地址  ", padding=8)
        f.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        f.columnconfigure(0, weight=1)

        row = ttk.Frame(f)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(row, textvariable=self.url_var, font=FONT)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.url_entry.bind("<Return>", lambda _: self._do_parse())

        ttk.Button(row, text="粘贴", width=5,
                   command=self._paste_url).grid(row=0, column=1, padx=(0, 4))
        ttk.Button(row, text="清空", width=5,
                   command=lambda: self.url_var.set("")).grid(row=0, column=2, padx=(0, 4))
        self.parse_btn = ttk.Button(row, text="  解  析  ", command=self._do_parse)
        self.parse_btn.grid(row=0, column=3)

        ttk.Label(f, text="支持 Bilibili / 斗鱼 / 虎牙 / Twitch / YouTube 等及直链（m3u8/rtmp/flv）",
                  font=("Microsoft YaHei UI", 8), foreground="#888").grid(row=1, column=0, sticky="w", pady=(4, 2))

        # Referer 行
        ref_row = ttk.Frame(f)
        ref_row.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        ref_row.columnconfigure(1, weight=1)
        ttk.Label(ref_row, text="防盗链 Referer：", font=FONT).grid(row=0, column=0, padx=(0, 4))
        self.referer_var = tk.StringVar()
        ttk.Entry(ref_row, textvariable=self.referer_var, font=FONT).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(ref_row, text="自动提取", width=8,
                   command=self._auto_referer).grid(row=0, column=2, padx=(0, 4))
        ttk.Button(ref_row, text="清空", width=5,
                   command=lambda: self.referer_var.set("")).grid(row=0, column=3)
        ttk.Label(ref_row,
                  text="（直链遭遇 403 时填写直播页面域名，如 https://www.xxx.com/）",
                  font=("Microsoft YaHei UI", 8), foreground="#888").grid(
                  row=1, column=0, columnspan=4, sticky="w", pady=(2, 0))

    def _build_action_frame(self, parent):
        f = ttk.LabelFrame(parent, text="  播放控制  ", padding=8)
        f.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(f, text="画质：", font=FONT).grid(row=0, column=0, padx=(0, 4))

        self.quality_var = tk.StringVar(value="最佳画质")
        self.quality_combo = ttk.Combobox(f, textvariable=self.quality_var,
                                          state="readonly", width=16, font=FONT)
        self.quality_combo["values"] = ["最佳画质"]
        self.quality_combo.grid(row=0, column=1, padx=(0, 12))

        self.open_btn = ttk.Button(f, text="▶  在 PotPlayer 中打开",
                                   command=self._do_open, state="disabled")
        self.open_btn.grid(row=0, column=2, padx=(0, 6))

        self.copy_btn = ttk.Button(f, text="📋 复制流地址",
                                   command=self._do_copy, state="disabled")
        self.copy_btn.grid(row=0, column=3)

    def _build_log_frame(self, parent):
        f = ttk.LabelFrame(parent, text="  运行日志  ", padding=6)
        f.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        self.log_text = tk.Text(f, height=8, bg=LOG_BG, fg=LOG_FG,
                                font=("Consolas", 9), state="disabled",
                                relief="flat", wrap="word", cursor="arrow")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(f, command=self.log_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_text["yscrollcommand"] = sb.set

        self.log_text.tag_configure("ok", foreground=LOG_OK)
        self.log_text.tag_configure("err", foreground=LOG_ERR)
        self.log_text.tag_configure("info", foreground=LOG_INFO)
        self.log_text.tag_configure("dim", foreground="#888888")

    def _build_settings_frame(self, parent):
        f = ttk.LabelFrame(parent, text="  PotPlayer 路径  ", padding=8)
        f.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        f.columnconfigure(0, weight=1)

        row = ttk.Frame(f)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.pp_var = tk.StringVar(value=self.cfg.get("potplayer_path", ""))
        ttk.Entry(row, textvariable=self.pp_var, font=FONT).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(row, text="浏览", command=self._browse_potplayer).grid(row=0, column=1, padx=(0, 4))
        ttk.Button(row, text="自动检测", command=self._auto_find_potplayer_btn).grid(row=0, column=2, padx=(0, 4))
        ttk.Button(row, text="保存", command=self._save_potplayer).grid(row=0, column=3)

    def _build_history_frame(self, parent):
        f = ttk.LabelFrame(parent, text="  历史记录  ", padding=6)
        f.grid(row=5, column=0, sticky="ew")
        f.columnconfigure(0, weight=1)

        ctrl = ttk.Frame(f)
        ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        ttk.Label(ctrl, text="最近打开的直播（双击重新解析）：", font=FONT).pack(side="left")
        ttk.Button(ctrl, text="清空历史", command=self._clear_history).pack(side="right")

        self.history_list = tk.Listbox(f, height=4, font=("Consolas", 8),
                                       selectmode="single", relief="flat",
                                       bg="#fafafa", activestyle="dotbox")
        self.history_list.grid(row=1, column=0, sticky="ew")
        self.history_list.bind("<Double-Button-1>", self._history_open)

        hsb = ttk.Scrollbar(f, orient="horizontal", command=self.history_list.xview)
        hsb.grid(row=2, column=0, sticky="ew")
        self.history_list["xscrollcommand"] = hsb.set

        self._load_history()

    # ─── 日志 ────────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] ", "dim")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log_info(self, msg): self._log(msg, "info")
    def _log_ok(self, msg):   self._log(msg, "ok")
    def _log_err(self, msg):  self._log(msg, "err")

    # ─── 解析逻辑 ────────────────────────────────────────────────────────────

    def _do_parse(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入直播地址")
            return

        self._parsed_url = ""
        self.open_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.parse_btn.config(state="disabled", text="解析中…")
        self.quality_combo.config(state="disabled")
        self._log_info(f"正在解析：{url}")

        def worker():
            qualities, err = get_qualities(url)
            self.root.after(0, self._on_parse_done, url, qualities, err)

        threading.Thread(target=worker, daemon=True).start()

    def _on_parse_done(self, url, qualities, err):
        self.parse_btn.config(state="normal", text="  解  析  ")
        if err and not qualities:
            self._log_err(f"解析失败：{err}")
            messagebox.showerror("解析失败", err)
            return

        if err:
            self._log_info(f"提示：{err}")

        self._qualities = qualities
        self.quality_combo["values"] = qualities
        self.quality_combo.set(qualities[0])
        self.quality_combo.config(state="readonly")
        self._parsed_url = url
        self.open_btn.config(state="normal")
        self.copy_btn.config(state="normal")
        self._log_ok(f"解析成功，共 {len(qualities)} 种画质：{', '.join(qualities)}")

    # ─── 打开播放器 ──────────────────────────────────────────────────────────

    def _do_open(self):
        if not self._parsed_url:
            return
        quality = self.quality_var.get()
        pp_path = self.pp_var.get().strip()
        referer = self.referer_var.get().strip()

        self.open_btn.config(state="disabled", text="获取地址中…")
        self._log_info(f"获取 [{quality}] 流地址…")

        def worker():
            url, err = get_stream_url(self._parsed_url, quality)
            self.root.after(0, self._on_get_url_done, url, err, quality, pp_path, referer)

        threading.Thread(target=worker, daemon=True).start()

    def _on_get_url_done(self, stream_url, err, quality, pp_path, referer=""):
        self.open_btn.config(state="normal", text="▶  在 PotPlayer 中打开")
        if err or not stream_url:
            self._log_err(f"获取流地址失败：{err}")
            messagebox.showerror("失败", err or "无法获取流地址")
            return

        self._log_info(f"流地址：{stream_url[:80]}{'…' if len(stream_url) > 80 else ''}")
        if referer:
            self._log_info(f"使用 Referer：{referer}")
        ok, msg = open_stream(pp_path, stream_url, referer)
        if ok:
            self._log_ok(msg)
            self._add_history(self._parsed_url, quality)
        else:
            self._log_err(msg)
            messagebox.showerror("启动失败", msg)

    # ─── 复制流地址 ──────────────────────────────────────────────────────────

    def _do_copy(self):
        if not self._parsed_url:
            return
        quality = self.quality_var.get()
        self.copy_btn.config(state="disabled", text="获取中…")

        def worker():
            url, err = get_stream_url(self._parsed_url, quality)
            self.root.after(0, self._on_copy_done, url, err)

        threading.Thread(target=worker, daemon=True).start()

    def _on_copy_done(self, stream_url, err):
        self.copy_btn.config(state="normal", text="📋 复制流地址")
        if err or not stream_url:
            self._log_err(f"获取失败：{err}")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(stream_url)
            self._log_ok("流地址已复制到剪贴板")
        except Exception as e:
            self._log_err(f"复制失败：{e}")

    # ─── PotPlayer 设置 ──────────────────────────────────────────────────────

    def _browse_potplayer(self):
        path = filedialog.askopenfilename(
            title="选择 PotPlayer 可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initialdir=r"C:\Program Files",
        )
        if path:
            self.pp_var.set(path)

    def _auto_referer(self):
        """从 URL 输入框自动提取域名作为 Referer"""
        url = self.url_var.get().strip()
        if not url:
            self._log_err("请先在地址栏输入直播页面的 URL")
            return
        try:
            p = urlparse(url if url.startswith("http") else "https://" + url)
            referer = f"{p.scheme}://{p.netloc}/"
            self.referer_var.set(referer)
            self._log_info(f"已提取 Referer：{referer}")
        except Exception:
            self._log_err("无法解析 URL，请手动填写 Referer")

    def _auto_find_potplayer(self):
        if not self.cfg.get("potplayer_path"):
            found = find_potplayer()
            if found:
                self.pp_var.set(found)
                self.cfg["potplayer_path"] = found
                save_config(self.cfg)

    def _auto_find_potplayer_btn(self):
        found = find_potplayer()
        if found:
            self.pp_var.set(found)
            self._log_ok(f"自动检测到 PotPlayer：{found}")
        else:
            self._log_err("未能自动检测到 PotPlayer，请手动浏览选择")

    def _save_potplayer(self):
        path = self.pp_var.get().strip()
        self.cfg["potplayer_path"] = path
        save_config(self.cfg)
        self._log_ok(f"已保存 PotPlayer 路径：{path or '（已清空）'}")

    # ─── 历史记录 ────────────────────────────────────────────────────────────

    def _load_history(self):
        self.history_list.delete(0, "end")
        for item in reversed(self.cfg.get("history", [])):
            ts = item.get("time", "")
            url = item.get("url", "")
            q = item.get("quality", "")
            self.history_list.insert("end", f"[{ts}] [{q}]  {url}")

    def _add_history(self, url: str, quality: str):
        history = self.cfg.get("history", [])
        entry = {"url": url, "quality": quality, "time": datetime.now().strftime("%m-%d %H:%M")}
        history.append(entry)
        max_h = self.cfg.get("max_history", 50)
        self.cfg["history"] = history[-max_h:]
        save_config(self.cfg)
        self._load_history()

    def _clear_history(self):
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            self.cfg["history"] = []
            save_config(self.cfg)
            self._load_history()
            self._log_info("历史记录已清空")

    def _history_open(self, _event=None):
        sel = self.history_list.curselection()
        if not sel:
            return
        line = self.history_list.get(sel[0])
        # 格式: [时间] [画质]  url
        parts = line.split("  ", 1)
        if len(parts) == 2:
            url = parts[1].strip()
            self.url_var.set(url)
            self._do_parse()

    # ─── 粘贴 ────────────────────────────────────────────────────────────────

    def _paste_url(self):
        try:
            text = self.root.clipboard_get().strip()
            self.url_var.set(text)
        except Exception:
            pass

    # ─── 窗口 ────────────────────────────────────────────────────────────────

    def _restore_geometry(self):
        geo = self.cfg.get("window_geometry", "750x600")
        self.root.geometry(geo)
        self.root.update_idletasks()
        # 居中
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        geo = self.root.geometry().split("+")[0]
        self.cfg["window_geometry"] = geo
        save_config(self.cfg)
        self.root.destroy()
