import window_to_process
from win32gui import PostMessage
from win32api import ShellExecute
import win32con
import datetime
import psutil
import json
import vars
import webbrowser
from tkinter import messagebox



def convert_to_exe( no_list, curr_time, index, set_temp):
    # converts application titles to their .exe counterpart
    added = []

    for i in no_list:
        if not i.endswith(".exe") and not i.endswith(" #website"):
            added.append(i)
    for i in window_to_process.check_windows(added):
        PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        no_list.append(i['name'])
        added.remove(i['title'])
        vars.session_temp[set_temp[index]]['programs'] = no_list
        
        with open(vars.json_path, "w") as f:
            json.dump(vars.session_temp, f, indent=2)  # updates json file


def close_by_process(no_list, curr_time,time_index):
    if no_list != []: 
        # checks if process is banned with error catches
        allowed_time = vars.time_group[time_index]["allowed_time"]
        for proc in window_to_process.process_search(no_list):
            if allowed_time >= 0:
                allowed_time-=.5
                return

            with open(vars.log_path, "a") as log:
                try:
                    proc.kill()
                    productive_open(proc.info['name'], curr_time)
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

def close_by_title(added, window, win, curr_time):
    if window in added: 
    
        allowed_time = vars.time_group[curr_time]["time_left"]
        if allowed_time >= 0:
            allowed_time-=.5
            return 
        PostMessage(win, win32con.WM_CLOSE, 0, 0)
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {window} {curr_time}\n")
        
   
def productive_open(added, curr_time): # maybe add randomizer with multi later or queue system
    import random
    output=''
    select_type=vars.time_group[curr_time]["select_type"]
    if vars.time_group[curr_time]["productive"] == "":
         # write a window message that says no productive target for this time slot
        messagebox.showwarning("No productive app set!", "You did not set up an app to open when the last one was closed.",icon='warning')
        output = (f"    No productive application/website for this time slot")
    if select_type == "Random":
        productive = vars.time_group[curr_time]["productive"][random.randint(0, len(vars.time_group[curr_time]["productive"])-1)]
    if select_type == "Queue":
        productive = vars.time_group[curr_time]["productive"][0] 
        
    if productive.endswith(" #website"):
        webbrowser.open(productive.strip(" #website"))
        output = (f"    Opened productive website for {added} at {curr_time}\n") 
    else:
        ShellExecute(0, 'open',productive,'','',1) 
        output = (f"    Opened productive application for {added} at {curr_time}\n") 
    with open(vars.log_path, "a") as log:
        log.write(output)

