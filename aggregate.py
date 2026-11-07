"""Aggregate raw Focused Up samples into daily usage."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path


FOREGROUND_SAMPLE_SECONDS = 10
OPEN_SNAPSHOT_SECONDS = 300


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def _local_date(timestamp):
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    else:
        parsed = parsed.astimezone()
    return parsed.date().isoformat()


def _timestamp_too_old(timestamp, cutoff):
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    else:
        parsed = parsed.astimezone()
    return parsed < cutoff


def aggregate_day(date, database_path=None):
    """Replace usage totals for date without double-counting on reruns."""
    database_path = Path(database_path) if database_path else get_database_path()
    totals = {}

    with closing(sqlite3.connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT ts, process_name, is_foreground FROM samples WHERE idle = 0"
        ).fetchall()
        for timestamp, process_name, is_foreground in rows:
            if _local_date(timestamp) != date:
                continue
            totals.setdefault(process_name, [0.0, 0.0])
            if is_foreground:
                totals[process_name][0] += FOREGROUND_SAMPLE_SECONDS / 60.0
            else:
                totals[process_name][1] += OPEN_SNAPSHOT_SECONDS / 60.0

        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM daily_usage WHERE date = ?", (date,))
        connection.executemany(
            """
            INSERT INTO daily_usage
                (date, process_name, fg_minutes, open_minutes)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    date,
                    process_name,
                    round(foreground, 6),
                    round(opened, 6),
                )
                for process_name, (foreground, opened) in totals.items()
            ],
        )

        cutoff = datetime.now().astimezone() - timedelta(days=7)
        old_rows = connection.execute(
            "SELECT rowid, ts FROM samples"
        ).fetchall()
        connection.executemany(
            "DELETE FROM samples WHERE rowid = ?",
            [
                (row_id,)
                for row_id, timestamp in old_rows
                if _timestamp_too_old(timestamp, cutoff)
            ],
        )
        connection.commit()

    return totals


if __name__ == "__main__":
    aggregate_day(datetime.now().astimezone().date().isoformat())
