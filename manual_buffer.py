"""Day-buffered SQLite writes for Focused Up user settings."""
# python -m unittest discover -s tests -p "test_*.py" -v
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
_PENDING_BAN_COLUMNS = {
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
    "convertted": "TEXT",
    "warning_tiimes": "TEXT",
}


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def _log_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "log.txt"


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
        # Logging failures must not hide the original buffer failure.
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
        connection.executescript(
            """
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
                convertted TEXT,
                warning_tiimes TEXT,
                UNIQUE(table_name, key)
            );
            """
        )
        existing = {row["name"] for row in connection.execute(
            "PRAGMA table_info(pending_changes)"
        )}
        for column, definition in _PENDING_BAN_COLUMNS.items():
            if column not in existing:
                connection.execute(
                    "ALTER TABLE pending_changes ADD COLUMN %s %s" % (
                        column,
                        definition,
                    )
                )


def _payload(value):
    return json.loads(value) if value else {}


def _encoded_payload(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _database_payload(table_name, payload):
    if table_name != "ban_rules":
        return payload

    encoded = dict(payload)
    for column in ("program", "days", "productive", "convertted", "warning_tiimes"):
        if column in encoded and not isinstance(encoded[column], str):
            encoded[column] = json.dumps(
                encoded[column],
                ensure_ascii=False,
                separators=(",", ":"),
            )
    return encoded


def _pending_payload(row, payload):
    if row["table_name"] != "ban_rules":
        return payload
    result = dict(payload)
    for column in _PENDING_BAN_COLUMNS:
        if row[column] is not None:
            result[column] = row[column]
    return result


def load_pending_into_memory(database_path=None):
    init_buffer(database_path)
    with _LOCK:
        _MIRROR.clear()
        with closing(_connect(database_path)) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pending_changes
                ORDER BY id
                """
            ).fetchall()
        for row in rows:
            _MIRROR[(row["table_name"], row["key"])] = {
                "op": row["op"],
                "payload": _pending_payload(row, _payload(row["payload_json"])),
            }


def queue_change(table_name, op, key, payload=None, database_path=None):
    if table_name not in ALLOWED_TABLES:
        raise ValueError("Invalid buffered table: %s" % table_name)
    if op not in {"set", "delete"}:
        raise ValueError("Invalid buffered operation: %s" % op)
    if op == "delete":
        payload = None
    elif payload is None:
        payload = {}
    elif not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary")

    key = str(key)
    timestamp = datetime.now().isoformat(timespec="seconds")
    init_buffer(database_path)

    with _LOCK:
        existing = None
        with closing(_connect(database_path)) as connection:
            row = connection.execute(
                """
                SELECT op, payload_json FROM pending_changes
                WHERE table_name = ? AND key = ?
                """,
                (table_name, key),
            ).fetchone()
            if row is not None:
                existing = (row["op"], _payload(row["payload_json"]))

            merged = _database_payload(table_name, dict(payload or {}))  # pyright: ignore
            if op == "set" and existing and existing[0] == "set":  # pyright: ignore
                merged_payload = dict(existing[1])
                merged_payload.update(payload) #pyright: ignore
                merged = merged_payload

            column_names = [
                column for column in _PENDING_BAN_COLUMNS
                if table_name == "ban_rules" and op == "set" and column in merged
            ]
            if table_name == "ban_rules" and op == "set":
                merged.setdefault("name", key)
                column_names = ["name"] + column_names
                column_names = list(dict.fromkeys(column_names))
            direct_columns = ", " + ", ".join(column_names) if column_names else ""
            direct_placeholders = ", " + ", ".join("?" for _ in column_names) if column_names else ""
            assignments = "".join(
                ", %s = excluded.%s" % (column, column)
                for column in column_names
            )
            connection.execute(
                (
                    """
                INSERT INTO pending_changes
                    (ts, table_name, op, key, payload_json%s)
                VALUES (?, ?, ?, ?, ?%s)
                ON CONFLICT(table_name, key) DO UPDATE SET
                    ts = excluded.ts,
                    op = excluded.op,
                    key = excluded.key,
                    payload_json = excluded.payload_json%s
                """
                ) % (direct_columns, direct_placeholders, assignments),
                (
                    timestamp,
                    table_name,
                    op,
                    key,
                    None if op == "delete" else _encoded_payload(merged),
                ) + tuple(merged[column] for column in column_names),
            )
            connection.commit()
        _MIRROR[(table_name, key)] = {
            "op": op,
            "payload": merged if op == "set" else {},
        }


def _real_row(table_name, key, database_path=None):
    with closing(_connect(database_path)) as connection:
        if table_name == "app_settings":
            row = connection.execute(
                "SELECT * FROM app_settings WHERE process_name = ?", (key,)
            ).fetchone()
        elif table_name == "ban_rules":
            columns = _row_columns(connection, table_name)
            unique_column = "name" if "name" in columns else "category"
            row = connection.execute(
                "SELECT * FROM ban_rules WHERE %s = ?" % unique_column,
                (key,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT * FROM suggestions WHERE id = ?", (int(key),)
            ).fetchone()
    return dict(row) if row else None


def _overlay(table_name, key, database_path=None):
    key = str(key)
    pending = None
    with _LOCK:
        pending = _MIRROR.get((table_name, key))
        if pending is None and key:
            pending = None

    if table_name == "ban_rules" and not BAN_CHANGES_APPLY_IMMEDIATELY:
        pending = None
    if pending and pending["op"] == "delete":
        return None

    real = _real_row(table_name, key, database_path)
    if real is None:
        if table_name == "app_settings" and pending:
            real = {
                "process_name": key,
                "category": "uncategorized",
                "excluded": 0,
                "snooze_until": None,
                "display_name": None,
            }
        else:
            real = {}
    if pending:
        real.update(pending["payload"])
    return real or None


def get_app_setting(process_name, database_path=None):
    normalized_name = str(process_name).strip().casefold()
    setting = _overlay("app_settings", normalized_name, database_path)
    return setting if setting is not None else {
        "process_name": normalized_name,
        "category": "uncategorized",
        "excluded": 0,
        "snooze_until": None,
        "display_name": None,
    }


def get_ban_rule(category, database_path=None):
    return _overlay("ban_rules", category, database_path)


def get_suggestion(suggestion_id, database_path=None):
    return _overlay("suggestions", suggestion_id, database_path)


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
            (_encoded_payload(date),),
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


def _apply_change(connection, table_name, key, payload, op):
    if op == "delete":
        if table_name == "app_settings":
            connection.execute(
                "DELETE FROM app_settings WHERE process_name = ?", (key,)
            )
        elif table_name == "ban_rules":
            connection.execute("DELETE FROM ban_rules WHERE name = ?", (key,))
        else:
            connection.execute("DELETE FROM suggestions WHERE id = ?", (int(key),))
        return

    payload = dict(payload)
    columns = _row_columns(connection, table_name)
    if table_name == "app_settings":
        payload.setdefault("process_name", key)
        unique = "process_name"
    elif table_name == "ban_rules":
        payload.setdefault("name", key)
        unique = "name"
    else:
        payload.setdefault("id", int(key))
        unique = "id"
    if op == "set":
        existing_row = connection.execute(
            "SELECT * FROM %s WHERE %s = ?" % (table_name, unique),
            (payload[unique],),
        ).fetchone()
        if existing_row is not None:
            merged_payload = dict(existing_row)
            merged_payload.update(payload)
            payload = merged_payload

    fields = [column for column in payload if column in columns]
    values = [payload[column] for column in fields]
    placeholders = ",".join("?" for _ in fields)
    updates = ",".join(
        "%s = excluded.%s" % (column, column)
        for column in fields if column != unique
    )
    connection.execute(
        "INSERT INTO %s (%s) VALUES (%s) ON CONFLICT(%s) DO UPDATE SET %s"
        % (
            table_name,
            ",".join(fields),
            placeholders,
            unique,
            updates or "%s = %s" % (unique, unique),
        ),
        values,
    )


def flush_pending(database_path=None):
    init_buffer(database_path)
    with _LOCK:
        with closing(_connect(database_path)) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pending_changes ORDER BY id
                """
            ).fetchall()
            if not rows:
                return True

            attempted_ids = [row["id"] for row in rows]
            try:
                connection.execute("BEGIN IMMEDIATE")
                for row in rows:
                    savepoint = "pending_%s" % row["id"]
                    connection.execute("SAVEPOINT %s" % savepoint)
                    try:
                        payload = _pending_payload(row, _payload(row["payload_json"]))
                        _apply_change(
                            connection,
                            row["table_name"],
                            row["key"],
                            payload,
                            row["op"],
                        )
                    except Exception as error:
                        connection.execute("ROLLBACK TO %s" % savepoint)
                        connection.execute("RELEASE %s" % savepoint)
                        _log(
                            "Buffered change failed: table=%s key=%s payload=%s error=%s"
                            % (
                                row["table_name"],
                                row["key"],
                                row["payload_json"],
                                error,
                            )
                        )
                        continue
                    connection.execute("RELEASE %s" % savepoint)

                placeholders = ",".join("?" for _ in attempted_ids)
                connection.execute(
                    "DELETE FROM pending_changes WHERE id IN (%s)" % placeholders,
                    attempted_ids,
                )
                connection.commit()
            except Exception as error:
                connection.rollback()
                _log("Buffered transaction failed: %s" % error)
                return False

        _MIRROR.clear()

  
    return True


if __name__ == "__main__":
    load_pending_into_memory()
    print("Manual buffer initialized.")
