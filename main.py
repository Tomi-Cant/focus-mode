# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import win32gui
import datetime
import proc_funcs
import time
import sys
import json
from helper_funcs import time_seperator, cull_times, find_last_run
import vars


def main():
    index = 0
    
    time_list = vars.time_group

   
    curr_time = datetime.datetime.now()
    find_last_run(curr_time)
    day_of_week = datetime.date.today().strftime("%A")
    # set_times, loop to collect, check if end time is passed if so remove from list with pair
    set_temp = [key for key, data in time_list.items() if data.get('enabled', True)]
    if set_temp == []:
        sys.exit()
    to_remove :list[dict]= []
    for grouping,values in time_list.items():
            if day_of_week not in values.get('days', []):
                to_remove.append({grouping: values})
    for grouping in to_remove:
        grouping = list(grouping.keys())[0]
        del time_list[grouping]
        set_temp.remove(grouping)
    end_temp = [time_list[i]['end_time'] for i in set_temp]
    set_times = [datetime.datetime.now().replace(hour=int(time_seperator(set_temp[i])[0]), minute=int(
        time_seperator(set_temp[i])[1])) for i in range(len(set_temp))]     # *makes list of datetime objects for set times
    end_times = [datetime.datetime.now().replace(hour=int(time_seperator(end_temp[i])[
        0]), minute=int(time_seperator(end_temp[i])[1])) for i in range(len(end_temp))]  # *
      
    with open(vars.log_path, "a") as log:
        log.write(f"Script started at {datetime.datetime.now()}\n")
    
    while set_times != []:  # main loop goes through each time pair
        curr_time = datetime.datetime.now()
        no_list = vars.time_group[set_temp[index]]['programs']
        vars.time_var= vars.time_group[set_temp[index]]
        win = win32gui.GetForegroundWindow()
        window = win32gui.GetWindowText(win)
        
        if curr_time >= set_times[index] and day_of_week in vars.time_group[set_temp[index]]['days']:
            proc_funcs.convert_to_exe(
                             no_list, curr_time, index, set_temp)

            proc_funcs.close_by_process(no_list, curr_time,set_temp[index])

            proc_funcs.close_by_title(no_list, window, win, set_temp[index], curr_time)

            

        set_times, end_times = cull_times(set_times, end_times, index, curr_time)

        index += 1
        index %= len(set_times)
        
        time.sleep(.5)
        
    for i in to_remove:
        time_list.update(i)
    with open(vars.log_path, "a") as log:
        log.write(f"|Target Time Reached|\n")
    with open(vars.json_path, "w") as f:
        json.dump({"time_list": vars.time_group}, f, indent=2)  # updates json file
        
    on_finish = [sys.exit,proc_funcs.shutdown_pc, proc_funcs.sleep_pc]
    on_finish[vars.time_group['on_finish']](curr_time)
    
if __name__ == "__main__":
    main()
