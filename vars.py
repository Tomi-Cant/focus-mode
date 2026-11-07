# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import os

import json
import tkinter as tk
import re

import db

root: tk.Tk = None #type:ignore

selected_days = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
warning_time_minutes = (45, 30, 25, 20, 15, 10, 5, 1)
default_warning_times = [minutes * 60 for minutes in warning_time_minutes]
title_text = ""
help_open = False
time_selected = False
time_var:str = '' 


#declaring paths
def get_data_dir():
    app_data = os.path.join(os.environ["LOCALAPPDATA"], "Focused Up")
    os.makedirs(app_data, exist_ok=True)
    return app_data
def get_self_dir():
    return os.path.dirname(os.path.abspath(__file__))
def get_blacklist_path():
    return os.path.join(get_data_dir(), "blacklist.json")
def get_log_path():
    return os.path.join(get_data_dir(), "log.txt")
def get_config_path():
    return os.path.join(get_data_dir(), "config.json")
def get_audio_path():
    return os.path.join(get_data_dir(), "assets", "audio")
def save_config(data):
    db.save_blacklist(data)


def load_blacklist():
    return db.load_blacklist()


def save_configs(data):
    db.save_app_config(data, source="config")
    db.save_audio_paths(data.get("owned", []), data.get("active", []))


def _looks_like_time(value):
    if not isinstance(value, str):
        return False
    if len(value) != 5 or value[2] != ":":
        return False
    hour, minute = value.split(":", 1)
    try:
        return 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59
    except ValueError:
        return False


def get_next_group_name(existing_groups=None):
    groups = existing_groups if existing_groups is not None else time_group
    if not isinstance(groups, dict):
        groups = {}

    index = 1
    while True:
        candidate = f"New Group ({index})"
        if candidate not in groups:
            return candidate
        index += 1


def normalize_time_groups(raw_groups):
    if not isinstance(raw_groups, dict):
        return {}

    normalized = {}
    for key, value in raw_groups.items():
        if not isinstance(value, dict):
            continue

        if value.get("name"):
            group_name = str(value.get("name")).strip()
        elif _looks_like_time(str(key)):
            group_name = get_next_group_name(normalized)
        else:
            group_name = str(key).strip() or get_next_group_name(normalized)
        if group_name in normalized:
            base_name = group_name
            suffix = 2
            while True:
                candidate = f"{base_name} ({suffix})"
                if candidate not in normalized:
                    group_name = candidate
                    break
                suffix += 1

        data = dict(value)
        data["name"] = group_name
        warning_times = data.get("warning_times", default_warning_times)
        if not isinstance(warning_times, list):
            warning_times = default_warning_times
        data["warning_times"] = warning_times
        data.setdefault("no_productive_silenced", False)
        if not data.get("start_time") and _looks_like_time(str(key)):
            data["start_time"] = str(key)
        elif not data.get("start_time"):
            data["start_time"] = "00:00"
        normalized[group_name] = data

    return normalized
    
parent_path = get_data_dir()
self_path = get_self_dir()
root_dir= parent_path[:parent_path.find("\\")+1]
log_path = get_log_path()
json_path = get_blacklist_path()
config_path = get_config_path()
audio_path = get_audio_path()
# Initializing local state now uses SQLite. JSON files are only migration inputs.
db.init_db()
if not os.path.exists(log_path):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Log initialized\n")
if not os.path.exists(audio_path):
    os.makedirs(audio_path, exist_ok=True)        

session_temp = {"time_list": db.load_blacklist()}
original_time_list = session_temp["time_list"]
time_group : dict = normalize_time_groups(original_time_list)
session_temp['time_list'] = time_group

if original_time_list != time_group:
    db.save_blacklist(time_group)
configs = db.load_app_config(
    defaults={
        
        "volume": 1,
        "idle_threshold_seconds": 60,
        "sample_interval_seconds": 10,
        "foreground_weight": 1.0,
        "open_weight": 0.25,
        "category_caps_minutes": {
            "game": 120,
            "social": 90,
            "video": 120,
            "work": 480,
            "browser": 180,
            "other": 240,
        },
    },
)
configs["owned"], configs["active"] = db.load_audio_paths()
