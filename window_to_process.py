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


def _normalize_title(title):
    return "-".join(str(title).split()).casefold()


def _normalize_process_name(name):
    basename = os.path.basename(str(name).replace("\\", "/")).casefold()
    if basename.endswith(".exe"):
        basename = basename[:-4]
    return "".join(character for character in basename if character.isalnum())


def window_matches_targets(title, hwnd, targets):
    target_titles = {_normalize_title(target) for target in targets}
    if _normalize_title(title) in target_titles:
        return True

    target_processes = {_normalize_process_name(target) for target in targets}
    target_processes.discard("")
    if not target_processes:
        return False

    process = get_window_process(hwnd)
    if process is None:
        return False
    try:
        return _normalize_process_name(process.name()) in target_processes
    except psutil.Error:
        return False


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
    try:
        raw_id = str(hwnd).strip()
        window_id = int(raw_id, 16) if raw_id.lower().startswith("0x") else int(raw_id, 10)
        if window_id < 0:
            return False
        wmctrl_id = hex(window_id)
    except (TypeError, ValueError):
        return False
    if shutil.which("wmctrl") is None:
        return False
    try:
        result = subprocess.run(
            ["wmctrl", "-ic", wmctrl_id],
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
    target_titles = {_normalize_title(title) for title in window_titles}
    target_processes = {_normalize_process_name(name) for name in window_titles}
    target_processes.discard("")
    for w in windows:
        if (
            _normalize_title(w.get("title", "")) in target_titles
            or _normalize_process_name(w.get("name", "")) in target_processes
        ):
            processes.append(w)
    return processes


def process_search(executable_file_names: list[str]):
    def normalize_name(name):
        return os.path.basename(str(name).replace("\\", "/")).casefold()

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
