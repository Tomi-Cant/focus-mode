# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import win32gui
import win32con
import win32process
import psutil


def get_window_process(hwnd):
    """Return psutil.Process for a given window handle, or None."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid)
    except psutil.NoSuchProcess:
        return None


def is_taskbar_window(hwnd):
    """Check if a window should appear in the taskbar."""
    if not win32gui.IsWindowVisible(hwnd):
        return False
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):  # owned = not in taskbar
        return False
    if not win32gui.GetWindowText(hwnd):  # no title
        return False

    exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if exstyle & win32con.WS_EX_TOOLWINDOW:  # tool windows are excluded
        return False

    return True


def enum_taskbar_windows():
    windows = []

    def callback(hwnd, _):
        if is_taskbar_window(hwnd):
            proc = get_window_process(hwnd)
            if proc:
                windows.append({
                    "hwnd": hwnd,
                    "title": win32gui.GetWindowText(hwnd),
                    "pid": proc.pid,
                    "name": proc.name()
                })
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def check_windows(window_titles: list[str]):
    matching_titles = {title.casefold() for title in window_titles}
    return [
        window
        for window in enum_taskbar_windows()
        if window["title"].casefold() in matching_titles
    ]


def process_search(executable_file_names: list[str]):
    matching_names = {name.casefold() for name in executable_file_names}
    for proc in psutil.process_iter(['name']):
        process_name = proc.info.get('name')
        if process_name and process_name.casefold() in matching_names:
            yield proc
