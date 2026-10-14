# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import os
import shutil
import subprocess

import psutil

def get_window_process(hwnd):
    """Return psutil.Process for a given window handle, or None."""
    try:
        result = subprocess.run(
            ["xdotool", "getwindowpid", str(hwnd)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        pid = int(result.stdout.strip())
        return psutil.Process(pid)
    except (OSError, ValueError, psutil.Error):
        return None


def enum_taskbar_windows():
    if shutil.which("wmctrl") is None:
        return []
    try:
        result = subprocess.run(
            ["wmctrl", "-lp"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    windows = []
    if result.returncode != 0:
        return windows
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=4)
        if len(fields) < 5:
            continue
        try:
            pid = int(fields[2])
            process = psutil.Process(pid)
            windows.append({
                "hwnd": fields[0],
                "title": fields[4],
                "pid": pid,
                "name": process.name(),
            })
        except (ValueError, psutil.Error):
            continue
    return windows


def get_active_window():
    """Return the active window title and handle when the desktop exposes them."""
    if shutil.which("xdotool") is None:
        return "", None
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return "", None
        hwnd = result.stdout.strip()
        title = subprocess.run(
            ["xdotool", "getwindowname", hwnd],
            capture_output=True,
            text=True,
            check=False,
        )
        return (title.stdout.strip(), hwnd) if title.returncode == 0 else ("", None)
    except OSError:
        return "", None


def close_window(hwnd):
    """Request a graceful close using the current desktop's window manager."""
    if hwnd is None:
        return False
    if shutil.which("wmctrl") is None:
        return False
    try:
        result = subprocess.run(
            ["wmctrl", "-ic", str(hwnd)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


def check_windows(window_titles: list[str]):
    windows = enum_taskbar_windows()
    processes = []
    target_titles = {title.casefold() for title in window_titles}
    for w in windows:
        if w['title'].casefold() in target_titles:
            processes.append(w)
    return processes


def process_search(executable_file_names: list[str]):
    def normalize_name(name):
        return os.path.basename(str(name)).casefold()

    target_names = {normalize_name(name) for name in executable_file_names}
    for proc in psutil.process_iter(["name", "exe", "cmdline"]):
        try:
            info = proc.info
            candidates = [info.get("name"), info.get("exe")]
            command = info.get("cmdline") or []
            if command:
                candidates.append(command[0])
            if target_names.intersection(
                normalize_name(candidate) for candidate in candidates if candidate
            ):
                yield proc
        except psutil.Error:
            continue
