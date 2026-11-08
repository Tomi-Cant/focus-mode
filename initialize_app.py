# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025


import os
import subprocess
import vars
import os.path as path
import tkinter as tk
from tkinter import messagebox, ttk
import create_task
import sys
import target_edit

CURRENT_APP_VERSION = 2.0


def show_setup_welcome(root, admin_confirmation=False):
    agreed = False

    def agree():
        nonlocal agreed
        agreed = True
        root.destroy()

    def decline():
        root.destroy()

    frame = ttk.Frame(root, padding=20)
    frame.grid(sticky="nsew")
    ttk.Label(
        frame,
        text="Setup Wizard",
        font=("Segoe UI", 14, "bold"),
    ).grid(row=0, column=0, sticky="w")
    description = (
        "Confirm that Focused Up can create scheduled tasks that periodically "
        "sample your PC activity habits to provide usage insights and controls."
        if admin_confirmation else
        "This installation requires administrator access, permission to add "
        "a desktop shortcut, and installation into Program Files. Continue?"
    )
    ttk.Label(
        frame,
        text=(
            description
        ),
        wraplength=420,
        justify="left",
    ).grid(row=1, column=0, pady=(10, 18), sticky="w")

    buttons = ttk.Frame(frame)
    buttons.grid(row=2, column=0, sticky="e")
    primary_text = "Start" if admin_confirmation else "I Agree"
    ttk.Button(buttons, text=primary_text, command=agree).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(buttons, text="Cancel", command=decline).grid(row=0, column=1)

    root.update_idletasks()
    width, height = 460, 190
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.focus_force()
    root.lift()
    root.mainloop()
    return agreed


def ask_desktop_icon():
    choice = None
    root = tk.Tk()
    root.title("Focused Up Setup")
    root.resizable(False, False)
   

    def choose(create_icon):
        nonlocal choice
        choice = create_icon
        root.destroy()

    frame = ttk.Frame(root, padding=20)
    frame.grid(sticky="nsew")
    ttk.Label(
        frame,
        text="Desktop Shortcut",
        font=("Segoe UI", 14, "bold"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        frame,
        text="Would you like to add Focused Up to your desktop for easier access?",
        wraplength=420,
        justify="left",
    ).grid(row=1, column=0, pady=(10, 18), sticky="w")

    buttons = ttk.Frame(frame)
    buttons.grid(row=2, column=0, sticky="e")
    ttk.Button(buttons, text="Add Icon", command=lambda: choose(True)).grid(
        row=0, column=0, padx=(0, 8)
    )
    ttk.Button(buttons, text="Skip", command=lambda: choose(False)).grid(
        row=0, column=1
    )

    root.update_idletasks()
    width, height = 460, 190
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.focus_force()
    root.lift()
    root.mainloop()
    return choice


def show_setup_complete():
    root = tk.Tk()
    root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.title("Setup Complete")
    dialog.resizable(False, False)

    ttk.Label(
        dialog,
        text="Setup is complete! You can now use Focused Up to help you focus and limit distractions.",
        wraplength=420,
        justify="center",
        padding=(20, 20, 20, 10),
    ).grid(row=0, column=0)

    ttk.Button(dialog, text="OK", command=root.destroy).grid(row=1, column=0, pady=(0, 20))
    dialog.update_idletasks()
    dialog.after(5000, root.destroy)
    dialog.mainloop()


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
    if ask_desktop_icon() is True:
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

    vars.configs["version"] = CURRENT_APP_VERSION
    vars.save_configs(vars.configs)
    saved_configs = vars.db.load_app_config()
    if saved_configs.get("version") != CURRENT_APP_VERSION:
        messagebox.showerror("Setup Incomplete", "The application version could not be saved.")
        return
    show_setup_complete()
    target_edit.main()
    
# Usage in your app's startup:
if __name__ == "__main__":
    installed_version = vars.db.load_app_config().get("version",0.0)
    
    vars.log_path = vars.get_log_path()
    with open(vars.log_path, "a", encoding="utf-8") as log:
        log.write(f"req: {CURRENT_APP_VERSION}, installed: {installed_version}\n")
    if installed_version == CURRENT_APP_VERSION:
        target_edit.main()
        sys.exit()
    root = tk.Tk()
    root.title("Focused Up Setup")
    root.resizable(False, False)
    if not show_setup_welcome(root, admin_confirmation=pyuac.isUserAdmin()):
        sys.exit()
    initalize_app()
  