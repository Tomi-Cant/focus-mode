# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import os

import json
import tkinter as tk

root: tk.Tk = None #type:ignore

selected_days = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
title_text = ""
help_open = False
time_selected = False
time_var = ''


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
    
parent_path = get_data_dir()
self_path = get_self_dir()
root_dir= parent_path[:parent_path.find("\\")+1]
log_path = get_log_path()
json_path = get_blacklist_path()
config_path = get_config_path()

#initializing data files
if not os.path.exists(json_path):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"time_list": {}}, f, indent=4)
if not os.path.exists(log_path):
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Log initialized\n")
if not os.path.exists(config_path):
    with open(config_path, "w", encoding= "utf-8") as f:
        json.dump({"audio": False,"volume": 1},f, indent = 4)
        
with open(json_path, "r", encoding="utf-8") as f:
    session_temp :dict = json.load(f)
time_group : dict = session_temp.get('time_list', {})
with open(config_path, "r", encoding= "utf-8") as f:
    configs :dict = json.load(f)
    configs["audio"]=True
