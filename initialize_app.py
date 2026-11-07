# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import json
import os
import subprocess
import vars
import os.path as path
subprocess.run(["pip","install", "-r","requirements.txt"], creationflags=subprocess.CREATE_NO_WINDOW)
from tkinter import messagebox
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
    
import pyuac
@pyuac.main_requires_admin
def initalize_app() -> None:
    if not pyuac.isUserAdmin():
        return
    curr_dir=path.abspath(path.dirname(path.dirname(sys.executable)))
    dir_path: str = path.join(os.environ["ProgramFiles"], "Focused Up")
    copy_result = subprocess.run(["robocopy", curr_dir, dir_path , "/s"],creationflags=subprocess.CREATE_NO_WINDOW)
    if copy_result.returncode >= 8:
        messagebox.showerror("Setup Incomplete", "The application files could not be copied. Setup was not completed.")
        return
    
    task_created = create_task.create_scheduled_task(
        task_name="FocusedUpTask",
        script_path='wscript.exe',
        script_args=f'"{dir_path}\\SilentRun.vbs" "{dir_path}\\StartProcess.bat"',
    )
    if not task_created:
        messagebox.showerror("Setup Incomplete", "The scheduled task could not be created. Setup was not completed.")
        return
    task_created =create_task.create_sampler_task(
        f"{dir_path}\\FocusedUpSampler\\FocusedUpSampler.exe"
    )
    if not task_created:
        messagebox.showerror("Setup Incomplete", "The usage sampler task could not be created. Setup was not completed.")
        return
    task_created = create_task.create_usage_scheduler_task(
        f"{dir_path}\\FocusedUpUsageSchduler\\FocusedUpUsageSchduler.exe"
    )
    if not task_created:
        messagebox.showerror("Setup Incomplete", "The usage scheduler task could not be created. Setup was not completed.")
        return
    if messagebox.askyesno("Desktop Icon?", "Would you like to add this app to your desktop screen for easier access?"):
        target = path.join(dir_path,"Focused Up", "Focused Up.exe")
        ps = f'''
        $desktop = [Environment]::GetFolderPath("Desktop")
        $s = (New-Object -ComObject WScript.Shell).CreateShortcut("$desktop\\Focused Up.lnk")
        $s.TargetPath = "{target}"
        $s.WorkingDirectory = "{dir_path}"
        $s.Save()
        '''
        shortcut_result = subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
        if shortcut_result.returncode != 0:
            messagebox.showerror("Setup Incomplete", "The desktop shortcut could not be created. Setup was not completed.")
            return

    vars.configs["version"] = 2.0
    vars.save_configs(vars.configs)
    messagebox.showinfo("Setup Complete", "Setup is complete! You can now use Focused Up to help you focus and limit distractions.")
    target_edit.main()
    
# Usage in your app's startup:
if __name__ == "__main__":
    if vars.configs.get("version") == 2.0:
        target_edit.main()
        sys.exit()
    if pyuac.isUserAdmin():
        initalize_app()   
        sys.exit()
    elif not messagebox.askokcancel("Setup Wizard", "This installation requires admin access to the device, will ask for permission to add itself to the desktop, and will install itself into Program Files (Where it can later be uninstalled if needed). Is this ok?", icon ='info'):
        sys.exit()
    
    result = initalize_app()
  