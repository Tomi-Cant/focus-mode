# idea: grouping certain apps so they they can be blocked at sperate times
# need: new buttons - back to time list, double click for text,refactor json to change to dict

import win32gui,win32con,win32process
import datetime
import psutil
import time,sys
import json
import window_to_process
from os.path import dirname,abspath,join

def main():   
    index=0
    parent_path = dirname(abspath(__file__))
    pathjson=join(parent_path,"blacklist.json")

    def time_seperator(time:str)-> tuple[str,str]:
        return time[:2],time[3:]

    with open(pathjson, "r",encoding="utf-8") as f: # json data collect
        data=json.load(f)

    added=data["added_list"]
    for i,j in enumerate(added):
        added[i]=j.lower()
    time_list= data["time_list"]


    path=join(parent_path,"log.txt")
    curr_time=datetime.datetime.now()
    #set_times, loop to collect, check if end time is passed if so remove from list with pair
    set_temp=[list(time_list.keys())[i] for i in range(len(list(time_list.keys())))] #generator for loop makes list of set time
    if set_temp == []:
        sys.exit()
    end_temp=[time_list[i]['end_time'] for i in set_temp]
    set_times=[datetime.datetime.now().replace(hour=int(time_seperator(set_temp[i])[0]),minute=int(time_seperator(set_temp[i])[1])) for i in range(len(set_temp))] # *makes list of datetime objects for set times
    end_times=[datetime.datetime.now().replace(hour=int(time_seperator(end_temp[i])[0]),minute=int(time_seperator(end_temp[i])[1])) for i in range(len(end_temp))] # *
    
    with open(path, "a") as log:
        log.write(f"Script started at {datetime.datetime.now()}\n")
        
    while set_times!=[]: # main loop goes through each time pair
        curr_time=datetime.datetime.now()
        no_list=data['time_list'][set_temp[index]]['programs']
        win =win32gui.GetForegroundWindow()
        window =win32gui.GetWindowText(win)
        if  curr_time<=set_times[index]:
            if window in added:# older method for titles
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
                time_list[set_temp[index]]['programs']=no_list
                data["added_list"]=added
                with open(pathjson, "w") as f:
                    json.dump(data,f, indent=2) # updates json file      
            if no_list!=[]: #newer process based method
                for proc in window_to_process.process_search(no_list): #checks if process is banned with error catches (works, high consumption)
                    try:
                        proc.kill()
                        print(f"Process '{proc.info['name']}' terminated successfully.")
                        with open(path, "a") as log:
                            log.write(f"    Closed {proc.name()} {curr_time}\n")
                        continue
                    except psutil.NoSuchProcess:
                        print(f"Process '{proc.info['name']}' no longer exists.")
                    except psutil.AccessDenied:
                        print(f"Access denied to terminate process '{proc.info['name']}'.")
                
            if  curr_time>=end_times[index]: # checks if end time is passed if so remove from list with pair
                del end_times[index]
                del set_times[index]
            index+=1
            index%=len(set_times)   
            
        time.sleep(.75) # checks every .75 seconds
    with open(path, "a") as log:
        log.write(f"|Target Time Reached|\n")


if __name__ == "__main__":
    main()
