# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025
import tkinter as tk
import random
import vars
from pygame import mixer
from tkinter import messagebox
import os
def shorten(text: str, box_width: int, font_size: int = 10) -> str:
    

    tries = 0
    max_width = box_width // (font_size // 2)  # Rough estimate for character width
    
    if len(text) <= max_width:
        return text
    
    while len(text) > max_width and tries < 1000:
        tries += 1
        text = text[:-1]
    
    text = text.rstrip()
    if len(text) > max_width - 3:
        text = text[:max_width-3]
    text = text + '...'
    return text


def cull_times(start, end, indx, time):
    """Remove time entries that have passed their end time"""
    if time >= end[indx]:
        del end[indx]
        del start[indx]
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
           
def find_last_run(curr_time, ):
    found = False
    for line in read_last_x_lines(vars.log_path,5):
        if str(curr_time).split(" ")[0] in line:
            found =True
    if not found:
        for time in vars.time_group.values():
            time["time_left"] = time["allowed_time"]

def find_steam_games():
    import vdf, winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            
    except FileNotFoundError:
        return None
    
    steam_path= steam_path + r"\steamapps"
    paths=[steam_path]
    try:
        with open(steam_path+r"\libraryfolders.vdf", 'r', encoding='utf-8') as f:
            for line in f:
                if '"path"' in line:
                    path = line.split('"')[3]
                    path = path.replace("\\\\", "\\")
                    path = path + r"\steamapps"
                    if path not in paths:
                        paths.append(path)
                        
        
    except FileNotFoundError:
        pass
    games =[]
    for path in paths:
        for file in os.listdir(path):
            if file.endswith(".acf"):
                with open(os.path.join(path, file), 'r', encoding='utf-8') as f:
                    data = vdf.load(f)
                    name = data.get('AppState', {}).get('name')
                    if name and name not in games:
                        games.append(name)
    return games

def find_epic_games():
    import json
    path= r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests"
    games = []
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

def play_audio():
    if vars.configs["active"]==[]:
        return
    available_audio=get_audio()
    selected_audio= load_audio(available_audio)
    if not available_audio:
        return 
    selected_audio.set_volume(vars.configs["volume"])
    selected_audio.play(maxtime=4000)
    
def get_audio() -> list[str] :
    return vars.configs.get("active", [])

def check_audio_files():     
    audio_sets = vars.self_path + "\\assets\\audio"
    audio_folders=os.listdir(audio_sets)
    audio_files=vars.configs.get("owned", [])
    for folder in audio_folders:
        folder_dest= audio_sets+"\\"+folder
        for file in os.listdir(folder_dest): 
            if file.endswith(".mp3") and folder_dest+"\\"+file not in audio_files:
                audio_files.append(folder_dest+"\\"+file)
    vars.configs["owned"] = audio_files
    import json
    with open(vars.config_path, "w") as f:
        json.dump(vars.configs, f)

def load_audio(audio_paths) ->mixer.Sound:
    random.shuffle(audio_paths)
    mixer.init()
    return mixer.Sound(audio_paths[0])
    
def play_voice(voice_path):
    if not os.path.exists(voice_path):
        messagebox.showerror("Error", f"Voice file not found: {voice_path}\n Please try relaunching the program or re-downloading the voice pack.")
        return
    mixer.init()
    sound = mixer.Sound(voice_path)
    sound.play(maxtime=4000)
    
def contact_support():    
    import webbrowser
    support_email = "focusedupofficial@gmail.com"
    subject = "Support Request"
    body = "Please describe your issue here."
    mailto_link = f"mailto:{support_email}?subject={subject}&body={body}"
    webbrowser.open(mailto_link) 