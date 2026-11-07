"""Compute robust foreground-use baselines from daily usage."""

import os
import sqlite3
import statistics
from contextlib import closing
from pathlib import Path


MINIMUM_DAYS = 5


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def get_baseline(process_name, window_days=7, database_path=None):
    """Return the median and MAD for at least five recent foreground-use days."""
    database_path = Path(database_path) if database_path else get_database_path()
    if window_days < MINIMUM_DAYS:
        return None, None

    with closing(sqlite3.connect(database_path)) as connection:
        setting = connection.execute(
            """
            SELECT excluded FROM app_settings WHERE process_name = ?
            """,
            (process_name,),
        ).fetchone()
        if setting and setting[0]:
            return None, None

        rows = connection.execute(
            """
            SELECT fg_minutes FROM daily_usage
            WHERE process_name = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (process_name, window_days),
        ).fetchall()

    values = [float(row[0]) for row in rows]
    if len(values) < MINIMUM_DAYS:
        return None, None

    median = statistics.median(values)
    mad = statistics.median(abs(value - median) for value in values)
    return median, mad


def is_above_baseline(today_minutes, baseline, threshold=3.5):
    """Report an anomaly only when a robust z-score crosses the threshold."""
    median, mad = baseline
    if median is None or mad is None or mad == 0:
        return False

    robust_z_score = 0.6745 * (today_minutes - median) / mad
    return robust_z_score > threshold
