# idea: grouping certain apps so they they can be blocked at sperate times
# need: fix shift for special symbols

import win32gui
import datetime
import proc_funcs
import time
import sys
import json
from helper_funcs import time_seperator, cull_times
from os.path import dirname, abspath, join


def main():
    index = 0
    parent_path = dirname(abspath(__file__))
    pathjson = join(parent_path, "blacklist.json")

    with open(pathjson, "r", encoding="utf-8") as f:  # json data collect
        data = json.load(f)

    added = data["added_list"]
    set_days = data["days"]
    for i in added:
        i = i.lower()
    time_list = data["time_list"]

    path = join(parent_path, "log.txt")
    curr_time = datetime.datetime.now()
    day_of_week = datetime.date.today().strftime("%A")
    # set_times, loop to collect, check if end time is passed if so remove from list with pair
    set_temp = [list(time_list.keys())[i] for i in range(
        # generator for loop makes list of set time
        len(list(time_list.keys())))]
    if set_temp == []:
        sys.exit()
    end_temp = [time_list[i]['end_time'] for i in set_temp]
    set_times = [datetime.datetime.now().replace(hour=int(time_seperator(set_temp[i])[0]), minute=int(
        # *makes list of datetime objects for set times
        time_seperator(set_temp[i])[1])) for i in range(len(set_temp))]
    end_times = [datetime.datetime.now().replace(hour=int(time_seperator(end_temp[i])[
        # *
        0]), minute=int(time_seperator(end_temp[i])[1])) for i in range(len(end_temp))]

    with open(path, "a") as log:
        log.write(f"Script started at {datetime.datetime.now()}\n")

    while set_times != []:  # main loop goes through each time pair
        curr_time = datetime.datetime.now()
        no_list = data['time_list'][set_temp[index]]['programs']
        win = win32gui.GetForegroundWindow()
        window = win32gui.GetWindowText(win)
        # checks for time and day of week
        if curr_time <= set_times[index] and day_of_week in set_days:

            proc_funcs.close_by_process(no_list, path, curr_time)

            proc_funcs.close_by_title(added, window, win, path, curr_time)

            proc_funcs.convert_to_exe(
                added, no_list, path, curr_time, index, set_temp, data, time_list, pathjson)

            

            index += 1
            index %= len(set_times)
        else:
            set_times, end_times = cull_times(set_times, end_times, index, curr_time)
        time.sleep(.75)  # checks every .75 seconds

    with open(path, "a") as log:
        log.write(f"|Target Time Reached|\n")


if __name__ == "__main__":
    main()
