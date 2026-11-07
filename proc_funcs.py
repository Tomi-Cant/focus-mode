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
import json
import vars
import webbrowser

import random

import tkinter as tk


NO_PRODUCTIVE_WARNING_DURATION_MS = 5000
PROTECTED_PROCESS_NAMES = {"focusedupsampler.exe", "focusedupsampler", "focusedsampler.exe"}


def show_no_productive_warning(time_group_key=None):
    if time_group_key is None:
        popup = tk.Tk()
        popup.title("No productive app set!")
        popup.resizable(False, False)
        tk.Label(
            popup,
            text="You did not set up an app to open when the last one was closed.",
            padx=20,
            pady=15,
        ).pack()
        popup.after(NO_PRODUCTIVE_WARNING_DURATION_MS, popup.destroy)
        popup.mainloop()
        return

    popup = tk.Tk()
    popup.title("No productive app set!")
    popup.resizable(False, False)
    tk.Label(
        popup,
        text="You did not set up an app to open when the last one was closed.",
        padx=20,
        pady=15,
    ).pack()

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


def convert_to_exe(no_list, curr_time, index, set_temp, closed_process_names=None):
    closed = False
    allowed_time = vars.time_group[set_temp[index]]["time_left"]
    for proc in window_to_process.process_search(no_list):
        if allowed_time > 0:
            allowed_time-=.5
            vars.save_config(vars.time_group)
            return False
    # converts application titles to their .exe counterpart
    added = vars.time_group[set_temp[index]].get("converted", [])
    temp =[]
    for i in no_list:
        
        if not i.endswith(".exe") :
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
            productive_open(i['title'], curr_time, set_temp[index])
            if closed_process_names is not None:
                closed_process_names.add(i['name'].casefold())
        except:
                pass
        
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {i['title']} at {curr_time}\n")
        if i['name'] not in added:    
            added.append(i['name'])
        vars.time_group[set_temp[index]]['converted'] = added
        
        vars.save_config(vars.time_group)
    return closed


def close_by_process(no_list, curr_time, time_index, skip_productive_for=None):
    closed = False
    if no_list == []:
        return 
    skip_productive_for = {
        name.casefold() for name in (skip_productive_for or set())
    }
    # checks if process is banned with error catches
    allowed_time = vars.time_group[time_index]["time_left"]
    for proc in window_to_process.process_search(no_list):
        process_name = proc.info.get("name", "")
        if process_name.casefold() in PROTECTED_PROCESS_NAMES:
            continue
        if allowed_time > 0:
            allowed_time-=.5
            return

        with open(vars.log_path, "a") as log:
            try:
                proc.kill()
                closed = True
                if proc.info['name'].casefold() not in skip_productive_for:
                    productive_open(proc.info['name'], curr_time, time_index)
                log.write(f"    .Closed {proc.name()} at {curr_time}\n")
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

def close_by_title(added, window, win, time_index, curr_time, trigger_productive=True):
    if window in added or find_minecraft(window,added) != []: 
        if vars.time_group[time_index]["time_left"] > 0:
            vars.time_group[time_index]["time_left"]-=.5
            return False
        closed = False
        try:
            PostMessage(win, win32con.WM_CLOSE, 0, 0)
            closed = True
            if trigger_productive:
                productive_open(window, curr_time, time_index)
        except:
            pass
       
        with open(vars.log_path, "a") as log:
            log.write(f"    ,Closed {window} at {curr_time}\n")
        return closed
    return False
        
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


def productive_open(added, curr_time, time_index): 
    
    output=''
    select_type=vars.time_group[time_index]["select_type"]
    if vars.time_group[time_index]["productive"] == []:
        output = f"    No productive application/website for this time slot at {curr_time}\n"
        with open(vars.log_path, "a") as log:
            log.write(output)
        if not vars.time_group[time_index].get("no_productive_silenced", False):
            show_no_productive_warning(time_index)
        
        return
    if select_type == "Random":
        productive = vars.time_group[time_index]["productive"][random.randint(0, len(vars.time_group[time_index]["productive"])-1)]
    if select_type == "Queue":
        productive = vars.time_group[time_index]["productive"][0] 
    if productive == "#sleep pc":
        sleep_pc(curr_time)
    if productive == "#shutdown pc":
       shutdown_pc(curr_time)
    
    if productive.startswith("www."):
        webbrowser.open(productive.strip("www."))
        output = (f"    Opened productive website for {added} at {curr_time}\n") 
    else:
        ShellExecute(0, 'open',productive,'','',1) 
        output = (f"    Opened productive application for {added} at {curr_time}\n") 
    with open(vars.log_path, "a") as log:
        log.write(output)
