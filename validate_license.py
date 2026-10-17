# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import json
import subprocess
import vars
import os.path as path
subprocess.run(["pip","install", "-r","requirements.txt"], creationflags=subprocess.CREATE_NO_WINDOW)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from tkinter import messagebox, filedialog
import webbrowser
from pathlib import Path
import create_task
import sys
import target_edit

class DummyStream:
    def write(self, data): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyStream()
if sys.stderr is None:
    sys.stderr = DummyStream()
    
PUBLIC_KEY_HEX = "2aa3b0cd6993482ed51a9b5e10004eb601cda72aaae88fad360efc95aa634ad7"
import pyuac
@pyuac.main_requires_admin
def initalize_app() -> None:
    dir_path :str =f"{vars.root_dir}\\Program Files\\Focused Up"
    create_task.create_scheduled_task(
        task_name="FocusedUpTask",
        script_path=f"{vars.root_dir}\\FocusedUpScript.exe"
    )
    if messagebox.askyesno("Desktop Icon?", "Would you like to add this app to your desktop screen for easier access?"):
        curr_dir=path.abspath(path.dirname(__file__))
        subprocess.run(["robocopy", curr_dir, dir_path , "/s"],creationflags=subprocess.CREATE_NO_WINDOW)
        subprocess.run(['mklnk',f"%userprofile%\\Desktop\\Focused Up.lnk",f"{dir_path}\\Focused Up.exe", "/s"],creationflags=subprocess.CREATE_NO_WINDOW)
    target_edit.main()

   
# Usage in your app's startup:
if __name__ == "__main__":
    if pyuac.isUserAdmin():
        initalize_app()
        sys.exit()
    elif not messagebox.askokcancel("Setup Wizard", "This installation requires admin access to the device, will ask for permission to add itself to the desktop, and will install itself into Program Files (Where it can later be uninstalled if needed). Is this ok?", icon ='info'):
        sys.exit()
    result = initalize_app()
  