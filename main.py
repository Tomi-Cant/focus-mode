# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

# pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "Focused Up" initialize_app.py      
# pyinstaller --onedir --noupx --windowed --icon=focused_up_logo.ico --name "FocusedUpScript" main.py
import win32gui
import datetime
import proc_funcs
import time
import sys
import json
import subprocess
import webbrowser
from helper_funcs import time_seperator, cull_times, find_last_run
import helper_funcs
import vars
import manual_buffer


def ensure_sampler_running():
    database_path = vars.db.get_database_path()
    stale = True
    try:
        heartbeat = manual_buffer._last_run_date(database_path)
        # The sampler heartbeat uses its own SQLite table in sampler.py.
        import sqlite3
        from contextlib import closing
        from datetime import timedelta
        with closing(sqlite3.connect(database_path)) as connection:
            row = connection.execute(
                "SELECT ts FROM sampler_heartbeat WHERE id = 1"
            ).fetchone()
        if row:
            last = datetime.datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            stale = datetime.datetime.now(datetime.timezone.utc) - last > timedelta(minutes=3)
    except Exception:
        stale = True

    if stale:
        try:
            subprocess.run(
                ["schtasks", "/run", "/tn", "FocusedUpSampler"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass


def run_custom_action(action, action_name="finish"):
    if isinstance(action, dict) and action.get('type') == 'custom':
        target = action.get('target', '').strip()
        try:
            if not target:
                raise ValueError(f"Custom {action_name} target is empty")
            if action.get('target_type') == 'website':
                webbrowser.open(target)
            elif action.get('target_type') == 'application':
                subprocess.Popen([target])
            else:
                raise ValueError(f"Unknown custom {action_name} target type")
        except Exception as error:
            with open(vars.log_path, "a", encoding="utf-8") as log:
                log.write(f"Could not run custom {action_name} action: {error}\n")
        return True
    return False


def run_trigger_action(action, curr_time):
    return run_custom_action(action, "start")


def run_start_action(action, curr_time):
    if run_custom_action(action, "start"):
        return
    return


def run_finish_action(action, curr_time):
    if run_custom_action(action, "finish"):
        return

    actions = [sys.exit, proc_funcs.shutdown_pc, proc_funcs.sleep_pc]
    if isinstance(action, int) and 0 <= action < len(actions):
        actions[action](curr_time)
    else:
        sys.exit()


def main():
    manual_buffer.check_day_rollover()
    ensure_sampler_running()
    vars.time_group = manual_buffer.load_effective_time_groups()
    index = 0
    finish_action = 0
    time_list = vars.time_group
    curr_time = datetime.datetime.now()
    is_same_day=find_last_run(curr_time)
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
    start_times = [time_list[i].get('start_time', '00:00') for i in set_temp]
    set_times = [datetime.datetime.now().replace(hour=int(time_seperator(start_times[i])[0]), minute=int(
        time_seperator(start_times[i])[1])) for i in range(len(start_times))]
    end_times = [datetime.datetime.now().replace(hour=int(time_seperator(end_temp[i])[0]), minute=int(time_seperator(end_temp[i])[1])) for i in range(len(end_temp))]
    if is_same_day:
            for i in range(len(set_temp)-1,0,-1):
                cull_times(set_times, end_times, i, curr_time, set_temp)  
    with open(vars.log_path, "a") as log:
        log.write(f"Script started at {datetime.datetime.now()}\n")
    
    started_groups = set()
    for group in set_temp:
        vars.time_group[group]["time_left"]=vars.time_group[group]["allowed_time"]
    
    while set_times != []:  # main loop goes through each time pair
        curr_time = datetime.datetime.now()
        no_list = vars.time_group[set_temp[index]]['programs']
        converted_list= vars.time_group[set_temp[index]]['converted']
        vars.time_var= vars.time_group[set_temp[index]]
        win = win32gui.GetForegroundWindow()
        window = win32gui.GetWindowText(win)
        
        if curr_time >= set_times[index] and day_of_week in vars.time_group[set_temp[index]]['days']:
            group_key = set_temp[index]
            if group_key not in started_groups:
                run_start_action(vars.time_group[group_key].get('on_start', 0), curr_time)
                started_groups.add(group_key)
            closed_process_names = set()
            closed = proc_funcs.convert_to_exe(
                no_list, curr_time, index, set_temp, closed_process_names)
            closed = proc_funcs.close_by_process(
                converted_list, curr_time, set_temp[index],
                skip_productive_for=closed_process_names) or closed
            closed = proc_funcs.close_by_title(
                no_list, window, win, set_temp[index], curr_time,
                trigger_productive=not closed_process_names) or closed
            if closed:
                helper_funcs.play_audio()

        if curr_time >= end_times[index]:
            finish_action = vars.time_group[set_temp[index]].get('on_finish', finish_action)

        set_times, end_times = cull_times(set_times, end_times, index, curr_time,set_temp)

        if not set_times:
            break
        index += 1
        index %= len(set_times)
        
        time.sleep(.5)
        
    for i in to_remove:
        time_list.update(i)
    with open(vars.log_path, "a") as log:
        log.write(f"|Target Time Reached|\n")
    vars.save_config(vars.time_group)
        
    run_finish_action(finish_action, curr_time)
    
if __name__ == "__main__":
    main()
