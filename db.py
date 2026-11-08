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
    ,ignore_until TEXT
);

CREATE INDEX IF NOT EXISTS suggestions_outcome_idx ON suggestions (outcome);

CREATE TABLE IF NOT EXISTS app_names (
    process_name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    updated_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ban_rules (
    name TEXT PRIMARY KEY,
    program TEXT NOT NULL DEFAULT '[]',
    start_time TEXT NOT NULL DEFAULT '00:00',
    end_time TEXT NOT NULL DEFAULT '23:59',
    days TEXT NOT NULL DEFAULT '[]',
    productive TEXT NOT NULL DEFAULT '[]',
    select_type TEXT NOT NULL DEFAULT '',
    allowed_hours REAL NOT NULL DEFAULT 0 CHECK (allowed_hours >= 0),
    time_left REAL NOT NULL DEFAULT 0 CHECK (time_left >= 0),
    on_finish INTEGER NOT NULL DEFAULT 0 ,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    alowed_time REAL NOT NULL DEFAULT 0 CHECK (alowed_time >= 0),
    on_start INTEGER NOT NULL DEFAULT 0 ,
    converted TEXT NOT NULL DEFAULT '[]',
    warning_times TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS ban_rules_name_idx ON ban_rules (name);

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
    name TEXT,
    program TEXT,
    start_time TEXT,
    end_time TEXT,
    days TEXT,
    productive TEXT,
    select_type TEXT,
    allowed_hours REAL,
    time_left REAL,
    on_finish INTEGER,
    enabled INTEGER,
    alowed_time REAL,
    on_start INTEGER,
    converted TEXT,
    warning_times TEXT,
    UNIQUE(table_name, key)
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
    stored_keys = {
        str(key)
        for key in values
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

def _relax_ban_rules_checks(connection):
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='ban_rules'"
    ).fetchone()
    if not row or "on_finish IN (0, 1)" not in row[0]:
        return
    cols = ("name, program, start_time, end_time, days, productive, "
            "select_type, allowed_hours, time_left, on_finish, enabled, "
            "alowed_time, on_start, converted, warning_times")
    connection.execute("DROP INDEX IF EXISTS ban_rules_name_idx")
    connection.execute("ALTER TABLE ban_rules RENAME TO ban_rules_old")
    connection.executescript(_SCHEMA)   # recreates ban_rules with the new definition
    connection.execute(
        f"INSERT INTO ban_rules ({cols}) SELECT {cols} FROM ban_rules_old"
    )
    connection.execute("DROP TABLE ban_rules_old")
    
def _prepare_ban_rules_migration(connection):
    required_columns = {
        "name",
        "program",
        "start_time",
        "end_time",
        "days",
        "productive",
        "select_type",
        "allowed_hours",
        "time_left",
        "on_finish",
        "enabled",
        "alowed_time",
        "on_start",
        "converted",
        "warning_times",
    }
    table_exists = connection.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'ban_rules'
        """
    ).fetchone()
    if not table_exists:
        return
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(ban_rules)")
    }
    if columns == required_columns:
        return

    connection.execute("ALTER TABLE ban_rules RENAME TO ban_rules_legacy")


def _finish_ban_rules_migration(connection):
    table_exists = connection.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'ban_rules_legacy'
        """
    ).fetchone()
    if not table_exists:
        return

    legacy_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(ban_rules_legacy)")
    }
    legacy_required = {
        "category",
        "start_hour",
        "end_hour",
        "allowed_minutes",
    }
    if not legacy_required.issubset(legacy_columns):
        connection.execute("DROP TABLE ban_rules_legacy")
        return
    optional_column = lambda name, default: name if name in legacy_columns else default
    days_expression = optional_column("days_json", "'[]'")
    processes_expression = optional_column("processes_json", "'[]'")
    legacy_expression = optional_column("legacy_data_json", "'{}'")
    rows = connection.execute(
        f"""
        SELECT category, start_hour, end_hour, allowed_minutes,
               {days_expression}, {processes_expression}, {legacy_expression}
        FROM ban_rules_legacy
        """
    ).fetchall()

    for row in rows:
        category, start_hour, end_hour, allowed_minutes, days_json, processes_json, legacy_json = row
        try:
            legacy_rule = json.loads(legacy_json or "{}")
        except json.JSONDecodeError:
            legacy_rule = {}
        if not isinstance(legacy_rule, dict):
            legacy_rule = {}

        name = str(category or "").strip()
        if not name:
            continue
        start_time = legacy_rule.get("start_time", f"{int(start_hour):02d}:00")
        end_time = legacy_rule.get("end_time", f"{int(end_hour):02d}:00")
        program = legacy_rule.get("programs", legacy_rule.get("program", processes_json))
        if isinstance(program, str):
            try:
                program = json.loads(program)
            except json.JSONDecodeError:
                program = [program]

        days = legacy_rule.get("days")
        if not isinstance(days, list):
            days = _json_list(days_json)
        productive = legacy_rule.get("productive", [])
        if not isinstance(productive, list):
            productive = []
        select_type = legacy_rule.get("select_type", "")
        allowed_hours = legacy_rule.get("allowed_hours", 0)
        alowed_time = legacy_rule.get("allowed_time", float(allowed_minutes) * 60)
        time_left = legacy_rule.get("time_left", alowed_time)
        converted = legacy_rule.get("converted", [])
        warning_times = legacy_rule.get("warning_times", [])

        connection.execute(
            """
            INSERT OR REPLACE INTO ban_rules (
                name, program, start_time, end_time, days, productive,
                select_type, allowed_hours, time_left, on_finish, enabled,
                alowed_time, on_start, converted, warning_times
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                _encode_json(program if isinstance(program, list) else []),
                start_time,
                end_time,
                _encode_json(days),
                _encode_json(productive),
                str(select_type),
                float(allowed_hours or 0),
                float(time_left or 0),
                int(bool(legacy_rule.get("on_finish", 0))),
                int(bool(legacy_rule.get("enabled", True))),
                float(alowed_time or 0),
                int(bool(legacy_rule.get("on_start", 0))),
                _encode_json(converted if isinstance(converted, list) else []),
                _encode_json(warning_times if isinstance(warning_times, list) else []),
            ),
        )

    connection.execute("DROP TABLE ban_rules_legacy")


def _json_list(value):
    try:
        decoded = json.loads(value or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return decoded if isinstance(decoded, list) else []


def init_db(db_path=None):
    """Create the Focused Up database; JSON configuration is never imported."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if db_path is None:
        # The explicit per-user path also works when the app is frozen by PyInstaller.
        local_app_data = os.environ["LOCALAPPDATA"]
        db_path = Path(local_app_data) / "Focused Up" / "usage.db"
    else:
        db_path = Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        with connection:
            _prepare_ban_rules_migration(connection)
            connection.executescript(_SCHEMA)
            _finish_ban_rules_migration(connection)
            _relax_ban_rules_checks(connection)
            connection.execute("DROP TABLE IF EXISTS buffer_state")
            pending_columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(pending_changes)"
                )
            }
            pending_ban_columns = {
                "name": "TEXT",
                "program": "TEXT",
                "start_time": "TEXT",
                "end_time": "TEXT",
                "days": "TEXT",
                "productive": "TEXT",
                "select_type": "TEXT",
                "allowed_hours": "REAL",
                "time_left": "REAL",
                "on_finish": "INTEGER",
                "enabled": "INTEGER",
                "alowed_time": "REAL",
                "on_start": "INTEGER",
                "converted": "TEXT",
                "warning_times": "TEXT",
            }
            for column, definition in pending_ban_columns.items():
                if column not in pending_columns:
                    connection.execute(
                        "ALTER TABLE pending_changes ADD COLUMN %s %s"
                        % (column, definition)
                    )
            suggestion_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(suggestions)")
            }
            if "ignore_until" not in suggestion_columns:
                connection.execute(
                    "ALTER TABLE suggestions ADD COLUMN ignore_until TEXT"
                )
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
    groups = {}
    with sqlite3.connect(get_database_path()) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT name, program, start_time, end_time, days, productive,
                   select_type, allowed_hours, time_left, on_finish, enabled,
                   alowed_time, on_start, converted, warning_times
            FROM ban_rules
            ORDER BY name
            """
        ).fetchall()

    for row in rows:
        rule = dict(row)
        for column in ("program", "days", "productive", "converted", "warning_times"):
            try:
                rule[column] = json.loads(rule[column] or "[]")
            except (json.JSONDecodeError, TypeError):
                rule[column] = []

        groups[rule["name"]] = {
            "name": rule["name"],
            "programs": rule["program"],
            "start_time": rule["start_time"],
            "end_time": rule["end_time"],
            "days": rule["days"],
            "productive": rule["productive"],
            "select_type": rule["select_type"],
            "allowed_hours": rule["allowed_hours"],
            "time_left": rule["time_left"],
            "on_start": _load_action(rule["on_start"]),
            "enabled": bool(rule["enabled"]),
            "allowed_time": rule["alowed_time"],
            "on_finish": _load_action(rule["on_finish"]),
            "converted": rule["converted"],
            "warning_times": rule["warning_times"],
        }
    return groups


def _store_action(value):
    """on_start/on_finish can be 0/1/2 or a dict (custom action)."""
    if isinstance(value, (bool, int)):
        return int(value)
    return _encode_json(value)


def _load_action(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return 0
    return value or 0


def save_blacklist(time_groups):
    """Write every schedule group to ban_rules, one row per group."""
    rows = []
    for key, g in time_groups.items():
        rows.append((
            str(g.get("name") or key),
            _encode_json(g.get("programs", [])),
            g.get("start_time", "00:00"),
            g.get("end_time", "23:59"),
            _encode_json(g.get("days", [])),
            _encode_json(g.get("productive", [])),
            g.get("select_type", "") or "",
            max(0.0, float(g.get("allowed_hours", 0) or 0)),
            max(0.0, float(g.get("time_left", 0) or 0)),
            _store_action(g.get("on_finish", 0)),
            int(bool(g.get("enabled", True))),
            max(0.0, float(g.get("allowed_time", 0) or 0)),
            _store_action(g.get("on_start", 0)),
            _encode_json(g.get("converted", [])),
            _encode_json(g.get("warning_times", [])),
        ))

    names = [r[0] for r in rows]
    with sqlite3.connect(get_database_path()) as connection:
        if names:
            marks = ",".join("?" * len(names))
            connection.execute(
                f"DELETE FROM ban_rules WHERE name NOT IN ({marks})", names
            )
        else:
            connection.execute("DELETE FROM ban_rules")

        connection.executemany(
            """
            INSERT INTO ban_rules (
                name, program, start_time, end_time, days, productive,
                select_type, allowed_hours, time_left, on_finish, enabled,
                alowed_time, on_start, converted, warning_times
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                program = excluded.program,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                days = excluded.days,
                productive = excluded.productive,
                select_type = excluded.select_type,
                allowed_hours = excluded.allowed_hours,
                time_left = excluded.time_left,
                on_finish = excluded.on_finish,
                enabled = excluded.enabled,
                alowed_time = excluded.alowed_time,
                on_start = excluded.on_start,
                converted = excluded.converted,
                warning_times = excluded.warning_times
            """,
            rows,
        )


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