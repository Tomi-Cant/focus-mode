# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import tkinter as tk
import random
import subprocess
import vars
from pygame import mixer
from tkinter import messagebox
import os



def cull_times(start, end, indx, time,set_temp):
    """Remove time entries that have passed their end time"""
    if time >= end[indx]:
        del end[indx]
        del start[indx]
        del set_temp[indx]
    return start, end

def time_seperator(time: str) -> tuple[str, str]:
    """Separate time string into hours and minutes"""
    return time[:2], time[3:]


def get_active_texts(widgets, func) -> list:
    """
    Get active text from a list of tkinter Entry widgets
    If func is provided, apply it to each widget
    """
    output = []
    if not isinstance(widgets, list):
        return output
    
    if func is not None:
        for widget in widgets:
            if isinstance(widget, tk.Entry) and widget.winfo_exists():
                try:
                    result = func(widget)
                    if result is not None:
                        output.append(result)
                except:
                    pass
    else:
        for widget in widgets:
            if isinstance(widget, tk.Entry) and widget.winfo_exists():
                try:
                    text = widget.get().strip()
                    if text:
                        output.append(text)
                except:
                    pass
    
    return output

def read_last_x_lines(path, lines) -> list[str]:
    with open(path, 'r') as f:
        return f.readlines()[len(f.readlines())-lines-1:]
           
def find_last_run(curr_time ):
    found = False
    for line in read_last_x_lines(vars.log_path,5):
        if str(curr_time).split(" ")[0] in line:
            found =True
            break
    if found:
        return found  
    for group in vars.time_group.values():
        group["time_left"] = group["allowed_time"]
    return found

def find_steam_games():
    import vdf

    home = os.path.expanduser("~")
    steam_roots = [
        os.path.join(home, ".steam", "steam"),
        os.path.join(home, ".local", "share", "Steam"),
        os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam"),
    ]

    paths = []
    for steam_root in steam_roots:
        steamapps = os.path.join(steam_root, "steamapps")
        if os.path.isdir(steamapps) and steamapps not in paths:
            paths.append(steamapps)
        library_file = os.path.join(steamapps, "libraryfolders.vdf")
        if os.path.isfile(library_file):
            try:
                with open(library_file, "r", encoding="utf-8") as file:
                    library_data = vdf.load(file).get("libraryfolders", {})
                for library in library_data.values():
                    library_path = library.get("path") if isinstance(library, dict) else library
                    if library_path:
                        library_steamapps = os.path.join(library_path, "steamapps")
                        if os.path.isdir(library_steamapps) and library_steamapps not in paths:
                            paths.append(library_steamapps)
            except (OSError, ValueError):
                continue
    if not paths:
        return None

    games = ["Steam"]
    for path in paths:
        for file in os.listdir(path):
            if file.endswith(".acf"):
                try:
                    with open(os.path.join(path, file), "r", encoding="utf-8") as acf_file:
                        data = vdf.load(acf_file)
                    name = data.get("AppState", {}).get("name")
                    if name and name not in games:
                        games.append(name)
                except (OSError, ValueError):
                    continue
    return games

def find_epic_games():
    import json
    path = os.path.join(
        os.path.expanduser("~"),
        ".config",
        "Epic",
        "EpicGamesLauncher",
        "Data",
        "Manifests",
    )
    games = ["Epic Games Launcher"]
    if not os.path.exists(path):
        return None
    for file in os.listdir(path):
        if file.endswith(".item"):
            with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                name = data.get('DisplayName')
                if name and name not in games:
                    games.append(name)
    return games


def open_application(target):
    subprocess.Popen([target], start_new_session=True)

def play_audio():
    available_audio = get_audio()
    if not available_audio:
        return

    if not mixer.get_init():
        mixer.init()
    channel = mixer.Channel(0)
    if channel.get_busy():
        return

    selected_audio = load_audio(random.choice(available_audio))
    selected_audio.set_volume(vars.configs["volume"])
    channel.play(selected_audio, maxtime=4000)
    
def get_audio() -> list[str] :
    return vars.configs.get("active", [])

def check_audio_files():     
    audio_sets = os.path.join(vars.self_path, "assets", "audio")
    audio_files = vars.configs.get("owned", [])
    for folder, _, files in os.walk(audio_sets):
        for file in files:
            audio_path = os.path.join(folder, file)
            if file.lower().endswith(".mp3") and audio_path not in audio_files:
                audio_files.append(audio_path)
    vars.configs["owned"] = audio_files
    import json
    with open(vars.config_path, "w") as f:
        json.dump(vars.configs, f)

def load_audio(audio_path) ->mixer.Sound:
    if not mixer.get_init():
        mixer.init()
    return mixer.Sound(audio_path)
    
def play_voice(voice_path):
    if not os.path.exists(voice_path):
        messagebox.showerror("Error", f"Voice file not found: {voice_path}\n Please try relaunching the program or re-downloading the voice pack.")
        return
    mixer.init()
    sound = mixer.Sound(voice_path)
    sound.play(maxtime=4000)
    
def time_check(end_times, idx, curr_time):
    till_end = int((end_times[idx] - curr_time).total_seconds() )
    
    warning_times = vars.time_group[vars.time_var].get(
        "warning_times", vars.default_warning_times
    )
    if till_end in warning_times:
        # play audio on warning times
        play_warning_audio(till_end)
        return True
def play_warning_audio(time):        
    warning_audio = vars.configs.get("warning_audio", {})
    audio_path = warning_audio.get(str(int(time))+ "_left", None)
    if audio_path and os.path.exists(audio_path):
        audio =load_audio(audio_path)
        audio.set_volume(vars.configs["volume"])
        channel = mixer.Channel(1)
        if channel.get_busy():
            return
        channel.play(audio, maxtime=4000)
    else:
        with open(vars.log_path, "a") as log:
            log.write(f"        !Warning audio file not found for {time} seconds left\n")

def contact_support():    
    import webbrowser
    support_email = "focusedupofficial@gmail.com"
    subject = "Support Request"
    body = "Please describe your issue here."
    mailto_link = f"mailto:{support_email}?subject={subject}&body={body}"
    webbrowser.open(mailto_link) 