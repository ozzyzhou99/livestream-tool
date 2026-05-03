"""主界面 — 直播解析工具 / Live Stream Tool"""
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

# ─── 多语言字符串 ─────────────────────────────────────────────────────────────
STRINGS = {
    "zh": {
        "window_title":         "直播解析工具  |  PotPlayer 助手",
        "app_title":            "🎬  直播解析工具",
        "made_by":              "由 Ozzy 制作",
        "lang_switch":          "EN",
        "frame_url":            "  直播地址  ",
        "btn_paste":            "粘贴",
        "btn_clear":            "清空",
        "btn_parse":            "  解  析  ",
        "btn_parsing":          "解析中…",
        "url_hint":             "支持 Bilibili / 斗鱼 / 虎牙 / Twitch / YouTube 等及直链（m3u8/rtmp/flv）",
        "referer_label":        "防盗链 Referer：",
        "btn_auto_referer":     "自动提取",
        "btn_clear_referer":    "清空",
        "referer_hint":         "（直链遭遇 403 时填写直播页面域名，如 https://www.xxx.com/）",
        "frame_action":         "  播放控制  ",
        "quality_label":        "画质：",
        "quality_best":         "最佳画质",
        "btn_open":             "▶  在 PotPlayer 中打开",
        "btn_opening":          "获取地址中…",
        "btn_copy":             "📋 复制流地址",
        "btn_copying":          "获取中…",
        "frame_log":            "  运行日志  ",
        "frame_settings":       "  PotPlayer 路径  ",
        "btn_browse":           "浏览",
        "btn_autodetect":       "自动检测",
        "btn_save":             "保存",
        "frame_history":        "  历史记录  ",
        "history_label":        "最近打开的直播（双击重新解析）：",
        "btn_clear_history":    "清空历史",
        "log_ready":            "就绪  •  解析引擎：{}",
        "log_no_engine":        "未检测到，请配置环境",
        "log_parsing":          "正在解析：{}",
        "log_parse_fail":       "解析失败：{}",
        "log_parse_hint":       "提示：{}",
        "log_parse_ok":         "解析成功，共 {} 种画质：{}",
        "log_fetching":         "获取 [{}] 流地址…",
        "log_stream_url":       "流地址：{}",
        "log_referer_used":     "使用 Referer：{}",
        "log_get_fail":         "获取流地址失败：{}",
        "log_copy_fail":        "获取失败：{}",
        "log_copied":           "流地址已复制到剪贴板",
        "log_copy_err":         "复制失败：{}",
        "log_pp_found":         "自动检测到 PotPlayer：{}",
        "log_pp_not_found":     "未能自动检测到 PotPlayer，请手动浏览选择",
        "log_pp_saved":         "已保存 PotPlayer 路径：{}",
        "log_pp_cleared":       "（已清空）",
        "log_history_cleared":  "历史记录已清空",
        "log_referer_ok":       "已提取 Referer：{}",
        "log_no_url_referer":   "请先在地址栏输入直播页面的 URL",
        "log_referer_fail":     "无法解析 URL，请手动填写 Referer",
        "warn_no_url_title":    "提示",
        "warn_no_url_msg":      "请输入直播地址",
        "err_parse_title":      "解析失败",
        "err_open_title":       "失败",
        "err_open_no_url":      "无法获取流地址",
        "err_start_title":      "启动失败",
        "confirm_clear_title":  "确认",
        "confirm_clear_msg":    "确定要清空所有历史记录吗？",
        "dlg_browse_pp":        "选择 PotPlayer 可执行文件",
        "dlg_filter_exe":       "可执行文件",
        "dlg_filter_all":       "所有文件",
    },
    "en": {
        "window_title":         "Live Stream Tool  |  PotPlayer Helper",
        "app_title":            "🎬  Live Stream Tool",
        "made_by":              "Made by Ozzy",
        "lang_switch":          "中文",
        "frame_url":            "  Stream URL  ",
        "btn_paste":            "Paste",
        "btn_clear":            "Clear",
        "btn_parse":            "  Parse  ",
        "btn_parsing":          "Parsing…",
        "url_hint":             "Supports Bilibili / Douyu / Huya / Twitch / YouTube and direct links (m3u8/rtmp/flv)",
        "referer_label":        "Hotlink Referer:",
        "btn_auto_referer":     "Auto Extract",
        "btn_clear_referer":    "Clear",
        "referer_hint":         "(Fill in stream page domain on 403, e.g. https://www.xxx.com/)",
        "frame_action":         "  Playback  ",
        "quality_label":        "Quality:",
        "quality_best":         "Best",
        "btn_open":             "▶  Open in PotPlayer",
        "btn_opening":          "Fetching URL…",
        "btn_copy":             "📋 Copy Stream URL",
        "btn_copying":          "Fetching…",
        "frame_log":            "  Log  ",
        "frame_settings":       "  PotPlayer Path  ",
        "btn_browse":           "Browse",
        "btn_autodetect":       "Auto Detect",
        "btn_save":             "Save",
        "frame_history":        "  History  ",
        "history_label":        "Recent streams (double-click to reopen):",
        "btn_clear_history":    "Clear History",
        "log_ready":            "Ready  •  Parse engines: {}",
        "log_no_engine":        "none found, please set up environment",
        "log_parsing":          "Parsing: {}",
        "log_parse_fail":       "Parse failed: {}",
        "log_parse_hint":       "Note: {}",
        "log_parse_ok":         "Parsed successfully, {} qualities: {}",
        "log_fetching":         "Fetching [{}] stream URL…",
        "log_stream_url":       "Stream URL: {}",
        "log_referer_used":     "Using Referer: {}",
        "log_get_fail":         "Failed to get stream URL: {}",
        "log_copy_fail":        "Fetch failed: {}",
        "log_copied":           "Stream URL copied to clipboard",
        "log_copy_err":         "Copy failed: {}",
        "log_pp_found":         "Auto-detected PotPlayer: {}",
        "log_pp_not_found":     "PotPlayer not found, please browse manually",
        "log_pp_saved":         "PotPlayer path saved: {}",
        "log_pp_cleared":       "(cleared)",
        "log_history_cleared":  "History cleared",
        "log_referer_ok":       "Referer extracted: {}",
        "log_no_url_referer":   "Please enter a stream URL first",
        "log_referer_fail":     "Cannot parse URL, please fill in Referer manually",
        "warn_no_url_title":    "Notice",
        "warn_no_url_msg":      "Please enter a stream URL",
        "err_parse_title":      "Parse Failed",
        "err_open_title":       "Error",
        "err_open_no_url":      "Unable to get stream URL",
        "err_start_title":      "Launch Failed",
        "confirm_clear_title":  "Confirm",
        "confirm_clear_msg":    "Clear all history?",
        "dlg_browse_pp":        "Select PotPlayer executable",
        "dlg_filter_exe":       "Executable files",
        "dlg_filter_all":       "All files",
    },
}


class LiveStreamApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.cfg = load_config()
        self.lang: str = self.cfg.get("language", "zh")
        self._qualities: list[str] = []
        self._parsed_url: str = ""

        self._build_ui()
        self._restore_geometry()
        self._auto_find_potplayer()
        engines = available_engines()
        eng_str = ", ".join(engines) if engines else self._t("log_no_engine")
        self._log_info(self._t("log_ready").format(eng_str))

    # ─── 多语言 ──────────────────────────────────────────────────────────────

    def _t(self, key: str) -> str:
        return STRINGS[self.lang].get(key, STRINGS["zh"].get(key, key))

    def _switch_lang(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        self.cfg["language"] = self.lang
        save_config(self.cfg)
        self._apply_lang()

    def _apply_lang(self):
        """Update all translatable widgets after language change."""
        s = STRINGS[self.lang]

        self.root.title(s["window_title"])
        self._lbl_title.configure(text=s["app_title"])
        self._lbl_made_by.configure(text=s["made_by"])
        self._btn_lang.configure(text=s["lang_switch"])

        self._frm_url.configure(text=s["frame_url"])
        self._btn_paste.configure(text=s["btn_paste"])
        self._btn_clear_url.configure(text=s["btn_clear"])
        self._btn_parse.configure(text=s["btn_parse"])
        self._lbl_url_hint.configure(text=s["url_hint"])
        self._lbl_referer.configure(text=s["referer_label"])
        self._btn_auto_referer.configure(text=s["btn_auto_referer"])
        self._btn_clear_referer.configure(text=s["btn_clear_referer"])
        self._lbl_referer_hint.configure(text=s["referer_hint"])

        self._frm_action.configure(text=s["frame_action"])
        self._lbl_quality.configure(text=s["quality_label"])
        if not self._parsed_url:
            self.quality_combo["values"] = [s["quality_best"]]
            self.quality_var.set(s["quality_best"])
        self._btn_open.configure(text=s["btn_open"])
        self._btn_copy.configure(text=s["btn_copy"])

        self._frm_log.configure(text=s["frame_log"])

        self._frm_settings.configure(text=s["frame_settings"])
        self._btn_browse.configure(text=s["btn_browse"])
        self._btn_autodetect.configure(text=s["btn_autodetect"])
        self._btn_save.configure(text=s["btn_save"])

        self._frm_history.configure(text=s["frame_history"])
        self._lbl_history.configure(text=s["history_label"])
        self._btn_clear_history.configure(text=s["btn_clear_history"])

    # ─── UI 构建 ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.title(self._t("window_title"))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=14)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)

        # 标题行
        title_row = ttk.Frame(main)
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_row.columnconfigure(0, weight=1)

        self._lbl_title = ttk.Label(title_row, text=self._t("app_title"),
                                    font=FONT_TITLE, foreground=ACCENT, background=BG)
        self._lbl_title.grid(row=0, column=0, sticky="w")

        self._lbl_made_by = ttk.Label(title_row, text=self._t("made_by"),
                                      font=("Microsoft YaHei UI", 8),
                                      foreground="#aaaaaa", background=BG)
        self._lbl_made_by.grid(row=0, column=1, sticky="e", padx=(0, 8))

        self._btn_lang = ttk.Button(title_row, text=self._t("lang_switch"),
                                    width=5, command=self._switch_lang)
        self._btn_lang.grid(row=0, column=2, sticky="e")

        self._build_input_frame(main)
        self._build_action_frame(main)
        self._build_log_frame(main)
        self._build_settings_frame(main)
        self._build_history_frame(main)

    def _build_input_frame(self, parent):
        self._frm_url = ttk.LabelFrame(parent, text=self._t("frame_url"), padding=8)
        self._frm_url.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._frm_url.columnconfigure(0, weight=1)

        row = ttk.Frame(self._frm_url)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(row, textvariable=self.url_var, font=FONT)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.url_entry.bind("<Return>", lambda _: self._do_parse())

        self._btn_paste = ttk.Button(row, text=self._t("btn_paste"), width=5,
                                     command=self._paste_url)
        self._btn_paste.grid(row=0, column=1, padx=(0, 4))

        self._btn_clear_url = ttk.Button(row, text=self._t("btn_clear"), width=5,
                                         command=lambda: self.url_var.set(""))
        self._btn_clear_url.grid(row=0, column=2, padx=(0, 4))

        self._btn_parse = ttk.Button(row, text=self._t("btn_parse"),
                                     command=self._do_parse)
        self._btn_parse.grid(row=0, column=3)

        self._lbl_url_hint = ttk.Label(self._frm_url, text=self._t("url_hint"),
                                       font=("Microsoft YaHei UI", 8), foreground="#888")
        self._lbl_url_hint.grid(row=1, column=0, sticky="w", pady=(4, 2))

        ref_row = ttk.Frame(self._frm_url)
        ref_row.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        ref_row.columnconfigure(1, weight=1)

        self._lbl_referer = ttk.Label(ref_row, text=self._t("referer_label"), font=FONT)
        self._lbl_referer.grid(row=0, column=0, padx=(0, 4))

        self.referer_var = tk.StringVar()
        ttk.Entry(ref_row, textvariable=self.referer_var, font=FONT).grid(
            row=0, column=1, sticky="ew", padx=(0, 6))

        self._btn_auto_referer = ttk.Button(ref_row, text=self._t("btn_auto_referer"),
                                            width=10, command=self._auto_referer)
        self._btn_auto_referer.grid(row=0, column=2, padx=(0, 4))

        self._btn_clear_referer = ttk.Button(ref_row, text=self._t("btn_clear_referer"),
                                             width=5,
                                             command=lambda: self.referer_var.set(""))
        self._btn_clear_referer.grid(row=0, column=3)

        self._lbl_referer_hint = ttk.Label(ref_row, text=self._t("referer_hint"),
                                           font=("Microsoft YaHei UI", 8), foreground="#888")
        self._lbl_referer_hint.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 0))

    def _build_action_frame(self, parent):
        self._frm_action = ttk.LabelFrame(parent, text=self._t("frame_action"), padding=8)
        self._frm_action.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self._lbl_quality = ttk.Label(self._frm_action, text=self._t("quality_label"),
                                      font=FONT)
        self._lbl_quality.grid(row=0, column=0, padx=(0, 4))

        self.quality_var = tk.StringVar(value=self._t("quality_best"))
        self.quality_combo = ttk.Combobox(self._frm_action, textvariable=self.quality_var,
                                          state="readonly", width=16, font=FONT)
        self.quality_combo["values"] = [self._t("quality_best")]
        self.quality_combo.grid(row=0, column=1, padx=(0, 12))

        self._btn_open = ttk.Button(self._frm_action, text=self._t("btn_open"),
                                    command=self._do_open, state="disabled")
        self._btn_open.grid(row=0, column=2, padx=(0, 6))

        self._btn_copy = ttk.Button(self._frm_action, text=self._t("btn_copy"),
                                    command=self._do_copy, state="disabled")
        self._btn_copy.grid(row=0, column=3)

    def _build_log_frame(self, parent):
        self._frm_log = ttk.LabelFrame(parent, text=self._t("frame_log"), padding=6)
        self._frm_log.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        self._frm_log.rowconfigure(0, weight=1)
        self._frm_log.columnconfigure(0, weight=1)

        self.log_text = tk.Text(self._frm_log, height=8, bg=LOG_BG, fg=LOG_FG,
                                font=("Consolas", 9), state="disabled",
                                relief="flat", wrap="word", cursor="arrow")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(self._frm_log, command=self.log_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_text["yscrollcommand"] = sb.set

        self.log_text.tag_configure("ok",   foreground=LOG_OK)
        self.log_text.tag_configure("err",  foreground=LOG_ERR)
        self.log_text.tag_configure("info", foreground=LOG_INFO)
        self.log_text.tag_configure("dim",  foreground="#888888")

    def _build_settings_frame(self, parent):
        self._frm_settings = ttk.LabelFrame(parent, text=self._t("frame_settings"),
                                            padding=8)
        self._frm_settings.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self._frm_settings.columnconfigure(0, weight=1)

        row = ttk.Frame(self._frm_settings)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.pp_var = tk.StringVar(value=self.cfg.get("potplayer_path", ""))
        ttk.Entry(row, textvariable=self.pp_var, font=FONT).grid(
            row=0, column=0, sticky="ew", padx=(0, 6))

        self._btn_browse = ttk.Button(row, text=self._t("btn_browse"),
                                      command=self._browse_potplayer)
        self._btn_browse.grid(row=0, column=1, padx=(0, 4))

        self._btn_autodetect = ttk.Button(row, text=self._t("btn_autodetect"),
                                          command=self._auto_find_potplayer_btn)
        self._btn_autodetect.grid(row=0, column=2, padx=(0, 4))

        self._btn_save = ttk.Button(row, text=self._t("btn_save"),
                                    command=self._save_potplayer)
        self._btn_save.grid(row=0, column=3)

    def _build_history_frame(self, parent):
        self._frm_history = ttk.LabelFrame(parent, text=self._t("frame_history"),
                                           padding=6)
        self._frm_history.grid(row=5, column=0, sticky="ew")
        self._frm_history.columnconfigure(0, weight=1)

        ctrl = ttk.Frame(self._frm_history)
        ctrl.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

        self._lbl_history = ttk.Label(ctrl, text=self._t("history_label"), font=FONT)
        self._lbl_history.pack(side="left")

        self._btn_clear_history = ttk.Button(ctrl, text=self._t("btn_clear_history"),
                                             command=self._clear_history)
        self._btn_clear_history.pack(side="right")

        self.history_list = tk.Listbox(self._frm_history, height=4,
                                       font=("Consolas", 8),
                                       selectmode="single", relief="flat",
                                       bg="#fafafa", activestyle="dotbox")
        self.history_list.grid(row=1, column=0, sticky="ew")
        self.history_list.bind("<Double-Button-1>", self._history_open)

        hsb = ttk.Scrollbar(self._frm_history, orient="horizontal",
                            command=self.history_list.xview)
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
            messagebox.showwarning(self._t("warn_no_url_title"),
                                   self._t("warn_no_url_msg"))
            return

        self._parsed_url = ""
        self._btn_open.config(state="disabled")
        self._btn_copy.config(state="disabled")
        self._btn_parse.config(state="disabled", text=self._t("btn_parsing"))
        self.quality_combo.config(state="disabled")
        self._log_info(self._t("log_parsing").format(url))

        def worker():
            qualities, err = get_qualities(url)
            self.root.after(0, self._on_parse_done, url, qualities, err)

        threading.Thread(target=worker, daemon=True).start()

    def _on_parse_done(self, url, qualities, err):
        self._btn_parse.config(state="normal", text=self._t("btn_parse"))
        if err and not qualities:
            self._log_err(self._t("log_parse_fail").format(err))
            messagebox.showerror(self._t("err_parse_title"), err)
            return

        if err:
            self._log_info(self._t("log_parse_hint").format(err))

        self._qualities = qualities
        self.quality_combo["values"] = qualities
        self.quality_combo.set(qualities[0])
        self.quality_combo.config(state="readonly")
        self._parsed_url = url
        self._btn_open.config(state="normal")
        self._btn_copy.config(state="normal")
        self._log_ok(self._t("log_parse_ok").format(len(qualities), ", ".join(qualities)))

    # ─── 打开播放器 ──────────────────────────────────────────────────────────

    def _do_open(self):
        if not self._parsed_url:
            return
        quality = self.quality_var.get()
        pp_path = self.pp_var.get().strip()
        referer = self.referer_var.get().strip()

        self._btn_open.config(state="disabled", text=self._t("btn_opening"))
        self._log_info(self._t("log_fetching").format(quality))

        def worker():
            url, err = get_stream_url(self._parsed_url, quality)
            self.root.after(0, self._on_get_url_done, url, err, quality, pp_path, referer)

        threading.Thread(target=worker, daemon=True).start()

    def _on_get_url_done(self, stream_url, err, quality, pp_path, referer=""):
        self._btn_open.config(state="normal", text=self._t("btn_open"))
        if err or not stream_url:
            self._log_err(self._t("log_get_fail").format(err))
            messagebox.showerror(self._t("err_open_title"),
                                 err or self._t("err_open_no_url"))
            return

        self._log_info(self._t("log_stream_url").format(
            stream_url[:80] + ("…" if len(stream_url) > 80 else "")))
        if referer:
            self._log_info(self._t("log_referer_used").format(referer))
        ok, msg = open_stream(pp_path, stream_url, referer)
        if ok:
            self._log_ok(msg)
            self._add_history(self._parsed_url, quality)
        else:
            self._log_err(msg)
            messagebox.showerror(self._t("err_start_title"), msg)

    # ─── 复制流地址 ──────────────────────────────────────────────────────────

    def _do_copy(self):
        if not self._parsed_url:
            return
        quality = self.quality_var.get()
        self._btn_copy.config(state="disabled", text=self._t("btn_copying"))

        def worker():
            url, err = get_stream_url(self._parsed_url, quality)
            self.root.after(0, self._on_copy_done, url, err)

        threading.Thread(target=worker, daemon=True).start()

    def _on_copy_done(self, stream_url, err):
        self._btn_copy.config(state="normal", text=self._t("btn_copy"))
        if err or not stream_url:
            self._log_err(self._t("log_copy_fail").format(err))
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(stream_url)
            self._log_ok(self._t("log_copied"))
        except Exception as e:
            self._log_err(self._t("log_copy_err").format(e))

    # ─── PotPlayer 设置 ──────────────────────────────────────────────────────

    def _browse_potplayer(self):
        path = filedialog.askopenfilename(
            title=self._t("dlg_browse_pp"),
            filetypes=[(self._t("dlg_filter_exe"), "*.exe"),
                       (self._t("dlg_filter_all"), "*.*")],
            initialdir=r"C:\Program Files",
        )
        if path:
            self.pp_var.set(path)

    def _auto_referer(self):
        url = self.url_var.get().strip()
        if not url:
            self._log_err(self._t("log_no_url_referer"))
            return
        try:
            p = urlparse(url if url.startswith("http") else "https://" + url)
            referer = f"{p.scheme}://{p.netloc}/"
            self.referer_var.set(referer)
            self._log_info(self._t("log_referer_ok").format(referer))
        except Exception:
            self._log_err(self._t("log_referer_fail"))

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
            self._log_ok(self._t("log_pp_found").format(found))
        else:
            self._log_err(self._t("log_pp_not_found"))

    def _save_potplayer(self):
        path = self.pp_var.get().strip()
        self.cfg["potplayer_path"] = path
        save_config(self.cfg)
        label = path if path else self._t("log_pp_cleared")
        self._log_ok(self._t("log_pp_saved").format(label))

    # ─── 历史记录 ────────────────────────────────────────────────────────────

    def _load_history(self):
        self.history_list.delete(0, "end")
        for item in reversed(self.cfg.get("history", [])):
            ts  = item.get("time", "")
            url = item.get("url", "")
            q   = item.get("quality", "")
            self.history_list.insert("end", f"[{ts}] [{q}]  {url}")

    def _add_history(self, url: str, quality: str):
        history = self.cfg.get("history", [])
        entry = {"url": url, "quality": quality,
                 "time": datetime.now().strftime("%m-%d %H:%M")}
        history.append(entry)
        max_h = self.cfg.get("max_history", 50)
        self.cfg["history"] = history[-max_h:]
        save_config(self.cfg)
        self._load_history()

    def _clear_history(self):
        if messagebox.askyesno(self._t("confirm_clear_title"),
                               self._t("confirm_clear_msg")):
            self.cfg["history"] = []
            save_config(self.cfg)
            self._load_history()
            self._log_info(self._t("log_history_cleared"))

    def _history_open(self, _event=None):
        sel = self.history_list.curselection()
        if not sel:
            return
        line = self.history_list.get(sel[0])
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
        w  = self.root.winfo_width()
        h  = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        geo = self.cfg.get("window_geometry", "750x600")
        try:
            geo = self.root.geometry().split("+")[0]
        except Exception:
            pass
        self.cfg["window_geometry"] = geo
        save_config(self.cfg)
        self.root.destroy()
