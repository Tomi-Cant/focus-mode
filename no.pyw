import win32gui,win32con,win32process
import datetime
import psutil
import time
import json
import window_to_process
from os.path import dirname,abspath,join
parent_path = dirname(abspath(__file__))
path=join(parent_path,"blacklist.json")
no_list=["Epic Games Launcher","Steam",'Minecraft Lanuncher']


with open(path, "r",encoding="utf-8") as f:
    data=json.load(f)
no_list=data["blacklist"]
added=data["added_list"]
set_hour= data["set_hour"]  
set_minute= data['set_minute']
path=join(parent_path,"log.txt")
set_time=datetime.datetime.now().replace(hour=int(set_hour),minute=int(set_minute))
with open(path, "a") as log:
    log.write(f"Script started at {datetime.datetime.now()}\n")
while True:
    curr_time=datetime.datetime.now()
    win =win32gui.GetForegroundWindow()
    window =win32gui.GetWindowText(win)
    if  curr_time<=set_time:
        if window in no_list:
            win32gui.PostMessage(win, win32con.WM_CLOSE, 0, 0)
            with open(path, "a") as log:
                log.write(f"    Closed {window} {curr_time}\n")
            time.sleep(.5)
    if curr_time>=set_time:
        with open(path, "a") as log:
            log.write(f"|Target Time Reached|\n")
        break
    
    for i in window_to_process.check_windows(added):
        win32gui.PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        no_list.append(i['pid'])
        added.remove(i)
    while no_list:
        for proc in window_to_process.process_search(no_list):
            try:
                proc.kill()
                print(f"Process '{proc}' terminated successfully.")
            except psutil.NoSuchProcess:
                print(f"Process '{proc.info['name']}' no longer exists.")
            except psutil.AccessDenied:
                print(f"Access denied to terminate process '{proc.info['name']}'.")
        else:
            print(f"Process '{proc.info['name']}' not found.")
        with open(path, "a") as log:
            log.write(f"    Closed {proc.name()} {curr_time}\n")
            