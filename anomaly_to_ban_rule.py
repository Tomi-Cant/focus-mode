"""
Convert an anomaly detection result into a ban rule and queue it in the
pending_changes table.

Usage:
    python anomaly_to_ban_rule.py
"""

import json
import os
import sqlite3
from datetime import datetime

# ---- Config (adjust to match your app) -------------------------------------
DB_PATH = os.path.join(os.environ.get("LOCALAPPDATA", "."), "FocusUp", "focusup.db")

# Assumptions about the anomaly data (change if they don't match):
#   - baseline = [mean, std] of daily usage, in MINUTES
#   - allowed time for the rule = the baseline mean
ALLOWED_TIME_FROM_BASELINE = lambda baseline: int(baseline[0])
WARNING_TIMES = [10, 5, 1]       # minutes before the limit hits
ON_FINISH = "close_program"      # what happens when time runs out
ON_START = "none"                # what happens when the program starts
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6] # 0 = Monday ... 6 = Sunday


# ---- Conversion ------------------------------------------------------------
def active_hours(histogram):
    """Return the sorted list of hours (ints) where the program was ever used."""
    return sorted(int(h) for h, count in histogram.items() if count > 0)


def anomaly_to_rule(anomaly):
    """anomaly is a tuple: (program, kind, details_dict)."""
    program, kind, details = anomaly

    hours = active_hours(details["time_of_day_histogram"])
    allowed_minutes = ALLOWED_TIME_FROM_BASELINE(details["baseline"])

    # Window = first active hour -> end of the last active hour
    start_time = f"{hours[0]:02d}:00" if hours else "00:00"
    end_time = f"{hours[-1]:02d}:59" if hours else "23:59"

    return {
        "name": f"Auto: {program} {kind.replace('_', ' ')}",
        "program": program,
        "start_time": start_time,
        "end_time": end_time,
        "days": json.dumps(ALL_DAYS),
        # games/entertainment are not productive; anything else, assume productive
        "productive": 0 if details.get("category") == "game" else 1,
        "select_type": "time",               # limit by total time rather than by hours
        "allowed_hours": json.dumps(hours),
        "time_left": allowed_minutes,        # starts full
        "on_finish": ON_FINISH,
        "enabled": 1,
        "alowed_time": allowed_minutes,      # spelled as in your schema
        "on_start": ON_START,
        "converted": 1,                      # 1 = created from an anomaly, not by hand
        "warning_times": json.dumps(WARNING_TIMES),
    }


# ---- Pending changes table -------------------------------------------------
def ensure_pending_table(conn):
    # If you already have this table, this does nothing.
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_changes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            change_type TEXT NOT NULL,
            payload     TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL
        )
        """
    )


def add_to_pending(conn, rule):
    cur = conn.execute(
        "INSERT INTO pending_changes (change_type, payload, status, created_at) "
        "VALUES (?, ?, 'pending', ?)",
        ("add_ban_rule", json.dumps(rule), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return cur.lastrowid


# ---- Main ------------------------------------------------------------------
if __name__ == "__main__":
    anomaly = (
        "Minecraft.Windows.exe",
        "usage_limit",
        {
            "score": 800.5,
            "baseline": [301.0, 141.0],
            "time_of_day_histogram": {
                "0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0,
                "7": 0, "8": 0, "9": 0, "10": 4, "11": 12, "12": 78,
                "13": 372, "14": 372, "15": 372, "16": 372, "17": 330,
                "18": 48, "19": 372, "20": 372, "21": 372, "22": 372,
                "23": 312,
            },
            "category": "game",
        },
    )

    rule = anomaly_to_rule(anomaly)
    print(json.dumps(rule, indent=2))

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        ensure_pending_table(conn)
        row_id = add_to_pending(conn, rule)
    print(f"Queued in pending_changes as id {row_id}")
