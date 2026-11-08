"""Day-buffered SQLite writes for Focused Up user settings."""
import json
import logging
import os
import sqlite3
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path


BAN_CHANGES_APPLY_IMMEDIATELY = True

ALLOWED_TABLES = {"app_settings", "ban_rules", "suggestions"}
_MIRROR = {}
_LOCK = threading.Lock()

BAN_RULE_COLUMNS = [
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
    "convertted",
    "warning_tiimes",
]


def get_database_path():
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "Focused Up" / "usage.db"


def _log_path():
    return Path(os.environ.get("LOCALAPPDATA", ".")) / "Focused Up" / "log.txt"


def _log(message):
    try:
        _log_path().parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=str(_log_path()),
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logging.error(message)
    except Exception as error:
        print("Unable to write crash log:", error)


def _connect(database_path=None):
    path = Path(database_path) if database_path else get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_buffer(database_path=None):
    with closing(_connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_changes (
                name TEXT PRIMARY KEY,
                program TEXT NOT NULL DEFAULT '[]',
                start_time TEXT NOT NULL DEFAULT '00:00',
                end_time TEXT NOT NULL DEFAULT '23:59',
                days TEXT NOT NULL DEFAULT '[]',
                productive TEXT NOT NULL DEFAULT '[]',
                select_type TEXT NOT NULL DEFAULT '',
                allowed_hours REAL NOT NULL DEFAULT 0 CHECK (allowed_hours >= 0),
                time_left REAL NOT NULL DEFAULT 0 CHECK (time_left >= 0),
                on_finish INTEGER NOT NULL DEFAULT 0 CHECK (on_finish IN (0, 1)),
                enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
                alowed_time REAL NOT NULL DEFAULT 0 CHECK (alowed_time >= 0),
                on_start INTEGER NOT NULL DEFAULT 0 CHECK (on_start IN (0, 1)),
                convertted TEXT NOT NULL DEFAULT '[]',
                warning_tiimes TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        connection.commit()


def _encode_json_fields(payload):
    encoded = dict(payload)
    for col in ("program", "days", "productive", "convertted", "warning_tiimes", "converted", "warning_times"):
        if col in encoded and not isinstance(encoded[col], str):
            encoded[col] = json.dumps(encoded[col], ensure_ascii=False, separators=(",", ":"))
    return encoded


def load_pending_into_memory(database_path=None):
    init_buffer(database_path)
    with _LOCK:
        _MIRROR.clear()
        with closing(_connect(database_path)) as connection:
            rows = connection.execute("SELECT * FROM pending_changes").fetchall()
        for row in rows:
            _MIRROR[("ban_rules", row["name"])] = {
                "op": "set",
                "payload": dict(row),
            }


def queue_change(table_name="ban_rules", op="set", key=None, payload=None, database_path=None):
    if payload is None:
        payload = {}
    if key is None and "name" in payload:
        key = payload["name"]
    key = str(key)
    
    payload = _encode_json_fields(payload)
    payload["name"] = key

    init_buffer(database_path)

    with _LOCK:
        with closing(_connect(database_path)) as connection:
            if op == "delete":
                connection.execute("DELETE FROM pending_changes WHERE name = ?", (key,))
                connection.commit()
                _MIRROR[("ban_rules", key)] = {"op": "delete", "payload": {}}
                return

            columns = _row_columns(connection, "pending_changes")
            valid_fields = [c for c in columns if c in payload]
            
            if not valid_fields:
                valid_fields = ["name"]
                payload["name"] = key

            placeholders = ", ".join("?" for _ in valid_fields)
            cols_str = ", ".join(valid_fields)
            updates = ", ".join("%s = excluded.%s" % (c, c) for c in valid_fields if c != "name")
            
            sql = """
            INSERT INTO pending_changes (%s)
            VALUES (%s)
            ON CONFLICT(name) DO UPDATE SET %s
            """ % (cols_str, placeholders, updates or "name = excluded.name")

            values = [payload[c] for c in valid_fields]
            connection.execute(sql, values)
            connection.commit()

        _MIRROR[("ban_rules", key)] = {
            "op": "set",
            "payload": payload,
        }


def _real_row(table_name, key, database_path=None):
    with closing(_connect(database_path)) as connection:
        columns = _row_columns(connection, "ban_rules")
        if not columns:
            return None
        unique_column = "name" if "name" in columns else "category"
        row = connection.execute(
            "SELECT * FROM ban_rules WHERE %s = ?" % unique_column,
            (key,),
        ).fetchone()
    return dict(row) if row else None


def _overlay(table_name, key, database_path=None):
    key = str(key)
    with _LOCK:
        pending = _MIRROR.get((table_name, key))

    if pending and pending["op"] == "delete":
        return None

    real = _real_row(table_name, key, database_path) or {}
    if pending:
        real.update(pending["payload"])
    return real or None


def get_ban_rule(name, database_path=None):
    return _overlay("ban_rules", name, database_path)


def _last_run_date(database_path=None):
    with closing(_connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_config (
                source TEXT NOT NULL,
                config_key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (source, config_key)
            )
            """
        )
        row = connection.execute(
            """
            SELECT value_json FROM app_config
            WHERE source = 'manual_buffer' AND config_key = 'last_run_date'
            """
        ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["value_json"])
    except json.JSONDecodeError:
        return None


def _set_last_run_date(date, database_path=None):
    with closing(_connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_config (
                source TEXT NOT NULL,
                config_key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (source, config_key)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO app_config (source, config_key, value_json)
            VALUES ('manual_buffer', 'last_run_date', ?)
            ON CONFLICT(source, config_key) DO UPDATE
                SET value_json = excluded.value_json
            """,
            (json.dumps(date),),
        )
        connection.commit()


def check_day_rollover(database_path=None):
    today = datetime.now().date().isoformat()
    previous = _last_run_date(database_path)
    if previous is None or previous != today:
        if flush_pending(database_path):
            _set_last_run_date(today, database_path)


def _row_columns(connection, table_name):
    rows = connection.execute("PRAGMA table_info(%s)" % table_name).fetchall()
    return [row["name"] for row in rows]


def _apply_change(connection, target_table, key, payload):
    columns = _row_columns(connection, target_table)
    payload = dict(payload)
    payload["name"] = key

    if "convertted" in payload and "converted" in columns and "converted" not in payload:
        payload["converted"] = payload["convertted"]
    if "warning_tiimes" in payload and "warning_times" in columns and "warning_times" not in payload:
        payload["warning_times"] = payload["warning_tiimes"]

    fields = [c for c in payload if c in columns]
    values = [payload[c] for c in fields]
    placeholders = ",".join("?" for _ in fields)
    updates = ",".join("%s = excluded.%s" % (c, c) for c in fields if c != "name")

    sql = """
    INSERT INTO %s (%s) VALUES (%s)
    ON CONFLICT(name) DO UPDATE SET %s
    """ % (target_table, ",".join(fields), placeholders, updates or "name = excluded.name")

    connection.execute(sql, values)


def flush_pending(database_path=None):
    init_buffer(database_path)
    with _LOCK:
        with closing(_connect(database_path)) as connection:
            rows = connection.execute("SELECT * FROM pending_changes").fetchall()
            if not rows:
                return True

            try:
                connection.execute("BEGIN IMMEDIATE")
                for row in rows:
                    payload = dict(row)
                    name = payload["name"]
                    savepoint = "pending_%s" % name.replace(" ", "_").replace("'", "")
                    connection.execute("SAVEPOINT %s" % savepoint)
                    try:
                        _apply_change(connection, "ban_rules", name, payload)
                    except Exception as error:
                        connection.execute("ROLLBACK TO %s" % savepoint)
                        connection.execute("RELEASE %s" % savepoint)
                        _log("Buffered change failed for rule=%s error=%s" % (name, error))
                        continue
                    connection.execute("RELEASE %s" % savepoint)

                connection.execute("DELETE FROM pending_changes")
                connection.commit()
            except Exception as error:
                connection.rollback()
                _log("Buffered transaction failed: %s" % error)
                return False

        _MIRROR.clear()

    return True
def get_app_setting(process_name, database_path=None):
    normalized_name = str(process_name).strip().casefold()
    setting = _overlay("app_settings", normalized_name, database_path)
    return setting if setting is not None else {
        "process_name": normalized_name,
        "category": "uncategorized",
        "excluded": 0,
        "snooze_until": None,
    }
def load_effective_time_groups(database_path=None):
    """Load schedules from SQLite, overlaying buffered ban-rule edits."""
    import db

    groups = db.load_blacklist()
    with _LOCK:
        pending_groups = {
            key: value
            for (table_name, key), value in _MIRROR.items()
            if table_name == "ban_rules"
        }
    for key, pending in pending_groups.items():
        if pending["op"] == "delete":
            groups.pop(key, None)
            continue
        payload = dict(pending["payload"])
        if "time_group_json" in payload:
            groups[key] = json.loads(payload["time_group_json"])
        else:
            groups[key] = {**groups.get(key, {}), **payload}
    return groups

if __name__ == "__main__":
    load_pending_into_memory()
    print("Manual buffer initialized successfully with updated pending_changes schema.")