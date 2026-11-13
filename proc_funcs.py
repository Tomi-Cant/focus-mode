# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import re
import subprocess
import window_to_process
from win32gui import PostMessage
from win32api import ShellExecute
import win32con
import psutil
import threading
import vars
import webbrowser
import db

import random

import tkinter as tk

import time

NO_PRODUCTIVE_COOLDOWN_S = 5 * 60
_last_no_productive_warning = {}   # time_group_key -> time.monotonic() of last popup
_warning_lock = threading.Lock()
CLOSE_QUIET_S = 10
_last_close_seen = {}   # time_group_key -> time.monotonic() of last close detection

HELPER_TO_MAIN = {
    "steamwebhelper.exe": "steam.exe",
    "steamwebhelper": "steam",
    "opera web browser.exe": "opera.exe",
}

def _root_process(proc):
    main = HELPER_TO_MAIN.get(proc.info.get("name", "").casefold())
    if not main:
        return proc
    p = proc
    try:
        while p.parent() is not None and p.parent().name().casefold() == main:
            p = p.parent()
    except psutil.Error:
        pass
    return p
def _canonical(name):
    return HELPER_TO_MAIN.get(name.casefold(), name)
def is_new_close(time_index):
    """True only if this group had no close detected in the last CLOSE_QUIET_S seconds."""
    now = time.monotonic()
    with _warning_lock:
        last = _last_close_seen.get(time_index)
        _last_close_seen[time_index] = now   # refresh on every detection
        return last is None or now - last > CLOSE_QUIET_S

def _warning_allowed(time_group_key):
    """Returns True (and starts the cooldown) if the warning may be shown now."""
    now = time.monotonic()
    with _warning_lock:
        last = _last_no_productive_warning.get(time_group_key)
        if last is not None and now - last < NO_PRODUCTIVE_COOLDOWN_S:
            return False
        _last_no_productive_warning[time_group_key] = now
        return True
    
NO_PRODUCTIVE_WARNING_DURATION_MS = 5000
PROTECTED_PROCESS_NAMES = {"focusedupsampler.exe", "focusedupsampler", "focusedsampler.exe"}


def show_no_productive_warning(time_group_key=None):
    popup = tk.Tk()
    popup.title("No productive app set!")
    popup.resizable(False, False)
    tk.Label(
        popup,
        text="You did not set up an app to open when the last one was closed.",
        padx=20,
        pady=15,
    ).pack()

    if time_group_key is not None:
        def silence_indefinitely():
            rule = vars.time_group[time_group_key]
            rule["no_productive_silenced"] = True
            db.save_blacklist(vars.time_group)
            popup.destroy()

        tk.Button(popup, text="OK", command=popup.destroy).pack(
            side="left", padx=(20, 5), pady=(0, 15)
        )
        tk.Button(
            popup,
            text="Silence indefinitely",
            command=silence_indefinitely,
        ).pack(side="right", padx=(5, 20), pady=(0, 15))

    # auto-close after 5 seconds in every case
    popup.after(NO_PRODUCTIVE_WARNING_DURATION_MS, popup.destroy)
    popup.mainloop()

   
  
    def silence_indefinitely():
        rule = vars.time_group[time_group_key]
        rule["no_productive_silenced"] = True
        import db
        db.save_blacklist(vars.time_group)
        popup.destroy()

    tk.Button(popup, text="OK", command=popup.destroy).pack(
        side="left", padx=(20, 5), pady=(0, 15)
    )
    tk.Button(
        popup,
        text="Silence indefinitely",
        command=silence_indefinitely,
    ).pack(side="right", padx=(5, 20), pady=(0, 15))
    popup.mainloop()

def sleep_pc(curr_time):
    print("slept")
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
    with open(vars.log_path, "a") as log:
                log.write(f"    PC slept at {curr_time}\n")
                
def shutdown_pc(curr_time):
    print("shutdown")
    subprocess.run(["shutdown", "/s", "/t", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
    with open(vars.log_path, "a") as log:
                log.write(f"    PC shutdown at {curr_time}\n")      
                         
def find_minecraft(title, added):
    if  'minecraft' in added or "Minecraft" in added:
        if("minecraft" in title.lower() or "Minecraft" in title):
            pattern = r"Minecraft\*?\s\d+\.\d+\.?\d+?"
            return re.findall(pattern, title)
    return []

def convert_to_exe(no_list, curr_time, index, set_temp, closed_names=None):
    closed = False
    allowed_time = vars.time_group[set_temp[index]]["time_left"]
    for proc in window_to_process.process_search(no_list):
        if allowed_time > 0:
            allowed_time -= 0.5
            vars.time_group[set_temp[index]]["time_left"] = allowed_time
            vars.save_config(vars.time_group)
            return False
    added = vars.time_group[set_temp[index]].get("converted", [])
    added[:] = list(dict.fromkeys(_canonical(n) for n in added))
    temp = []
    for i in no_list:
        if not i.endswith(".exe"):
            temp.append(i.lower())
        if i.endswith(".exe") and i not in added:
            added.append(i)
    open_windows = window_to_process.check_windows(temp)
    for i in open_windows:
        if i["name"].casefold() in PROTECTED_PROCESS_NAMES:
            continue
        try:
            PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
            closed = True
            if closed_names is not None:
                closed_names.add(i['name'])
        except:
            pass

        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {i['title']} at {curr_time}\n")
        name = _canonical(i['name'])
        if name not in added:
            added.append(name)
        if closed_names is not None:
            closed_names.add(name)
        db.set_app_name(i['name'], i['title'])
        vars.time_group[set_temp[index]]['converted'] = added
        vars.save_config(vars.time_group)
    return closed


def close_by_process(no_list, curr_time, time_index, closed_names=None):
    closed = False
    if not no_list:
        return False
    no_list = list(dict.fromkeys(_canonical(n) for n in no_list))
    allowed_time = vars.time_group[time_index]["time_left"]
   
    for proc in window_to_process.process_search(no_list): # type: ignore
        process_name = proc.info.get("name", "")
        if process_name.casefold() in PROTECTED_PROCESS_NAMES:
            continue
        if allowed_time > 0:
            allowed_time -= 0.5
            vars.time_group[time_index]["time_left"] = allowed_time
            vars.save_config(vars.time_group)
            return False

        with open(vars.log_path, "a") as log:
            try:
                proc = _root_process(proc)
                for child in proc.children(recursive=True):
                    try:
                        child.kill()
                    except psutil.Error:
                        pass
                proc.kill()
                closed = True
                if closed_names is not None:
                    closed_names.add(process_name)
                log.write(f"    .Closed {process_name} at {curr_time}\n")
            except psutil.NoSuchProcess:
                log.write(f"Process '{process_name}' no longer exists.\n")
            except psutil.AccessDenied:
                log.write(f"Access denied to terminate process '{process_name}'.\n")
            except Exception as e:
                log.write(f"Unexpected error terminating '{process_name}': {e}\n")
    return closed


def close_by_title(added, window, win, time_index, curr_time, closed_names=None):
    if window in added or find_minecraft(window, added) != []:
        if vars.time_group[time_index]["time_left"] > 0:
            vars.time_group[time_index]["time_left"] -= 0.5
            vars.save_config(vars.time_group)
            return False
        closed = False
        try:
            PostMessage(win, win32con.WM_CLOSE, 0, 0)
            closed = True
            if closed_names is not None:
                closed_names.add(window)
        except:
            pass
        with open(vars.log_path, "a") as log:
            log.write(f"    ,Closed {window} at {curr_time}\n")
        return closed
    return False


def productive_open(added, curr_time, time_index):
    group = vars.time_group[time_index]
    productive_list = group["productive"]

    if not productive_list:
        with open(vars.log_path, "a") as log:
            log.write(f"    No productive application/website for this time slot at {curr_time}\n")
        if not group.get("no_productive_silenced", False) and _warning_allowed(time_index):
            threading.Thread(
                target=show_no_productive_warning,
                args=(time_index,),
                daemon=True,
            ).start()
        return

    if group["select_type"] == "Random":
        productive = random.choice(productive_list)
    else:  # Queue
        productive = productive_list[0]

    if productive == "#sleep pc":
        sleep_pc(curr_time)
        return
    if productive == "#shutdown pc":
        shutdown_pc(curr_time)
        return

    if productive.startswith("www."):
        webbrowser.open("https://" + productive)
        output = f"    Opened productive website for {added} at {curr_time}\n"
    else:
        ShellExecute(0, 'open', productive, '', '', 1)
        output = f"    Opened productive application for {added} at {curr_time}\n"
    with open(vars.log_path, "a") as log:
        log.write(output)