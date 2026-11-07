"""SQLite storage for Focused Up usage data and focus rules."""

import json
import math
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


_SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    ts TEXT NOT NULL,
    process_name TEXT NOT NULL,
    is_foreground INTEGER NOT NULL CHECK (is_foreground IN (0, 1)),
    idle INTEGER NOT NULL CHECK (idle IN (0, 1))
);

CREATE INDEX IF NOT EXISTS samples_ts_idx ON samples (ts);
CREATE INDEX IF NOT EXISTS samples_process_ts_idx ON samples (process_name, ts);

CREATE TABLE IF NOT EXISTS daily_usage (
    date TEXT NOT NULL,
    process_name TEXT NOT NULL,
    fg_minutes REAL NOT NULL DEFAULT 0,
    open_minutes REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (date, process_name)
);

CREATE TABLE IF NOT EXISTS app_settings (
    process_name TEXT PRIMARY KEY,
    category TEXT NOT NULL DEFAULT 'uncategorized',
    excluded INTEGER NOT NULL DEFAULT 0 CHECK (excluded IN (0, 1)),
    snooze_until TEXT
);

CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    process_name TEXT NOT NULL,
    type TEXT NOT NULL,
    features_json TEXT NOT NULL DEFAULT '{}',
    outcome TEXT NOT NULL DEFAULT 'pending'
        CHECK (outcome IN ('accepted', 'dismissed', 'snoozed', 'pending'))
);

CREATE INDEX IF NOT EXISTS suggestions_outcome_idx ON suggestions (outcome);

CREATE TABLE IF NOT EXISTS app_names (
    process_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    updated_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ban_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    start_hour INTEGER NOT NULL CHECK (start_hour BETWEEN 0 AND 23),
    end_hour INTEGER NOT NULL CHECK (end_hour BETWEEN 0 AND 24),
    allowed_minutes REAL NOT NULL DEFAULT 0 CHECK (allowed_minutes >= 0),
    updated_ts TEXT NOT NULL,
    days_json TEXT NOT NULL DEFAULT '[]',
    processes_json TEXT NOT NULL DEFAULT '[]',
    legacy_key TEXT UNIQUE,
    legacy_data_json TEXT NOT NULL DEFAULT '{}',
    no_productive_silenced INTEGER NOT NULL DEFAULT 0
        CHECK (no_productive_silenced IN (0, 1))
);

CREATE INDEX IF NOT EXISTS ban_rules_category_idx ON ban_rules (category);

CREATE TABLE IF NOT EXISTS ban_attempts (
    ts TEXT NOT NULL,
    process_name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ban_attempts_ts_idx ON ban_attempts (ts);

CREATE TABLE IF NOT EXISTS app_config (
    source TEXT NOT NULL,
    config_key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    PRIMARY KEY (source, config_key)
);

CREATE TABLE IF NOT EXISTS audio_files (
    path TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS active_audio (
    path TEXT PRIMARY KEY,
    FOREIGN KEY (path) REFERENCES audio_files (path) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pending_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    table_name TEXT NOT NULL,
    op TEXT NOT NULL CHECK (op IN ('set', 'delete')),
    key TEXT NOT NULL,
    payload_json TEXT,
    UNIQUE(table_name, key)
);

CREATE TABLE IF NOT EXISTS buffer_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_run_date TEXT
);

CREATE TABLE IF NOT EXISTS sampler_heartbeat (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    ts TEXT NOT NULL
);
"""

APP_NAME_FALLBACKS = {
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
    "minecraft.windows.exe": "Minecraft",
}


def set_app_name(process_name, display_name, db_path=None):
    """Persist a converted process name without overwriting an existing name."""
    normalized_name = str(process_name).strip().casefold()
    display_name = str(display_name).strip()
    if not normalized_name or not display_name:
        return
    db_path = Path(db_path) if db_path else get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    updated_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO app_names
                    (process_name, display_name, updated_ts)
                VALUES (?, ?, ?)
                """,
                (normalized_name, display_name, updated_ts),
            )


def _encode_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _read_json_object(path):
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _parse_hour(value, field_name, allow_24=False):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise ValueError(f"Invalid {field_name} in legacy schedule: {value!r}")
    try:
        hour = int(value[:2])
        minute = int(value[3:])
    except ValueError as error:
        raise ValueError(
            f"Invalid {field_name} in legacy schedule: {value!r}"
        ) from error

    max_hour = 24 if allow_24 else 23
    if not 0 <= hour <= max_hour or not 0 <= minute <= 59:
        raise ValueError(f"Invalid {field_name} in legacy schedule: {value!r}")
    if hour == 24 and (not allow_24 or minute != 0):
        raise ValueError(f"Invalid {field_name} in legacy schedule: {value!r}")
    return hour


def _allowed_minutes(rule):
    # Older rules track their allowance in seconds; retain that meaning on import.
    if "allowed_time" in rule:
        value = rule["allowed_time"]
        divisor = 60
    else:
        value = rule.get("allowed_hours", 0)
        divisor = 1 / 60

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid allowed time in legacy schedule: {value!r}")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid allowed time in legacy schedule: {value!r}")
    return value / divisor


def _store_legacy_values(connection, source, values):
    ignored_config_keys = (
        {"enabled", "first_run", "active", "owned"}
        if source == "config"
        else set()
    )
    if ignored_config_keys:
        connection.executemany(
            "DELETE FROM app_config WHERE source = ? AND config_key = ?",
            [(source, key) for key in ignored_config_keys],
        )

    stored_keys = {
        str(key)
        for key in values
        if str(key) not in ignored_config_keys
    }
    connection.execute(
        """
        DELETE FROM app_config
        WHERE source = ?
          AND config_key NOT IN (
              SELECT value FROM json_each(?)
          )
        """,
        (
            source,
            _encode_json(sorted(stored_keys)),
        ),
    )

    # Store every legacy setting, including keys unknown to this database version.
    connection.executemany(
        """
        INSERT INTO app_config (source, config_key, value_json)
        VALUES (?, ?, ?)
        ON CONFLICT(source, config_key) DO UPDATE SET value_json = excluded.value_json
        """,
        [
            (source, str(key), _encode_json(value))
            for key, value in values.items()
            if str(key) not in ignored_config_keys
        ],
    )


def _import_legacy_blacklist(connection, path):
    if not path.exists():
        return
    blacklist = _read_json_object(path)
    _store_legacy_values(connection, "blacklist", blacklist)

    groups = blacklist.get("time_list", {})
    if not isinstance(groups, dict):
        raise ValueError(f"Expected 'time_list' to be an object in {path}")

    updated_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for group_key, rule in groups.items():
        if not isinstance(rule, dict):
            raise ValueError(f"Expected schedule {group_key!r} to be an object")

        category = str(rule.get("name") or group_key).strip()
        if not category:
            raise ValueError(f"Schedule {group_key!r} has no name")

        start_time = rule.get("start_time") or group_key
        if not isinstance(start_time, str) or len(start_time) != 5:
            start_time = "00:00"
        end_time = rule.get("end_time", "23:59")
        start_hour = _parse_hour(start_time, "start time")
        end_hour = _parse_hour(end_time, "end time", allow_24=True)

        days = rule.get("days", [])
        processes = rule.get("programs", [])
        if not isinstance(days, list) or not isinstance(processes, list):
            raise ValueError(f"Invalid days or programs in schedule {group_key!r}")

        # Keep the complete row because the new rule columns represent only part of it.
        connection.execute(
            """
            INSERT OR IGNORE INTO ban_rules (
                category, start_hour, end_hour, allowed_minutes, updated_ts,
                days_json, processes_json, legacy_key, legacy_data_json,
                no_productive_silenced
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(legacy_key) DO UPDATE SET
                category = excluded.category,
                start_hour = excluded.start_hour,
                end_hour = excluded.end_hour,
                allowed_minutes = excluded.allowed_minutes,
                updated_ts = excluded.updated_ts,
                days_json = excluded.days_json,
                processes_json = excluded.processes_json,
                legacy_data_json = excluded.legacy_data_json,
                no_productive_silenced = excluded.no_productive_silenced
            """,
            (
                category,
                start_hour,
                end_hour,
                _allowed_minutes(rule),
                updated_ts,
                _encode_json(days),
                _encode_json(processes),
                str(group_key),
                _encode_json(rule),
                int(bool(rule.get("no_productive_silenced", False))),
            ),
        )


def _import_legacy_audio(connection, audio_dir, config):
    audio_dir = Path(audio_dir)
    audio_extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    discovered = []
    if audio_dir.exists():
        for file_path in sorted(audio_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                discovered.append(str(file_path.resolve()))

    owned = config.get("owned", [])
    active = config.get("active", [])
    owned = owned if isinstance(owned, list) else []
    active = active if isinstance(active, list) else []

    def resolve_legacy_paths(paths):
        resolved = []
        for path_value in paths:
            if not isinstance(path_value, str) or not path_value.strip():
                continue
            candidate = Path(path_value)
            if candidate.is_absolute() and candidate.exists():
                resolved.append(str(candidate.resolve()))
                continue

            name = Path(path_value).name.casefold()
            matches = [
                found for found in discovered
                if Path(found).name.casefold() == name
            ]
            if matches:
                resolved.append(matches[0])
        return resolved

    all_paths = set(discovered)
    all_paths.update(resolve_legacy_paths(owned))
    all_paths.update(resolve_legacy_paths(active))

    connection.executemany(
        """
        INSERT OR IGNORE INTO audio_files (path, name)
        VALUES (?, ?)
        """,
        [(path, Path(path).name) for path in sorted(all_paths)],
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO active_audio (path)
        VALUES (?)
        """,
        [(path,) for path in resolve_legacy_paths(active)],
    )

    valid_active_paths = set(resolve_legacy_paths(active))
    connection.execute(
        """
        DELETE FROM active_audio
        WHERE path NOT IN (
            SELECT value FROM json_each(?)
        )
        """,
        (_encode_json(sorted(valid_active_paths)),),
    )


def _import_legacy_config(connection, path, audio_dir):
    if path.exists():
        config = _read_json_object(path)
        _store_legacy_values(connection, "config", config)
        _import_legacy_audio(connection, audio_dir, config)


def init_db(db_path=None):
    """Create the Focused Up database and import existing JSON settings."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if db_path is None:
        # The explicit per-user path also works when the app is frozen by PyInstaller.
        local_app_data = os.environ["LOCALAPPDATA"]
        db_path = Path(local_app_data) / "Focused Up" / "usage.db"
    else:
        db_path = Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_dir = Path(local_app_data) / "Focused Up" if local_app_data else None

    connection = sqlite3.connect(db_path)
    try:
        with connection:
            connection.executescript(_SCHEMA)
            updated_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            connection.executemany(
                """
                INSERT OR IGNORE INTO app_names
                    (process_name, display_name, updated_ts)
                VALUES (?, ?, ?)
                """,
                [
                    (process_name, display_name, updated_ts)
                    for process_name, display_name in APP_NAME_FALLBACKS.items()
                ],
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(ban_rules)")
            }
            if "no_productive_silenced" not in columns:
                connection.execute(
                    """
                    ALTER TABLE ban_rules
                    ADD COLUMN no_productive_silenced INTEGER NOT NULL DEFAULT 0
                    CHECK (no_productive_silenced IN (0, 1))
                    """
                )
            if legacy_dir is not None:
                _import_legacy_blacklist(
                    connection, legacy_dir / "blacklist.json"
                )
                _import_legacy_config(
                    connection,
                    legacy_dir / "config.json",
                    legacy_dir / "assets" / "audio",
                )
    finally:
        connection.close()


def get_database_path():
    """Return the per-user SQLite database path."""
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def load_app_config(source="config", defaults=None):
    """Load JSON-encoded application settings from SQLite."""
    config = dict(defaults or {})
    with sqlite3.connect(get_database_path()) as connection:
        rows = connection.execute(
            "SELECT config_key, value_json FROM app_config WHERE source = ?",
            (source,),
        ).fetchall()

    for key, encoded_value in rows:
        config[key] = json.loads(encoded_value)
    return config


def save_app_config(config, source="config"):
    """Replace one application's settings stored in SQLite."""
    with sqlite3.connect(get_database_path()) as connection:
        _store_legacy_values(connection, source, config)


def load_blacklist():
    """Load schedule groups from SQLite."""
    config = load_app_config("blacklist")
    groups = config.get("time_list", {})
    if not isinstance(groups, dict):
        return {}

    with sqlite3.connect(get_database_path()) as connection:
        for group_key, silenced in connection.execute(
            """
            SELECT legacy_key, no_productive_silenced
            FROM ban_rules
            WHERE legacy_key IS NOT NULL
            """
        ):
            if group_key in groups:
                groups[group_key]["no_productive_silenced"] = bool(silenced)
    return groups


def save_blacklist(time_groups):
    """Save schedule groups from SQLite."""
    with sqlite3.connect(get_database_path()) as connection:
        connection.execute(
            """
            INSERT INTO app_config (source, config_key, value_json)
            VALUES ('blacklist', 'time_list', ?)
            ON CONFLICT(source, config_key) DO UPDATE SET value_json = excluded.value_json
            """,
            (_encode_json(time_groups),),
        )
        for group_key, rule in time_groups.items():
            if not isinstance(rule, dict):
                continue
            connection.execute(
                """
                UPDATE ban_rules
                SET no_productive_silenced = ?,
                    legacy_data_json = ?
                WHERE legacy_key = ?
                """,
                (
                    int(bool(rule.get("no_productive_silenced", False))),
                    _encode_json(rule),
                    str(group_key),
                ),
            )
        connection.commit()


def load_audio_paths():
    """Load the owned and active audio paths from SQLite."""
    with sqlite3.connect(get_database_path()) as connection:
        owned = [
            row[0]
            for row in connection.execute(
                "SELECT path FROM audio_files ORDER BY path"
            )
        ]
        active = [
            row[0]
            for row in connection.execute(
                "SELECT path FROM active_audio ORDER BY path"
            )
        ]
    return owned, active


def save_audio_paths(owned, active):
    """Synchronize the audio inventory and active selections."""
    owned_paths = sorted(set(owned))
    active_paths = sorted(set(active))
    with sqlite3.connect(get_database_path()) as connection:
        connection.execute("DELETE FROM active_audio")
        connection.execute("DELETE FROM audio_files")
        connection.executemany(
            """
            INSERT INTO audio_files (path, name)
            VALUES (?, ?)
            """,
            [(path, Path(path).name) for path in owned_paths],
        )
        connection.executemany(
            """
            INSERT INTO active_audio (path)
            VALUES (?)
            """,
            [(path,) for path in active_paths if path in owned_paths],
        )


if __name__ == "__main__":
    init_db()
    print("Focused Up database initialized.")
