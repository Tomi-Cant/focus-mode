# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import re
import subprocess
import window_to_process
import psutil
import json
import vars
import webbrowser

import random
import helper_funcs

from tkinter import messagebox

def close_matching_windows(no_list, curr_time, index, set_temp):
    closed = False
    allowed_time = vars.time_group[set_temp[index]]["time_left"]
    if allowed_time > 0:
        return False
    added = vars.time_group[set_temp[index]].get("converted", [])
    targets = list(no_list) + list(added)
    open_windows = window_to_process.check_windows(targets)
    for i in open_windows:
        try:
            window_closed = window_to_process.close_window(i['hwnd'])
            closed = window_closed or closed
            if window_closed:
                productive_open(i['title'], curr_time, set_temp[index])
                with open(vars.log_path, "a", encoding="utf-8") as log:
                    log.write(f"    Closed {i['title']} {curr_time}\n")
                if i['name'] not in added:
                    added.append(i['name'])
                vars.time_group[set_temp[index]]['converted'] = added
                with open(vars.json_path, "w", encoding="utf-8") as f:
                    json.dump(vars.session_temp, f, indent=2)
        except (OSError, KeyError, TypeError):
            continue
    return closed


def close_by_process(no_list, curr_time,time_index):
    closed = False
    if no_list == []:
        return False
    for proc in window_to_process.process_search(no_list):
        allowed_time = vars.time_group[time_index]["time_left"]
        if allowed_time > 0:
            vars.time_group[time_index]["time_left"] = max(0, allowed_time - .5)
            return False

        with open(vars.log_path, "a") as log:
            try:
                proc.kill()
                closed = True
                productive_open(proc.info['name'], curr_time, time_index)
                log.write(f"    Closed {proc.name()} {curr_time}\n")
                continue
            except psutil.NoSuchProcess:
                log.write(f"Process '{proc.info['name']}' no longer exists.")
            except psutil.AccessDenied:
                log.write(
                    f"Access denied to terminate process '{proc.info['name']}'.")
            except Exception as e:
                log.write(
                        f"An unexpected error occurred while trying to terminate process '{proc.info['name']}': {e}\n")
    return closed

def close_by_title(added, window, win, time_index,curr_time):
    if window_to_process.window_matches_targets(window, win, added) or find_minecraft(window,added) != []:
        if vars.time_group[time_index]["time_left"] > 0:
            vars.time_group[time_index]["time_left"]-=.5
            return False
        closed = False
        closed = window_to_process.close_window(win)
        if not closed:
            return False
        productive_open(window, curr_time, time_index)
       
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {window} {curr_time}\n")
        return closed
    return False
        
def sleep_pc(curr_time):
    _run_power_action(["systemctl", "suspend"], curr_time, "slept")
                
def shutdown_pc(curr_time):
    _run_power_action(["systemctl", "poweroff"], curr_time, "shutdown")


def _run_power_action(command, curr_time, action):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        result_text = (
            f"    PC {action} {curr_time}\n"
            if result.returncode == 0
            else f"Power action '{action}' failed: {result.stderr.strip()}\n"
        )
    except OSError as error:
        result_text = f"Power action '{action}' failed: {error}\n"
    with open(vars.log_path, "a", encoding="utf-8") as log:
        log.write(result_text)
                         
def find_minecraft(title, added):
    if  'minecraft' in added or "Minecraft" in added:
        if("minecraft" in title.lower() or "Minecraft" in title):
            pattern = r"Minecraft\*?\s\d+\.\d+\.?\d+?"
            return re.findall(pattern, title)
    return []


def productive_open(added, curr_time, time_index): 
    
    output=''
    productive_list = vars.time_group[time_index].get("productive", [])
    if not productive_list:
        messagebox.showwarning("No productive app set!", "You did not set up an app to open when the last one was closed.", icon='warning')
        with open(vars.log_path, "a", encoding="utf-8") as log:
            log.write("    No productive application/website for this time slot\n")
        return

    select_type=vars.time_group[time_index]["select_type"]
    if select_type == "Random":
        productive = productive_list[random.randint(0, len(productive_list)-1)]
    if select_type == "Queue":
        productive = productive_list[0]
    if select_type not in ("Random", "Queue"):
        productive = productive_list[0]
    if productive.casefold() == "#sleep pc":
        sleep_pc(curr_time)
        return
    if productive.casefold() == "#shutdown pc":
        shutdown_pc(curr_time)
        return
    
    if productive.startswith("www."):
        webbrowser.open(productive.strip("www."))
        output = (f"    Opened productive website for {added} at {curr_time}\n") 
    else:
        helper_funcs.open_application(productive)
        output = (f"    Opened productive application for {added} at {curr_time}\n") 
    with open(vars.log_path, "a") as log:
        log.write(output)

