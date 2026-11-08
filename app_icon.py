import sys
import tkinter as tk
from pathlib import Path
import os.path as paths


def get_icon_path():
    candidates = (
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        / "focused_up_logo.ico",
        Path(__file__).resolve().parent / "focused_up_logo.ico",
        Path.cwd() / "focused_up_logo.ico",
        Path(paths.join(paths.abspath(paths.dirname(paths.dirname(sys.executable))) + "\\focused_up_logo.ico"))
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def apply(window):
    if window is None:
        return False
    icon_path = get_icon_path()
    if icon_path is None:
        return False
    try:
        window.iconbitmap(default=str(icon_path))
        return True
    except (tk.TclError, OSError):
        return False
