"""Background integration for usage sampling, aggregation, and suggestions."""

import sqlite3
import threading
import time
import argparse
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from aggregate import aggregate_day
from bans import adjust_bans_weekly, check_ban, finalize_ban_window
from categories import get_category
from db import get_database_path
from sampler import sample_once
from suggest import apply_usage_config, generate_suggestions


def log_crash(database_path, message):
    log_path = Path(database_path).parent / "crash.log"
    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write("%s usage scheduler: %s\n" %
                      (datetime.now().astimezone().isoformat(), message))
    except OSError:
        pass


def _last_weekly_adjustment(database_path):
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT value_json FROM app_config
            WHERE source = 'config' AND config_key = 'last_weekly_ban_adjustment'
            """
        ).fetchone()
    if not row:
        return None
    return row[0].strip('"')


def _record_weekly_adjustment(database_path, date):
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO app_config (source, config_key, value_json)
            VALUES ('config', 'last_weekly_ban_adjustment', ?)
            ON CONFLICT(source, config_key)
            DO UPDATE SET value_json = excluded.value_json
            """,
            ('"%s"' % date,),
        )
        connection.commit()


def run_usage_scheduler(config, database_path=None, stop_event=None, sleep=time.sleep):
    """Run one usage-data pass on the sampler interval."""
    database_path = Path(database_path) if database_path else get_database_path()
    stop_event = stop_event or threading.Event()
    apply_usage_config(config)
    interval = max(1, int(config.get("sample_interval_seconds", 10)))
    idle_threshold = max(0, int(config.get("idle_threshold_seconds", 60)))
    current_date = None
    previous_hour = datetime.now().astimezone().hour

    while not stop_event.is_set():
        try:
            sample_once(
                database_path,
                snapshot_gui=(int(time.monotonic()) % 300 < interval),
                idle_threshold=idle_threshold,
            )

            now = datetime.now().astimezone()
            with closing(sqlite3.connect(database_path)) as connection:
                connection.row_factory = sqlite3.Row
                daily_usage_exists = connection.execute(
                    """
                    SELECT 1 FROM sqlite_master
                    WHERE type = 'table' AND name = 'daily_usage'
                    """
                ).fetchone()
                active_processes = (
                    [
                        row["process_name"]
                        for row in connection.execute(
                            """
                            SELECT DISTINCT process_name
                            FROM daily_usage
                            WHERE date = ?
                            """,
                            (now.date().isoformat(),),
                        ).fetchall()
                    ]
                    if daily_usage_exists else []
                )
            for process_name in active_processes:
                if get_category(process_name, database_path=database_path) != "uncategorized":
                    check_ban(process_name, now=now, database_path=database_path)

            today = datetime.now().date()
            if current_date != today.isoformat():
                if current_date is not None:
                    aggregate_day(current_date, database_path=database_path)
                aggregate_day(today.isoformat(), database_path=database_path)
                generate_suggestions(database_path=database_path, date=today.isoformat())
                current_date = today.isoformat()

            if today.weekday() == 0:
                last_adjustment = _last_weekly_adjustment(database_path)
                if last_adjustment != today.isoformat():
                    adjust_bans_weekly(database_path=database_path)
                    _record_weekly_adjustment(database_path, today.isoformat())
            current_hour = datetime.now().astimezone().hour
            if current_hour != previous_hour:
                import manual_buffer

                with closing(sqlite3.connect(database_path)) as connection:
                    rules = connection.execute(
                        """
                        SELECT name, end_time FROM ban_rules
                        WHERE CAST(substr(end_time, 1, 2) AS INTEGER) = ?
                        """,
                        (current_hour,),
                    ).fetchall()
                for rule in rules:
                    finalize_ban_window(
                        rule["name"],
                        now=datetime.now().astimezone(),
                        database_path=database_path,
                    )
                previous_hour = current_hour
        except Exception as error:
            log_crash(database_path, str(error))
        stop_event.wait(interval)


def start_usage_scheduler(config, database_path=None):
    stop_event = threading.Event()
    thread = threading.Thread(
        target=run_usage_scheduler,
        args=(config, database_path, stop_event),
        name="FocusUpUsageScheduler",
        daemon=True,
    )
    thread.start()
    return thread, stop_event


def run_usage_scheduler_once(database_path=None):
    """Run aggregation and suggestion maintenance once for the current day."""
    database_path = Path(database_path) if database_path else get_database_path()
    today = datetime.now().date()
    aggregate_day(today.isoformat(), database_path=database_path)
    generate_suggestions(database_path=database_path, date=today.isoformat())

    if today.weekday() == 0:
        if _last_weekly_adjustment(database_path) != today.isoformat():
            adjust_bans_weekly(database_path=database_path)
            _record_weekly_adjustment(database_path, today.isoformat())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        run_usage_scheduler_once()
