# idea: grouping certain apps so they they can be blocked at sperate times


import win32gui,win32con,win32process
import datetime
import psutil
import time
import json
import window_to_process
from os.path import dirname,abspath,join
parent_path = dirname(abspath(__file__))
pathjson=join(parent_path,"blacklist.json")
no_list=["Epic Games Launcher","Steam",'Minecraft Lanuncher']


with open(pathjson, "r",encoding="utf-8") as f: # json data collect
    data=json.load(f)
no_list=data["blacklist"]
added=data["added_list"]
set_hour= data["set_hour"]  
set_minute= data['set_minute']
path=join(parent_path,"log.txt")
curr_time=datetime.datetime.now()
set_time=datetime.datetime.now().replace(hour=int(set_hour),minute=int(set_minute))
with open(path, "a") as log:
    log.write(f"Script started at {datetime.datetime.now()}\n")
    
while curr_time<=set_time: 
    curr_time=datetime.datetime.now()
    win =win32gui.GetForegroundWindow()
    window =win32gui.GetWindowText(win)
    if  curr_time<=set_time:
        if window in added:# old method for titles
            win32gui.PostMessage(win, win32con.WM_CLOSE, 0, 0)
            with open(path, "a") as log:
                log.write(f"    Closed {window} {curr_time}\n")
            time.sleep(.5)
  
    for i in window_to_process.check_windows(added): # converts application titles to their .exe counterpart 
        win32gui.PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        no_list.append(i['name'])
        added.remove(i['title'])
        
    if no_list!=[]: #newer process based method
        for proc in window_to_process.process_search(no_list): #checks if process is banned with error catches (works, high consumption)
            try:
                proc.kill()
                print(f"Process '{proc.info['name']}' terminated successfully.")
                continue
            except psutil.NoSuchProcess:
                print(f"Process '{proc.info['name']}' no longer exists.")
            except psutil.AccessDenied:
                print(f"Access denied to terminate process '{proc.info['name']}'.")
        else:
            print(f"Process '{proc.info['name']}' not found.")
        with open(path, "a") as log:
            log.write(f"    Closed {proc.name()} {curr_time}\n")
    time.sleep(.75) # checks every .75 seconds
data["blacklist"]=no_list
data["added_list"]=added
with open(path, "a") as log:
    log.write(f"|Target Time Reached|\n")
with open(pathjson, "w") as f:
    json.dump(data,f, indent=2) # updates json file       