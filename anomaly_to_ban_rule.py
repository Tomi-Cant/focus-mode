"""
Read ACCEPTED usage_limit suggestions, convert each one into a ban rule,
and queue it in the pending_changes table.

Usage:
    python anomaly_to_ban_rule.py            # convert all accepted usage_limit suggestions
    python anomaly_to_ban_rule.py 12         # convert only suggestion id 12 (any outcome, handy for testing)

Set FOCUSUP_DB to point at a different database file (e.g. a copy for testing).
"""

import json
import os
import sqlite3
import sys

# ---- Config -----------------------------------------------------------------
DB_PATH = os.environ.get("FOCUSUP_DB") or os.path.join(
    os.environ.get("LOCALAPPDATA", "."), "Focused Up", "usage.db"
)

# Assumptions about the data (check these against how your app reads them):
#   - baseline = [mean, std] of daily usage, in MINUTES
#   - allowed time for the rule = the baseline mean
ALLOWED_TIME_FROM_BASELINE = lambda baseline: float(baseline[0])
WARNING_TIMES = [600, 300, 60]   # SECONDS before the limit (your app stores seconds)
ON_FINISH = 0                   # pending_changes only allows 0 or 1
ON_START = 0                     # 0 or 1 as well
SELECT_TYPE = "Queue"             # existing rule uses "Queue"; set to whatever your app expects
ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]   # your app stores day NAMES


# ---- Reading suggestions ----------------------------------------------------
def fetch_suggestions(conn, suggestion_id=None):
    """Return a list of (id, process_name, type, features_dict, display_name)."""
    base = (
        "SELECT s.id, s.process_name, s.type, s.features_json, "
        "       COALESCE(n.display_name, s.process_name) "
        "FROM suggestions s "
        "LEFT JOIN app_names n ON lower(n.process_name) = lower(s.process_name) "
    )
    if suggestion_id is not None:
        rows = conn.execute(base + "WHERE s.id = ?", (suggestion_id,)).fetchall()
    else:
        rows = conn.execute(
            base + "WHERE s.type = 'usage_limit' AND s.outcome = 'accepted'"
        ).fetchall()

    return [(sid, proc, kind, json.loads(features or "{}"), display)
            for sid, proc, kind, features, display in rows]


# ---- Conversion -------------------------------------------------------------
def active_hours(histogram):
    """Sorted list of hours (ints) where the program was ever used."""
    return sorted(int(h) for h, count in histogram.items() if count > 0)


def suggestion_to_rule(display_name, kind, details):
    hours = active_hours(details.get("time_of_day_histogram", {}))
    allowed_minutes = ALLOWED_TIME_FROM_BASELINE(details["baseline"])

    # Window = first active hour -> end of the last active hour
    start_time = f"{hours[0]:02d}:00" if hours else "00:00"
    end_time = f"{hours[-1]:02d}:59" if hours else "23:59"

    return {
        "name": f"Auto: {display_name} {kind.replace('_', ' ')}",
        "program": [display_name],           # app stores a list of display names
        "start_time": start_time,
        "end_time": end_time,
        "days": ALL_DAYS,
        "productive": [],                    # your app uses a list here, not 0/1
        "select_type": SELECT_TYPE,
        "allowed_hours": 0.0,                # REAL column; unused for a time-based rule
        "time_left": allowed_minutes,        # starts full
        "on_finish": ON_FINISH,
        "enabled": 1,
        "alowed_time": allowed_minutes,      # spelled as in your schema
        "on_start": ON_START,
        "converted": [],
        "warning_times": WARNING_TIMES,
    }


# ---- Pending changes --------------------------------------------------------
def rule_exists(conn, name):
    for table in ("pending_changes", "ban_rules"):
        if conn.execute(f"SELECT 1 FROM {table} WHERE name = ?", (name,)).fetchone():
            return True
    return False


def add_to_pending(conn, rule, op="add", old_name=None):
    conn.execute(
        """
        INSERT INTO pending_changes (
            name, program, start_time, end_time, days, productive,
            select_type, allowed_hours, time_left, on_finish, enabled,
            alowed_time, on_start, converted, warning_times
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rule["name"],
            json.dumps(rule["program"]),
            rule["start_time"],
            rule["end_time"],
            json.dumps(rule["days"]),
            json.dumps(rule["productive"]),
            rule["select_type"],
            rule["allowed_hours"],
            rule["time_left"],
            rule["on_finish"],
            rule["enabled"],
            rule["alowed_time"],
            rule["on_start"],
            json.dumps(rule["converted"]),
            json.dumps(rule["warning_times"]),
        ),
    )
    return rule["name"]


def queue_from_suggestion(suggestion, display_name=None, database_path=None):
    """Queue ONE accepted suggestion (the dict the UI already has) into pending_changes.

    Works from the dict, not the suggestions table, because accepting a suggestion
    deletes its row. Returns the rule name, or None if nothing was queued (not a
    usage_limit suggestion, no baseline, or a rule with that name already exists).
    """
    if suggestion.get("type") != "usage_limit":   # e.g. category_time_window_ban
        return None
    try:
        details = json.loads(suggestion.get("features_json") or "{}")
    except (TypeError, json.JSONDecodeError):
        return None
    if "baseline" not in details:
        return None

    display = display_name or suggestion["process_name"]
    rule = suggestion_to_rule(display, suggestion["type"], details)

    conn = sqlite3.connect(database_path or DB_PATH)
    try:
        with conn:  # commits on success, rolls back on error
            if rule_exists(conn, rule["name"]):
                return None
            return add_to_pending(conn, rule)
    finally:
        conn.close()


# ---- Main -------------------------------------------------------------------
if __name__ == "__main__":
    only_id = int(sys.argv[1]) if len(sys.argv) > 1 else None

    # 'with' commits on success and rolls back if anything fails
    with sqlite3.connect(DB_PATH) as conn:
        suggestions = fetch_suggestions(conn, only_id)

        if not suggestions:
            print("No suggestions to convert.")

        for sid, process_name, kind, details, display in suggestions:
            rule = suggestion_to_rule(display, kind, details)
            if rule_exists(conn, rule["name"]):
                print(f"Suggestion {sid} ({display}) skipped: '{rule['name']}' already exists")
                continue
            name = add_to_pending(conn, rule)
            print(f"Suggestion {sid} ({display}) -> pending_changes '{name}'")