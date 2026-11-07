"""Collect foreground and visible-window samples on Windows."""

import ctypes
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing

import psutil
import win32gui
import win32process

from window_to_process import enum_taskbar_windows


SAMPLE_INTERVAL_SECONDS = 10
GUI_SNAPSHOT_INTERVAL_SECONDS = 300
IDLE_SECONDS = 60
SAMPLER_MUTEX_NAME = "Local\\FocusedUpSamplerSingleInstance"
HEARTBEAT_MAX_AGE_SECONDS = 180


def acquire_sampler_mutex():
    handle = ctypes.windll.kernel32.CreateMutexW(None, True, SAMPLER_MUTEX_NAME)
    if not handle or ctypes.windll.kernel32.GetLastError() == 183:
        return None
    return handle


def heartbeat(database_path=None):
    database_path = Path(database_path) if database_path else get_database_path()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sampler_heartbeat (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                ts TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO sampler_heartbeat (id, ts) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET ts = excluded.ts
            """,
            (timestamp,),
        )
        connection.commit()
    return timestamp

# Sampled product names use these executable basenames. Filtering every process
# at collection time keeps background noise out of both focused and open-app usage.
EXCLUDED_PROCESS_NAMES = {
    "applemusic.exe",
    "brave.exe",
    "chrome.exe",
    "chromium.exe",
    "firefox.exe",
    "msedge.exe",
    "opera.exe",
    "operagx.exe",
    "safari.exe",
    "spotify.exe",
    "vivaldi.exe",
}


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_database_path():
    local_app_data = os.environ["LOCALAPPDATA"]
    return Path(local_app_data) / "Focused Up" / "usage.db"


def get_idle_seconds():
    """Return seconds since the last user input."""
    info = _LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(_LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        raise ctypes.WinError()

    tick_count = ctypes.windll.kernel32.GetTickCount()
    elapsed = (tick_count - info.dwTime) & 0xFFFFFFFF
    return elapsed / 1000.0


def get_foreground_process_name():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None

    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
    if not process_id:
        return None

    try:
        process_name = psutil.Process(process_id).name()
        if should_exclude_process(process_name):
            return None
        return process_name
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def should_exclude_process(process_name):
    if not process_name:
        return False
    return process_name.strip().casefold() in EXCLUDED_PROCESS_NAMES


def insert_sample(database_path, process_name, is_foreground, idle=False):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO samples (ts, process_name, is_foreground, idle)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp, process_name, int(is_foreground), int(idle)),
        )
        connection.commit()


def sample_once(database_path=None, snapshot_gui=False, idle_threshold=IDLE_SECONDS):
    """Collect one foreground sample and optionally a visible-window snapshot."""
    database_path = Path(database_path) if database_path else get_database_path()
    try:
        idle_seconds = get_idle_seconds()
        if idle_seconds >= idle_threshold:
            return

        process_name = get_foreground_process_name()
        if process_name:
            insert_sample(database_path, process_name, True)

        if snapshot_gui:
            seen = set()
            for window in enum_taskbar_windows():
                name = window["name"]
                if name and not should_exclude_process(name) and name not in seen:
                    seen.add(name)
                    insert_sample(database_path, name, False)
    except Exception as error:
        log_path = database_path.parent / "crash.log"
        try:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(
                    "%s sampler error: %s\n"
                    % (datetime.now(timezone.utc).isoformat(), error)
                )
        except OSError:
            pass


def run_sampler(database_path=None, sleep=time.sleep, idle_threshold=IDLE_SECONDS,
                 sample_interval=SAMPLE_INTERVAL_SECONDS):
    """Run until stopped by the process."""
    database_path = Path(database_path) if database_path else get_database_path()
    next_gui_snapshot = 0.0
    mutex = acquire_sampler_mutex()
    if mutex is None:
        return

    while True:
        now = time.monotonic()
        snapshot_gui = now >= next_gui_snapshot
        if snapshot_gui:
            next_gui_snapshot = now + GUI_SNAPSHOT_INTERVAL_SECONDS

        sample_once(database_path, snapshot_gui=snapshot_gui,
                    idle_threshold=idle_threshold)
        heartbeat(database_path)
        sleep(sample_interval)


if __name__ == "__main__":
    run_sampler()
