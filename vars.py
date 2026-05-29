from os.path import dirname, abspath, join
import json
import tkinter as tk

root: tk.Tk = None #type:ignore

selected_days = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
title_text = ""
help_open = False
time_selected = False
time_var = ''
parent_path = dirname(abspath(__file__))
rootdir= parent_path[:parent_path.find("\\")+1]
log_path = join(parent_path, "log.txt")
json_path = join(parent_path, "blacklist.json")
with open(json_path, "r", encoding="utf-8") as f:
    session_temp :dict = json.load(f)
time_group : dict = session_temp.get('time_list', {})
gui_blacklist_widgets = []  # List of tkinter Entry widgets
gui_timelist_widgets = []   # List of tkinter widgets for time list
active_window = "main"
font = ("Arial", 10)
large_font = ("Arial", 20)



