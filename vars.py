# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import os

import json
import tkinter as tk
import re

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
    app_data = os.path.join(os.environ["LOCALAPPDATA"], "FocusUp")
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
    with open(get_blacklist_path(), "w") as f:
        json.dump(data, f, indent=2)

def load_blacklist():
    path = get_blacklist_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


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
#initializing data files
if not os.path.exists(json_path):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"time_list": {}}, f, indent=4)
if not os.path.exists(log_path):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Log initialized\n")
if not os.path.exists(config_path):
    with open(config_path, "w", encoding= "utf-8") as f:
        json.dump({"active": [],"owned": [],"enabled": False,"volume": 1},f, indent = 4)
if not os.path.exists(audio_path):
    os.makedirs(audio_path, exist_ok=True)        
    
with open(json_path, "r", encoding="utf-8") as f:
    session_temp :dict = json.load(f)
original_time_list = session_temp.get('time_list', {})
time_group : dict = normalize_time_groups(original_time_list)
session_temp['time_list'] = time_group

if original_time_list != time_group:
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(session_temp, f, indent=2)
with open(config_path, "r", encoding= "utf-8") as f:
    configs :dict = json.load(f)

