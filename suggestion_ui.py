"""Tkinter UI for reviewing generated Focused Up suggestions."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from manual_buffer import queue_change


_shown_dates = set()


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
            LIMIT 1
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
    return "Would you like Focused Up to help limit usage of %s?" % process_name


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
