import win32gui,win32con,win32process
import datetime
import psutil
import time
import json
import window_to_process
from os.path import dirname,abspath,join
parent_path = dirname(dirname(abspath(__file__)))
path=join(parent_path,"blacklist.json")
end_time= 14
no_list=["Epic Games Launcher","Steam",'Minecraft Lanuncher']


with open(path, "r",encoding="utf-8") as f:
    no_list=json.load(f)["blacklist"]
    added=json.load(f)["added_list"]
    end_time= json.load(f)["endtime"]
path=join(parent_path,"log.txt")

with open(path, "a") as log:
    log.write(f"Script started at {datetime.datetime.now()}\n")
while True:
    win =win32gui.GetForegroundWindow()
    window =win32gui.GetWindowText(win)
    if window in no_list and datetime.datetime.now().hour < end_time :
        win32gui.PostMessage(win, win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {window} {datetime.datetime.now()}\n")
    time.sleep(.5)
    if datetime.datetime.now().hour >=end_time:
        with open(path, "a") as log:
            log.write(f"|Target Time Reached|\n")
        break
    
    for i in window_to_process.check_windows(added):
        win32gui.PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {i['title']} {datetime.datetime.now()}\n")
        no_list.append(i['pid'])
        added.remove(i)
    while True:
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
            log.write(f"    Closed {proc.name()} {datetime.datetime.now()}\n")
            