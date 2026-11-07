"""Tkinter UI for reviewing generated Focused Up suggestions."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from manual_buffer import queue_change


_shown_dates = set()

_APP_NAME_FALLBACKS = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "firefox.exe": "Mozilla Firefox",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "steam.exe": "Steam",
    "excel.exe": "Microsoft Excel",
    "winword.exe": "Microsoft Word",
    "powerpnt.exe": "Microsoft PowerPoint",
    "code.exe": "Visual Studio Code",
    "outlook.exe": "Microsoft Outlook",
    "teams.exe": "Microsoft Teams",
    "vlc.exe": "VLC Media Player",
}


def application_display_name(process_name, database_path=None):
    normalized_name = str(process_name).strip().casefold()
    database_path = Path(database_path) if database_path else get_database_path()

    try:
        with closing(sqlite3.connect(database_path)) as connection:
            row = connection.execute(
                """
                SELECT display_name
                FROM app_names
                WHERE process_name = ?
                """,
                (normalized_name,),
            ).fetchone()
    except sqlite3.OperationalError:
        row = None
    if row and row[0]:
        return str(row[0])

    display_name = _APP_NAME_FALLBACKS.get(normalized_name)
    if display_name is None:
        try:
            import psutil

            for process in psutil.process_iter(["name", "exe"]):
                info = process.info
                if str(info.get("name") or "").casefold() != normalized_name:
                    continue
                executable = info.get("exe")
                if executable:
                    try:
                        import win32api

                        display_name = win32api.GetFileVersionInfo(
                            executable,
                            "\\StringFileInfo\\040904b0\\FileDescription",
                        )
                    except Exception:
                        display_name = None
                if display_name:
                    break
        except Exception:
            pass

    display_name = str(display_name or normalized_name.removesuffix(".exe")).strip()
    if display_name:
        display_name = " ".join(part.capitalize() for part in display_name.split())
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(database_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_names (
                    process_name TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    updated_ts TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO app_names (process_name, display_name, updated_ts)
                VALUES (?, ?, ?)
                ON CONFLICT(process_name) DO UPDATE SET
                    display_name = excluded.display_name,
                    updated_ts = excluded.updated_ts
                """,
                (
                    normalized_name,
                    display_name,
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )
            connection.commit()
    except sqlite3.Error:
        pass
    return display_name or normalized_name


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def is_fullscreen_foreground():
    """Return True when the foreground window fills the primary display."""
    try:
        import win32api
        import win32gui

        window = win32gui.GetForegroundWindow()
        left, top, right, bottom = win32gui.GetWindowRect(window)
        work_area = win32api.GetMonitorInfo(win32api.MonitorFromWindow(window))[2]
        monitor = win32api.GetMonitorInfo(win32api.MonitorFromWindow(window))[1]
        fills_monitor = (left, top, right, bottom) == monitor
        return fills_monitor and (left, top, right, bottom) != work_area
    except Exception:
        # Window APIs are unavailable in test hosts and headless builds; this only
        # prevents opening a dialog instead of risking a crash in the UI loop.
        return False


def _pending_suggestions(database_path=None):
    database_path = Path(database_path) if database_path else get_database_path()
    today = datetime.now().date().isoformat()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, ts, process_name, type, features_json, outcome
            FROM suggestions
            WHERE substr(ts, 1, 10) = ? AND outcome = 'pending'
            ORDER BY id DESC
            """,
            (today,),
        ).fetchall()
    return [dict(row) for row in rows]


def set_suggestion_outcome(suggestion, outcome, database_path=None):
    """Record an outcome and snooze the process for a three-day ignore."""
    if outcome not in {"accepted", "dismissed", "snoozed"}:
        raise ValueError("Invalid suggestion outcome: %s" % outcome)

    queue_change(
        "suggestions",
        "set",
        suggestion["id"],
        {"outcome": outcome},
        database_path=database_path,
    )
    if outcome == "snoozed":
        snooze_until = (
            datetime.now(timezone.utc) + timedelta(days=3)
        ).isoformat(timespec="seconds")
        queue_change(
            "app_settings",
            "set",
            suggestion["process_name"],
            {
                "process_name": suggestion["process_name"],
                "snooze_until": snooze_until,
            },
            database_path=database_path,
        )


def suggestion_text(suggestion):
    process_name = suggestion["process_name"]
    if suggestion["type"] == "category_time_window_ban":
        return "Would you like Focused Up to set a time-window ban for the game category?"
    return "Would you like Focused Up to help limit usage of %s?" % application_display_name(
        process_name
    )


def show_suggestion(parent=None, database_path=None, standalone=False):
    """Show at most one pending suggestion per local day when it is safe."""
    import tkinter as tk
    from tkinter import ttk

    database_path = Path(database_path) if database_path else get_database_path()
    today = datetime.now().date().isoformat()
    if today in _shown_dates or is_fullscreen_foreground():
        return False

    suggestions = _pending_suggestions(database_path)
    if not suggestions:
        return False
    suggestion = suggestions[0]

    if standalone:
        window = parent if parent is not None else tk.Tk()
        window.deiconify()
    else:
        window = tk.Toplevel(parent) if parent is not None else tk.Toplevel()
    window.title("Focus suggestion")
    if not standalone:
        window.transient(parent if parent is not None else window.master)
    window.grab_set()
    window.resizable(False, False)

    frame = ttk.Frame(window, padding=16)
    frame.grid(row=0, column=0, sticky="nsew")
    ttk.Label(frame, text=suggestion_text(suggestion), wraplength=360).grid(
        row=0, column=0, columnspan=3, pady=(0, 12)
    )

    def finish(outcome):
        set_suggestion_outcome(suggestion, outcome, database_path)
        window.destroy()

    ttk.Button(frame, text="Accept", command=lambda: finish("accepted")).grid(
        row=1, column=0, padx=4
    )
    ttk.Button(frame, text="Dismiss", command=lambda: finish("dismissed")).grid(
        row=1, column=1, padx=4
    )
    ttk.Button(frame, text="Ignore 3 days", command=lambda: finish("snoozed")).grid(
        row=1, column=2, padx=4
    )

    _shown_dates.add(today)
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry("+%d+%d" % (x, y))
    window.focus_set()
    return True


if __name__ == "__main__":
    import tkinter as tk

    root = tk.Tk()
    
    shown = show_suggestion(root, standalone=True)
    print("Suggestion shown:", shown, flush=True)
    if shown:
        root.mainloop()
    else:
        root.destroy()
