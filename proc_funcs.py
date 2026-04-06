
import window_to_process
import win32gui
import win32api
import win32con
import time
import psutil
import json


def close_by_title(added, window, win, path, curr_time):
    if window in added:  # method for titles
        time.sleep(.5)
        win32gui.PostMessage(win, win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {window} {curr_time}\n")
        time.sleep(.5)


def convert_to_exe(added, no_list, path, curr_time, index, set_temp, data, time_list, pathjson):
    # converts application titles to their .exe counterpart
    for i in window_to_process.check_windows(added):
        win32gui.PostMessage(i['hwnd'], win32con.WM_CLOSE, 0, 0)
        with open(path, "a") as log:
            log.write(f"    Closed {i['title']} {curr_time}\n")
        no_list.append(i['name'])
        added.remove(i['title'])
        time_list[set_temp[index]]['programs'] = no_list
        data["added_list"] = added
        with open(pathjson, "w") as f:
            json.dump(data, f, indent=2)  # updates json file


def close_by_process(no_list, path, curr_time):
    if no_list != []:  # newer process based method
        # checks if process is banned with error catches (works, high consumption)
        for proc in window_to_process.process_search(no_list):
            try:
                proc.kill()
                print(
                    f"Process '{proc.info['name']}' terminated successfully.")
                with open(path, "a") as log:
                    log.write(f"    Closed {proc.name()} {curr_time}\n")
                return True
            except psutil.NoSuchProcess:
                print(f"Process '{proc.info['name']}' no longer exists.")
            except psutil.AccessDenied:
                print(
                    f"Access denied to terminate process '{proc.info['name']}'.")
                
def start_program(path,to_open,curr_time):
    try:
        win32api.ShellExecute(0, 'open', to_open, '', '', 1)
        with open(path, "a") as log:
            log.write(f"        Started {to_open} {curr_time}\n")
    except Exception as e:
        print(f"Failed to start {to_open}: {e}")
    
if __name__ == "__main__":
    import datetime
    start_program(r"C:\Banjoko\Python\focus_mode\log.txt", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", datetime.datetime.now())   
    close_by_title(["Google Chrome"], "Google Chrome", 29100966, r"C:\Banjoko\Python\focus_mode\log.txt", datetime.datetime.now())
                   