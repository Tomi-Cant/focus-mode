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
import os
import random
from pygame import mixer
from tkinter import messagebox

def convert_to_exe( no_list, curr_time, index, set_temp):
    # converts application titles to their .exe counterpart
    added = vars.time_group[set_temp[index]].get("converted", [])
    temp =[]
    for i in no_list:
        
        if not i.endswith(".exe"):
            temp.append(i.lower())
        else:
            added.append(i)  
    open_windows = window_to_process.check_windows(temp)
    for i in open_windows:
        PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        added.append(i['name'])
        vars.time_group[set_temp[index]]['converted'] = added
        
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
                    play_audio()
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

def close_by_title(added, window, win, time_index,curr_time):
    if window in added or find_minecraft(window,added) != []: 
        if vars.time_group[time_index]["time_left"] >= 0:
            vars.time_group[time_index]["time_left"]-=.5
            return 
        
        PostMessage(win, win32con.WM_CLOSE, 0, 0)
        play_audio()
        with open(vars.log_path, "a") as log:
            log.write(f"    Closed {window} {curr_time}\n")
        
def sleep_pc(curr_time):
    print("slept")
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
    with open(vars.log_path, "a") as log:
                log.write(f"    PC slept {curr_time}\n")
                
def shutdown_pc(curr_time):
    print("shutdown")
    subprocess.run(["shutdown", "/s", "/t", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
    with open(vars.log_path, "a") as log:
                log.write(f"    PC shutdown {curr_time}\n")      
                         
def find_minecraft(title, added):
    if  'minecraft' in added or "Minecraft" in added:
        if("minecraft" in title.lower() or "Minecraft" in title):
            pattern = r"Minecraft\*?\s\d+\.\d+\.?\d+?"
            return re.findall(pattern, title)
    return []

def play_audio():
    if vars.configs["audio"]==False:
        return
    available_audio=get_audio()
    selected_audio= load_audio(available_audio)
    if not available_audio:
        return 
    selected_audio.set_volume(vars.configs["volume"])
    selected_audio.play(maxtime=4000)
    
def get_audio() -> list[str] | None:
    audio_sets = vars.self_path + "\\assets\\audio"
    audio_folders=os.listdir(audio_sets)
    audio_files=[]
    for folder in audio_folders:
        folder_dest= audio_sets+"\\"+folder
        for file in os.listdir(folder_dest): 
            if file.endswith(".mp4"):
                audio_files.append(file)
    
    return audio_files

def load_audio(audio_paths) ->mixer.Sound:
    
    random.shuffle(audio_paths)
    mixer.init()
    return mixer.Sound(audio_paths[0])
    
def productive_open(added, curr_time, time_index): 
    
    output=''
    select_type=vars.time_group[time_index]["select_type"]
    if vars.time_group[time_index]["productive"] == "":
         # write a window message that says no productive target for this time slot
        messagebox.showwarning("No productive app set!", "You did not set up an app to open when the last one was closed.",icon='warning')
        output = (f"    No productive application/website for this time slot")
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

if __name__ == '__main__':
    play_audio()