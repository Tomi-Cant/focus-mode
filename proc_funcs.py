import window_to_process
from win32gui import PostMessage
from win32api import ShellExecute
import win32con
import time
import psutil
import json
import vars
import webbrowser


def convert_to_exe(added, no_list, curr_time, index, set_temp, data, time_list, ):
    # converts application titles to their .exe counterpart
    for i in window_to_process.check_windows(added):
        PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        no_list.append(i['name'])
        added.remove(i['title'])
        time_list[set_temp[index]]['programs'] = no_list
        data["added_list"] = added
        with open(vars.json_path, "w") as f:
            json.dump(data, f, indent=2)  # updates json file


def close_by_process(no_list, curr_time):
    if no_list != []:  
        # checks if process is banned with error catches
        for proc in window_to_process.process_search(no_list):
            
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
        PostMessage(win, win32con.WM_CLOSE, 0, 0)
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {window} {curr_time}\n")
        time.sleep(.5)
        
def productive_open(added, curr_time): # maybe add randomizer with multi later
    output=''
    prod_type =vars.time_group[curr_time]["productive type"]
    if prod_type== '':
        
        output = (f"    No productive application/website for this time slot")
    if prod_type == "website":
        webbrowser.open(vars.time_group[curr_time]["productive"])
        output = (f"    Opened productive website for {added} at {curr_time}\n") 
    if prod_type == "executable":
        ShellExecute(0, 'open',vars.time_group[curr_time]["productive"],'','',1) 
        output = (f"    Opened productive application for {added} at {curr_time}\n") 
    with open(vars.log_path, "a") as log:
        log.write(output)