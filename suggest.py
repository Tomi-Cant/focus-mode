"""Score today's usage and create focus suggestions."""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from baseline import get_baseline, is_above_baseline
from categories import get_category
from manual_buffer import get_app_setting


W_FG = 1.0
W_OPEN = 0.25
MAX_APP_CANDIDATES = 2

CATEGORY_DAILY_CAPS = {
    "game": 120.0,
    "social": 90.0,
    "video": 120.0,
    "work": 480.0,
    "browser": 180.0,
    "other": 240.0,
}


def apply_usage_config(config):
    """Update scoring weights and category caps from saved application config."""
    global W_FG, W_OPEN
    W_FG = float(config.get("foreground_weight", W_FG))
    W_OPEN = float(config.get("open_weight", W_OPEN))
    saved_caps = config.get("category_caps_minutes", {})
    if isinstance(saved_caps, dict):
        for category, minutes in saved_caps.items():
            CATEGORY_DAILY_CAPS[category] = float(minutes)


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def _connect(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def score_app(process_name, date=None, database_path=None):
    """Score foreground and open minutes for one app on a date."""
    database_path = Path(database_path) if database_path else get_database_path()
    date = date or datetime.now().date().isoformat()
    with closing(_connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT fg_minutes, open_minutes
            FROM daily_usage
            WHERE date = ? AND process_name = ?
            """,
            (date, process_name),
        ).fetchone()
    if row is None:
        return 0.0
    return W_FG * float(row["fg_minutes"]) + W_OPEN * float(row["open_minutes"])


def _is_snoozed(setting):
    snooze_until = setting.get("snooze_until")
    if not snooze_until:
        return False
    try:
        until = datetime.fromisoformat(str(snooze_until).replace("Z", "+00:00"))
        if until.tzinfo is None:
            until = until.astimezone()
        return until.astimezone() > datetime.now().astimezone()
    except (TypeError, ValueError):
        return False


def _time_of_day_histogram(process_name, date, database_path):
    histogram = {str(hour): 0 for hour in range(24)}
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT ts FROM samples
            WHERE process_name = ? AND idle = 0
            """,
            (process_name,),
        ).fetchall()
    for row in rows:
        try:
            timestamp = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.astimezone()
            if timestamp.date().isoformat() == date:
                histogram[str(timestamp.hour)] += 1
        except (TypeError, ValueError):
            continue
    return histogram


def _recently_suggested(database_path, process_name=None, category=None, days=7):
    cutoff = (datetime.now().astimezone() - timedelta(days=days)).isoformat()
    with closing(_connect(database_path)) as connection:
        if category:
            return connection.execute(
                """
                SELECT 1 FROM suggestions
                WHERE process_name = ? AND ts >= ? LIMIT 1
                """,
                (category, cutoff),
            ).fetchone() is not None
        return connection.execute(
            """
            SELECT 1 FROM suggestions
            WHERE process_name = ? AND ts >= ? LIMIT 1
            """,
            (process_name, cutoff),
        ).fetchone() is not None


def generate_suggestions(database_path=None, date=None):
    """Generate at most two app suggestions, plus one category ban when needed."""
    database_path = Path(database_path) if database_path else get_database_path()
    date = date or datetime.now().date().isoformat()
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT process_name, fg_minutes, open_minutes
            FROM daily_usage
            WHERE date = ?
            """,
            (date,),
        ).fetchall()

    flagged = []
    game_apps = []
    for row in rows:
        process_name = row["process_name"]
        setting = get_app_setting(process_name, database_path=database_path)
        if setting.get("excluded") or _is_snoozed(setting):
            continue

        category = get_category(process_name, database_path=database_path)
        score = W_FG * float(row["fg_minutes"]) + W_OPEN * float(row["open_minutes"])
        baseline = get_baseline(
            process_name, database_path=database_path
        )
        over_baseline = is_above_baseline(float(row["fg_minutes"]), baseline)
        over_cap = float(row["fg_minutes"]) >= CATEGORY_DAILY_CAPS.get(category, 240.0)
        if over_baseline or over_cap:
            flagged.append((process_name, category, score, baseline))
            if category == "game":
                game_apps.append(process_name)

    suggestions = []
    with closing(_connect(database_path)) as connection:
        if len(game_apps) >= 2:
            category_key = "game"
            if not _recently_suggested(database_path, category=category_key):
                features = {
                    "score": round(sum(score for _, category, score, _ in flagged if category == "game"), 2),
                    "baseline": None,
                    "time_of_day_histogram": {},
                    "category": "game",
                    "processes": game_apps,
                }
                connection.execute(
                    """
                    INSERT INTO suggestions
                        (ts, process_name, type, features_json, outcome)
                    VALUES (?, ?, ?, ?, 'pending')
                    """,
                    (
                        timestamp,
                        category_key,
                        "category_time_window_ban",
                        json.dumps(features, separators=(",", ":")),
                    ),
                )
                suggestions.append(("game", "category_time_window_ban", features))
        else:
            flagged.sort(key=lambda item: item[2], reverse=True)
            for process_name, category, score, baseline in flagged:
                if len(suggestions) >= MAX_APP_CANDIDATES:
                    break
                if _recently_suggested(database_path, process_name=process_name):
                    continue
                baseline_features = (
                    [baseline[0], baseline[1]]
                    if baseline[0] is not None and baseline[1] is not None
                    else None
                )
                features = {
                    "score": round(score, 2),
                    "baseline": baseline_features,
                    "time_of_day_histogram": _time_of_day_histogram(
                        process_name, date, database_path
                    ),
                    "category": category,
                }
                connection.execute(
                    """
                    INSERT INTO suggestions
                        (ts, process_name, type, features_json, outcome)
                    VALUES (?, ?, ?, ?, 'pending')
                    """,
                    (
                        timestamp,
                        process_name,
                        "usage_limit",
                        json.dumps(features, separators=(",", ":")),
                    ),
                )
                suggestions.append((process_name, "usage_limit", features))
        connection.commit()

    return suggestions


if __name__ == "__main__":
    print(generate_suggestions())
