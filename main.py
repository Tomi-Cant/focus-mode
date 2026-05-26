
import win32gui
import datetime
import proc_funcs
import time
import sys
import json
from scapy.all import AsyncSniffer
from helper_funcs import time_seperator, cull_times, find_last_run
import vars

def main():
    index = 0
    
    time_list = vars.time_group
    sniffer = AsyncSniffer(filter="udp port 53", prn=lambda packet: proc_funcs.close_by_website(datetime.datetime.now(), packet), store=0)
    sniffer.start()
    curr_time = datetime.datetime.now()
    find_last_run(curr_time)
    day_of_week = datetime.date.today().strftime("%A")
    # set_times, loop to collect, check if end time is passed if so remove from list with pair
    set_temp = [list(time_list.keys())[i] for i in range(
        len(list(time_list.keys())))] # generator for loop makes list of set time
    if set_temp == []:
        sys.exit()
    end_temp = [time_list[i]['end_time'] for i in set_temp]
    set_times = [datetime.datetime.now().replace(hour=int(time_seperator(set_temp[i])[0]), minute=int(
        time_seperator(set_temp[i])[1])) for i in range(len(set_temp))]# *makes list of datetime objects for set times
    end_times = [datetime.datetime.now().replace(hour=int(time_seperator(end_temp[i])[
        0]), minute=int(time_seperator(end_temp[i])[1])) for i in range(len(end_temp))]
        # *
    with open(vars.log_path, "a") as log:
        log.write(f"Script started at {datetime.datetime.now()}\n")
    
    while set_times != []:  # main loop goes through each time pair
        curr_time = datetime.datetime.now()
        no_list = vars.time_group[set_temp[index]]['programs']
        vars.time_var= vars.time_group[set_temp[index]]
        win = win32gui.GetForegroundWindow()
        window = win32gui.GetWindowText(win)
        vars.web_target = vars.time_group[set_temp[index]].get('programs', '')
        vars.web_target = list(filter(lambda x: x.startswith("www.") or x.startswith("http"), vars.web_target))
        # checks for time and day of week
        if curr_time >= set_times[index] and day_of_week in vars.time_group[set_temp[index]]['days']:

            proc_funcs.close_by_process(no_list, curr_time,set_temp[index])

            proc_funcs.close_by_title(no_list, window, win, set_temp[index], curr_time)

            proc_funcs.convert_to_exe(
                 no_list, curr_time, index, set_temp)

            cull_times(set_times, end_times, index, curr_time)

        index += 1
        index %= len(set_times)

        time.sleep(.5)  # checks every .5 seconds

    with open(vars.log_path, "a") as log:
        log.write(f"|Target Time Reached|\n")
    with open(vars.json_path, "w") as f:
        json.dump({"time_list": vars.time_group}, f, indent=2)  # updates json file

if __name__ == "__main__":
    main()
