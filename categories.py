"""Category defaults and user category overrides."""

import os
import sqlite3
from pathlib import Path

import manual_buffer

 


DEFAULT_CATEGORIES = {
    "game.exe": "game",
    "leagueclient.exe": "game",
    "league of legends.exe": "game",
    "minecraft.exe": "game",
    "steam.exe": "game",
    "discord.exe": "social",
    "slack.exe": "work",
    "teams.exe": "work",
    "outlook.exe": "work",
    "code.exe": "work",
    "devenv.exe": "work",
    "excel.exe": "work",
    "winword.exe": "work",
    "powerpnt.exe": "work",
    "chrome.exe": "browser",
    "msedge.exe": "browser",
    "firefox.exe": "browser",
    "opera.exe": "browser",
    "brave.exe": "browser",
    "spotify.exe": "other",
    "vlc.exe": "video",
    "mpc-hc.exe": "video",
}


def get_database_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Focused Up" / "usage.db"


def get_category(process_name, database_path=None):
    """Return a saved override, a built-in category, or other."""
    database_path = Path(database_path) if database_path else get_database_path()
    name = str(process_name).strip().lower()

    setting = manual_buffer.get_app_setting(name, database_path=database_path)
    saved_category = setting.get("category")
    if saved_category and str(saved_category).lower() != "uncategorized":
        return str(saved_category).lower()
    return DEFAULT_CATEGORIES.get(name, "other")


def set_category(process_name, category, database_path=None):
    """Queue a category override so it remains visible during the current day."""
    name = str(process_name).strip().lower()
    value = str(category).strip().lower()
    if value not in {"game", "social", "video", "work", "browser", "other"}:
        raise ValueError("Invalid category: %s" % category)
    manual_buffer.queue_change(
        "app_settings",
        "set",
        name,
        {"process_name": name, "category": value},
        database_path=database_path,
    )
