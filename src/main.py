import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk

from gui import LiveStreamApp


def main():
    root = tk.Tk()
    # 使用系统原生主题（Windows Vista+）
    style = ttk.Style()
    for theme in ("vista", "winnative", "clam"):
        if theme in style.theme_names():
            style.theme_use(theme)
            break

    app = LiveStreamApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
