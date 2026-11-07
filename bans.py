"""Ban-window enforcement and weekly adaptive allowances."""

import ctypes
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

import os

from baseline import get_baseline
from categories import get_category


# Change the starting allowance policy here without editing ban logic.
NEW_BAN_ALLOWANCE_MODE = "baseline"
ATTEMPT_THRESHOLD = 10
ALLOWANCE_FLOOR_MINUTES = 15.0
EASE_PERCENT = 0.10
TIGHTEN_PERCENT = 0.15


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def _connect(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _window_contains_hour(rule, hour):
    start = int(rule["start_hour"])
    end = int(rule["end_hour"])
    if start <= end:
        return start <= hour < end
    return hour >= start or hour < end


def category_baseline(category, database_path=None):
    """Return the median baseline of apps currently used in a category."""
    database_path = Path(database_path) if database_path else get_database_path()
    baselines = []
    with closing(_connect(database_path)) as connection:
        processes = [
            row["process_name"]
            for row in connection.execute(
                "SELECT DISTINCT process_name FROM daily_usage"
            ).fetchall()
        ]

    for process_name in processes:
        if get_category(process_name, database_path=database_path) == category:
            process_baseline, mad = get_baseline(
                process_name, database_path=database_path
            )
            if process_baseline is not None:
                baselines.append(float(process_baseline))
    return median(baselines) if baselines else None


def _used_minutes(category, date, database_path):
    with closing(_connect(database_path)) as connection:
        processes = [
            row["process_name"]
            for row in connection.execute(
                """
                SELECT DISTINCT process_name FROM daily_usage WHERE date = ?
                """,
                (date,),
            ).fetchall()
        ]
        matching = [
            process_name
            for process_name in processes
            if get_category(process_name, database_path=database_path) == category
        ]
        if not matching:
            return 0.0
        placeholders = ",".join("?" for _ in matching)
        row = connection.execute(
            """
            SELECT COALESCE(SUM(fg_minutes), 0)
            FROM daily_usage
            WHERE date = ? AND process_name IN (%s)
            """ % placeholders,
            (date, *matching),
        ).fetchone()
    return float(row[0])


def show_ban_notice(process_name, category):
    """Show a non-blocking Windows notice; callers that host another UI may replace it."""
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            "%s has reached its time allowance for %s today."
            % (process_name, category),
            "Focused Up",
            0x40,
        )
    except Exception:
        # Headless and non-Windows test environments do not have MessageBox.
        return


def check_ban(process_name, now=None, database_path=None):
    """Log and notify when a process is in an exhausted ban window."""
    database_path = Path(database_path) if database_path else get_database_path()
    now = now or datetime.now().astimezone()
    category = get_category(process_name, database_path=database_path)

    with closing(_connect(database_path)) as connection:
        rule = connection.execute(
            """
            SELECT category, start_hour, end_hour, allowed_minutes
            FROM ban_rules WHERE category = ?
            ORDER BY updated_ts DESC LIMIT 1
            """,
            (category,),
        ).fetchone()

    if rule is None or not _window_contains_hour(rule, now.hour):
        return False

    used = _used_minutes(category, now.date().isoformat(), database_path)
    if used < float(rule["allowed_minutes"]):
        return False

    with closing(_connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO ban_attempts (ts, process_name, category)
            VALUES (?, ?, ?)
            """,
            (now.isoformat(timespec="seconds"), process_name, category),
        )
        connection.commit()
    show_ban_notice(process_name, category)
    return True


def create_ban(category, start_hour, end_hour, database_path=None, updated_ts=None):
    """Create a ban whose initial allowance is the category baseline."""
    database_path = Path(database_path) if database_path else get_database_path()
    if NEW_BAN_ALLOWANCE_MODE != "baseline":
        raise ValueError("Unsupported new-ban allowance mode")
    baseline = category_baseline(category, database_path)
    allowance = baseline if baseline is not None else ALLOWANCE_FLOOR_MINUTES
    updated_ts = updated_ts or datetime.now().astimezone().isoformat(timespec="seconds")
    with closing(_connect(database_path)) as connection:
        connection.execute(
            """
            UPDATE ban_rules SET
                start_hour = ?,
                end_hour = ?,
                allowed_minutes = ?,
                updated_ts = ?
            WHERE category = ?
            """,
            (start_hour, end_hour, allowance, updated_ts, category),
        )
        if connection.execute(
            "SELECT changes()"
        ).fetchone()[0] == 0:
            connection.execute(
                """
                INSERT INTO ban_rules
                    (category, start_hour, end_hour, allowed_minutes, updated_ts)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category, start_hour, end_hour, allowance, updated_ts),
            )
        connection.commit()
    return allowance


def adjust_bans_weekly(database_path=None, now=None):
    """Adjust every rule from the previous seven days of ban attempts."""
    database_path = Path(database_path) if database_path else get_database_path()
    now = now or datetime.now().astimezone()
    week_start = (now - timedelta(days=7)).isoformat(timespec="seconds")
    changes = []

    with closing(_connect(database_path)) as connection:
        rules = connection.execute(
            """
            SELECT category, allowed_minutes FROM ban_rules
            """
        ).fetchall()
        for rule in rules:
            category = rule["category"]
            attempts = connection.execute(
                """
                SELECT COUNT(*) FROM ban_attempts
                WHERE category = ? AND ts >= ?
                """,
                (category, week_start),
            ).fetchone()[0]

            baseline = category_baseline(category, database_path)
            ceiling = baseline if baseline is not None else float(rule["allowed_minutes"])
            allowance = float(rule["allowed_minutes"])
            if attempts > ATTEMPT_THRESHOLD:
                allowance *= 1.0 + EASE_PERCENT
            elif attempts == 0:
                allowance *= 1.0 - TIGHTEN_PERCENT

            allowance = max(ALLOWANCE_FLOOR_MINUTES, allowance)
            allowance = min(ceiling, allowance)
            connection.execute(
                """
                UPDATE ban_rules SET allowed_minutes = ?, updated_ts = ?
                WHERE category = ?
                """,
                (allowance, now.isoformat(timespec="seconds"), category),
            )
            changes.append((category, attempts, allowance))
        connection.commit()
    return changes
