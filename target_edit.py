# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
from tkinter import dialog
import helper_funcs
import webbrowser

# Import custom modules
from Button import Button
import vars


class FocusModeUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Focus Mode")
        self.root.geometry("600x600+600+100")
        vars.root = root
        
        # Initialize state
        self.time_buttons_frame = None
        self.blacklist_buttons_frame = None
        self.current_view = "main"
        
        # Create main UI
        self.create_main_view()
    
    def create_main_view(self):
        self.clear_window()
        self.current_view = "main"
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(
            main_container,
            text="Focused Up",
            font=("Arial", 16, "bold"),
            bg="lightgray"
        )
        title.pack(fill=tk.X, padx=5, pady=5)
        
        # Content frame
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Left panel - Buttons (smaller, fixed width)
        left_panel = ttk.Frame(content_frame, width=150)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        # left_panel.pack_propagate(False)
        
        self.blacklist_buttons_frame = ttk.Frame(left_panel)
        self.blacklist_buttons_frame.pack(fill=tk.BOTH)
        
        Button(self.blacklist_buttons_frame, x=0, y=0, text="Add", 
               command=self.add_to_time_list, bg_color="red", fg_color="white", font=("Arial", 11), width=12) #change to adda new time on other screen
        Button(self.blacklist_buttons_frame, x=1, y=0, text="Remove", 
               command=self.remove_from_timelist, bg_color="red", fg_color="white", font=("Arial", 11), width=12)
        Button(self.blacklist_buttons_frame, x=2, y=0, text="Edit Properties", 
               command=self.create_time_settings_view, bg_color="orange", fg_color="white", font=("Arial", 11), width=12)
        
        
        Button(self.blacklist_buttons_frame, x=4  , y=0, text="Save & Exit", 
                       command=self.exit, bg_color="green", fg_color="white", font=("Arial", 11), width=12)
        Button(self.blacklist_buttons_frame, x=5, y=0, text="Contact Support", 
               command=helper_funcs.contact_support, bg_color="yellow", fg_color="black", font=("Arial", 11), width=12)
        Button(self.blacklist_buttons_frame, x=6, y=0, text="Help", 
                       command=self.create_tutorial_view, bg_color="blue", fg_color="white", font=("Arial", 11), width=12)
        Button(self.blacklist_buttons_frame,x=7, y=0, text= "Sound Settings",
               command = self.open_audio_settings, bg_color="grey", fg_color='black', font=("Arial", 11), width=12, )
        # Right panel - List display (smaller)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        list_label = tk.Label(right_panel, text="Ban start times", font=("Arial", 11,))
        list_label.pack(fill=tk.X)
        
        # Listbox for blacklist (reduced size)
        self.blacklist_display = tk.Listbox(right_panel, height=35, width=60, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.blacklist_display.yview)
        self.blacklist_display.config(yscrollcommand=scrollbar.set)
        self.blacklist_display.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.blacklist_display.bind("<<ListboxSelect>>", self.select)
 
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
         
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(right_panel, textvariable=self.status_var, font=("Arial", 10, "italic"), fg="red", anchor="w")
        self.status_label.pack(fill=tk.X, pady=(5, 0))
 
        self.toggle_enabled_button = Button(self.blacklist_buttons_frame, x=3, y=0, text="Disable", command=self.toggle_time_group_enabled, bg_color="purple", fg_color="white", font=("Arial", 11), width=12)
        self.toggle_enabled_button.grid_remove()
 
        self.update_blacklist_display()
    
    def create_time_settings_view(self):
        
        self.clear_window()
        self.current_view = "time_settings"
        
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = tk.Label(
            main_container,
            text="Time Settings",
            font=("Arial", 16, "bold"),
            bg="lightgray"
        )
        title.pack(fill=tk.X, padx=5, pady=5)
        
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, padx=5, pady=5, anchor=tk.NW)
        
        tk.Label(left_panel, text="Time Groups", font=("Arial", 12, "bold")).pack(fill=tk.BOTH)
        
        # Frame for listbox and scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack( fill=tk.X, padx=0, pady=5)
        
        self.time_listbox = tk.Listbox(list_frame, height=10, width=30)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.time_listbox.yview)
        self.time_listbox.config(yscrollcommand=scrollbar.set)
        self.time_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        self.time_listbox.bind("<<ListboxSelect>>", self.select_time)
        
        
        # self.time_listbox.select_set(0)
        # self.time_listbox.event_generate("<<ListboxSelect>>")
        self.update_time_list()
        
        # Button frame for actions
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        temp = ttk.Button(button_frame, text= "Set Replacement Program/Site",command= self.change_replacement,default="disabled")
        temp.pack( padx=2, fill=tk.X,side= 'top')
        ttk.Button(button_frame, text="New", command=self.new_time_group).pack(side=tk.LEFT, fill=tk.X)
        ttk.Button(button_frame, text="Remove", command=self.remove_from_timelist).pack(side=tk.LEFT, padx=2, fill=tk.X)
        temp.configure(default='disabled')
        temp.pack_forget()
        temp.pack( padx=2, fill=tk.X,side= 'top')
        
        # Right panel - Settings (visible by default)
        right_panel = ttk.Frame(main_container,width=10)
        right_panel.pack(side=tk.RIGHT,  padx=5, pady=5, anchor =tk.N)
        
        # Name input section
        name_frame = ttk.LabelFrame(right_panel, text="Name")
        name_frame.pack(fill=tk.X, padx=5, pady=5,ipady=3)
        self.name_var = tk.StringVar(value="")
        ttk.Entry(name_frame, textvariable=self.name_var, width=20).pack(fill=tk.X, padx=5, pady=5)
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_panel, text="Enabled", variable=self.enabled_var,command= lambda: self.toggle_time_group_enabled()).pack(anchor=tk.W, padx=5, pady=(0,5))
        finish_frame= ttk.Frame(right_panel)
        self.finish_var= tk.StringVar(value="Nothing")
        ttk.Label(finish_frame,text="When Finished:").grid(row=0,column=0)
        self.finish_options= ["Nothing", "Shutdown PC", "Sleep PC"]
        ttk.OptionMenu(finish_frame, self.finish_var,"Nothing", *self.finish_options).grid(row=0, column=1)
        finish_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Time input section
        time_frame = ttk.LabelFrame(right_panel, text="Time Range (00:00-23:59)")
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(time_frame, text="Start Time (HH:MM):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(time_frame, text="End Time (HH:MM):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(time_frame, text= "Allowed Hours").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.end_hour_var = tk.StringVar(value="00")
        self.end_minute_var = tk.StringVar(value="00")
        self.allowed_hours= tk.DoubleVar(value=0.0) #converted to seconds in json
        
        
        ttk.Entry(time_frame, textvariable=self.hour_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(time_frame, text=":").grid(row=0, column=2)
        ttk.Entry(time_frame, textvariable=self.minute_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Entry(time_frame, textvariable=self.end_hour_var, width=5).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(time_frame, text=":").grid(row=1, column=2)
        ttk.Entry(time_frame, textvariable=self.end_minute_var, width=5).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Entry(time_frame,textvariable=self.allowed_hours,width=5).grid(row=2,column=1)
        # Day selection
        days_frame = ttk.LabelFrame(right_panel, text="Active Days")
        days_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.day_vars = {}
        for i, day in enumerate(vars.selected_days):
            var = tk.BooleanVar(value=True)
            self.day_vars[day] = var
            ttk.Checkbutton(days_frame, text=day, variable=var).grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=3)
        
        # Program blacklist for this time
        programs_frame = ttk.LabelFrame(left_panel, text="Programs to Block")
        programs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.program_listbox = tk.Listbox(programs_frame, height=8)
        prog_scrollbar = ttk.Scrollbar(programs_frame, orient=tk.VERTICAL, command=self.program_listbox.yview)
        self.program_listbox.config(yscrollcommand=prog_scrollbar.set)
        self.program_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Program input
        prog_input_frame = ttk.Frame(left_panel)
        prog_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.program_entry = ttk.Entry(prog_input_frame)
        self.program_entry.grid(row=1, column=1, padx=5)
        
        ttk.Button(prog_input_frame, text="Enter", command=self.add_program).grid(row=1, column=2, padx=5)
        ttk.Button(prog_input_frame, text="Browse...", command=self.add_to_blacklist).grid(row=1, column=3, padx=5)
        ttk.Button(prog_input_frame, text="Remove Selected", command=self.remove_program).grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        find_steam_button= ttk.Button(prog_input_frame, text="Search Steam", command=self.find_steam_games_helper)
        find_steam_button.grid(row=2, column=0, columnspan=2, padx=5, pady=15)
        find_epic_button= ttk.Button(prog_input_frame, text="Search Epic Games", command=self.find_epic_games_helper)
        find_epic_button.grid(row=2, column=2, columnspan=2, padx=5, pady=15)
        
        
        # Buttons
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self.save_time_settings).pack(side=tk.LEFT, padx=5,pady=20)
        ttk.Button(button_frame, text="Back", command=self.create_main_view).pack(side=tk.LEFT, padx=5,pady=20)
        if vars.time_group:
            self.time_listbox.select_set(0)
            vars.time_var=list(vars.time_group.keys())[0]
            self.update_time_display()
    
    def create_tutorial_view(self):
        self.clear_window()
        self.current_view = "tutorial"

        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = tk.Label(
            main_container,
            text="Focused Up Tutorial",
            font=("Arial", 16, "bold"),
            bg="lightgray"
        )
        title.pack(fill=tk.X, padx=5, pady=5)

        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_panel = ttk.Frame(content_frame, width=150)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)

        self.blacklist_buttons_frame = ttk.Frame(left_panel)
        self.blacklist_buttons_frame.pack(fill=tk.X)

        Button(self.blacklist_buttons_frame, x=0, y=0, text="Add", 
               command=self.tutorial_add, bg_color="red", fg_color="white", font=("Arial", 11), width=12, state=tk.NORMAL)
        Button(self.blacklist_buttons_frame, x=1, y=0, text="Remove", 
               command=self.remove_from_timelist, bg_color="grey", fg_color="white", font=("Arial", 9), width=12, state=tk.DISABLED)
        Button(self.blacklist_buttons_frame, x=2, y=0, text="Edit Properties", 
               command=self.create_time_settings_view, bg_color="grey", fg_color="white", font=("Arial", 9), width=12, state=tk.DISABLED)
        Button(self.blacklist_buttons_frame, x=3, y=0, text="Save & Exit", 
               command=self.exit, bg_color="grey", fg_color="white", font=("Arial", 11), width=12, state=tk.DISABLED)
        Button(self.blacklist_buttons_frame,x=4, y=0, text= "Sound Settings",
               command = self.open_audio_settings, bg_color="grey", fg_color='black', font=("Arial", 11), width=12, state=tk.DISABLED)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.blacklist_display = tk.Listbox(right_panel, height=15, width=35, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.blacklist_display.yview)
        self.blacklist_display.config(yscrollcommand=scrollbar.set)
        self.blacklist_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Button(self.root, text="Back to Main Menu", command=self.create_main_view).pack()
        self.blacklist_display.bind("<<ListboxSelect>>", self.select)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.intro = tk.Toplevel(self.root)
        
        self.intro.geometry("450x200+775+100")
        self.intro.title("Tutorial Add Function")
        self.intro.transient(self.root)
        tk.Label(self.intro, text="Welcome to Focus Mode!\nThis tutorial will guide you through the main features of the application.\nClick Add to get started").pack(pady=10)
        
        self.update_blacklist_display()

    def tutorial_add(self):
        self.intro.destroy()
        self.add_to_time_list()
        tutorial= tk.Toplevel(self.root)
        self.tutorial_window = tutorial
        tutorial.geometry("360x240+750+100")
        tutorial.title("Tutorial Add Function")
        tutorial.transient(self.root)

        dialogs = [
            "A time group defines when Focus Mode blocks selected programs. Use Add to create one, then give it a name and start time.",
            "On the Time Settings screen, choose the end time and the days of the week when this group should run.",
            "Use Allowed Hours to give yourself a daily allowance before a blocked program is closed. Set it to 0 for immediate blocking.",
            "The Enabled checkbox lets you pause a time group without deleting it. Disabled groups remain saved and can be enabled again later.",
            "Add programs by entering their window or process name, browsing for an executable, or searching installed Steam and Epic Games.",
            "When a blocked program is closed, you can add a replacement app or website. Replacement items can run in Queue order or be selected at Random.",
            "The replacement list also supports Force Sleep and Force Shutdown. These actions run when that replacement is selected, so use them carefully.",
            "Save the time group before going back. Save & Exit writes all groups to disk; Focus Mode then checks enabled groups on their selected days.",
            "This concludes the tutorial. Add as many time groups as you need, review each setting, and remember to save your changes before exiting.",
        ]
        self.tutorial_dialogs = dialogs
        self.index = 0
        self.label = ttk.Label(tutorial, text=dialogs[self.index], wraplength=330, font=("Arial", 12))
        self.label.pack(pady=10)
        button_frame = ttk.Frame(tutorial)
        button_frame.pack(pady=10)
        self.back_button = ttk.Button(button_frame, text="Back", command=lambda: self.next_dialog(-1))
        self.back_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(button_frame, text="Next", command=lambda: self.next_dialog(1))
        self.next_button.pack(side=tk.LEFT, padx=5)

        def close_tutorial():
            tutorial.destroy()

        ttk.Button(button_frame, text="Close", command=close_tutorial).pack(side=tk.LEFT, padx=5)
        self.back_button.config(state=tk.DISABLED)

    def next_dialog(self, direction=1):
        if direction > 0 and self.index == len(self.tutorial_dialogs) - 1:
            self.tutorial_window.destroy()
            return
        self.index = max(0, min(self.index + direction, len(self.tutorial_dialogs) - 1))
        self.label.config(text=self.tutorial_dialogs[self.index])
        self.back_button.config(state=tk.NORMAL if self.index > 0 else tk.DISABLED)
        self.next_button.config(
            text="Finish" if self.index == len(self.tutorial_dialogs) - 1 else "Next"
        )
    
    def add_to_blacklist(self):
        file_path = filedialog.askopenfilename(
            initialdir= vars.root_dir,   
            title="Select a program executable",
            filetypes=[ ("All files", "*.*"),("Executable files", "*.exe")]
        )
        
        if file_path:
            executable = file_path.split("\\")[-1]
            if vars.session_temp.get('time_list', {}) and vars.time_var in vars.time_group:
                programs = vars.time_group[vars.time_var]['programs']
                if executable not in programs:
                    programs.append(executable)
                    self.update_time_display()
                    messagebox.showinfo("Success", f"Added {executable} to blacklist")
                else:
                    messagebox.showwarning("Duplicate", f"{executable} is already in the list")
   
    def add_to_time_list(self):
        self.create_time_settings_view()
        self.new_time_group()
        
    def parse_selected_time(self, time_str:str) -> str:
        if " (" in time_str:
            return time_str.split(" (")[1].split(" - ")[0]
        return time_str.split(" - ")[0]
    
    def remove_from_timelist(self):
        if self.current_view == "time_settings":
            selection = self.select_time(None)
            if selection and selection in vars.time_group:
                del vars.time_group[selection]
                self.update_time_list()
                messagebox.showinfo("Removed", f"Removed {selection}")
        elif self.current_view == "main":
            if self.select(None)!=False: 
                item = self.select(None)
                if vars.time_group and vars.time_var in vars.time_group: 
                    if item in vars.time_group:
                        del vars.time_group[item]
                        self.update_blacklist_display()
                        self.update_main_selection_state()
                        messagebox.showinfo("Removed", f"Removed {item}")
 
    def select(self,event):
        selection = self.blacklist_display.curselection()
     
        if not selection:
            self.update_main_selection_state()
            return False
        selection_index = selection[0]
        selection_text = self.blacklist_display.get(selection_index).strip()
        if selection_text == "" or selection_text.startswith("-"):
            # If a program or blank line is selected, find the nearest group header above it
            while selection_index > 0:
                selection_index -= 1
                selection_text = self.blacklist_display.get(selection_index).strip()
                if selection_text and not selection_text.startswith("-"):
                    break
            else:
                self.update_main_selection_state()
                return False
 
        selection = self.parse_selected_time(selection_text)
        if selection in vars.time_group:
            vars.time_var = selection
            self.update_main_selection_state()
            return selection
 
        self.update_main_selection_state()
        return False
 
    def update_main_selection_state(self):
        if vars.time_var and vars.time_var in vars.time_group:
            enabled = vars.time_group[vars.time_var].get('enabled', True)
            self.status_var.set("Selected time group is disabled" if not enabled else "")
            self.toggle_enabled_button.configure(text="Enable" if not enabled else "Disable")
            self.toggle_enabled_button.grid()
        else:
            self.status_var.set("")
            self.toggle_enabled_button.grid_remove()
 
    def toggle_time_group_enabled(self):
        if vars.time_var and vars.time_var in vars.time_group:
            time_data = vars.time_group[vars.time_var]
            time_data['enabled'] = not time_data.get('enabled', True)
            vars.time_group[vars.time_var]['enabled'] = time_data['enabled']
            if self.current_view == 'main':
                self.update_blacklist_display()
                self.update_main_selection_state()
            if self.current_view == "time_settings" and vars.time_var in vars.session_temp.get('time_list', {}):
                self.enabled_var.set(time_data['enabled'])
                self.update_time_list()
                
            
    def select_time(self, event):
        selection = self.time_listbox.curselection()
    
        if selection:
            selection :str = self.time_listbox.get(selection[0])
            selection =self.parse_selected_time(selection)
            vars.time_var = selection
            self.update_time_display()
            return selection
        return False
    
    def select_program(self,event):
        selection = self.program_listbox.curselection()
    
        if selection:
            selection :str = self.program_listbox.get(selection[0])
            return selection
        return False
   
    def new_time_group(self):
        # Create a dialog for time and name input
        dialog = tk.Toplevel(self.root)
        dialog.title("New Time Group")
        dialog.geometry("350x220+700+400")
        dialog.transient(self.root)
        # dialog.grab_set()
        
        tk.Label(dialog, text="Enter name for this time group:", font=("Arial", 10)).pack(pady=5)
        name_var = tk.StringVar(value="")
        ttk.Entry(dialog, textvariable=name_var, width=30).pack(pady=5)
        
        tk.Label(dialog, text="Enter start time (HH:MM):", font=("Arial", 10)).pack(pady=5)
        
        time_frame = ttk.Frame(dialog)
        time_frame.pack(pady=10)
        
        hour_var = tk.StringVar(value="00")
        minute_var = tk.StringVar(value="00")
        
        ttk.Entry(time_frame, textvariable=hour_var, width=5, justify='center').pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        ttk.Entry(time_frame, textvariable=minute_var, width=5, justify='center').pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def add_time():
            try:
                hour = int(hour_var.get())
                minute = int(minute_var.get())
                
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    messagebox.showerror("Invalid", "Hour must be 0-23, minute must be 0-59")
                    return
                
                time_key = f"{hour:02d}:{minute:02d}"
                
                if time_key in vars.time_group:
                    messagebox.showwarning("Duplicate", f"Time {time_key} already exists")
                    return
                
                name = name_var.get().strip() or None
                
                # Add new time group with default values
                vars.time_group[time_key] = {
                    "name": name,
                    "programs": [],
                    "end_time": "23:59",
                    "days": vars.selected_days.copy(),
                    "productive":[],
                    "select_type":"Queue",
                    'allowed_hours': 0.0,
                    'time_left': 0.0, 
                    'on_finish': 0,  #either 0: nothing, 1: shutdown, 2: sleep 
                    'enabled': True
                }
                if vars.time_group[time_key]["name"]== None:
                    del vars.time_group[time_key]["name"]
                
                self.update_time_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Created new time group: {time_key}")
                self.time_listbox.select_set(tk.END)
                self.time_listbox.event_generate("<<ListboxSelect>>")
                
            except ValueError:
                messagebox.showerror("Invalid", "Please enter valid numbers for time")
        
        ttk.Button(button_frame, text="Create", command=add_time).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def change_replacement(self): #need to add option for queue or random 
        if not self.select_time(None):
            messagebox.showerror("Error","A time slot must be selected to use this option")
            return False
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Replacement App/Site")
        dialog.geometry("350x275+700+400")
        dialog.transient(self.root)
        # dialog.grab_set()
        app_frame= tk.Frame(dialog, name= 'app')
        web_frame= tk.Frame(dialog, name= 'web')
        button_frame= tk.Frame(dialog, name= "button",height=15)
        button_frame.grid_configure()
        self.list_frame= tk.Frame(dialog, name='list')
        web_url= tk.StringVar(value='Enter Website')
        button_frame.pack_configure(padx=4)
        tk.Label(app_frame, text= "Replacement Type: App",justify="center",font=("Arial", 14, "bold")).pack()
        ttk.Button(app_frame, text="Browse Files/Apps/Docs", command=lambda:self.select_file()).pack()

        app_frame.pack()
        
        tk.Label(web_frame, text="Replacement Type: Website",justify="center",font=("Arial", 14, "bold")).pack()
        tk.Entry(web_frame,textvariable=web_url,justify='center').pack()
        submit_entry=ttk.Button(web_frame, text="Enter", 
                               command = lambda:self.enter_replacement(web_url.get()))
        
        self.replacement_list= tk.Listbox(self.list_frame, height=15, width =50)
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.replacement_list.yview)
        self.replacement_list.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right",fill='y')
        self.update_replacement_listbox()
        ttk.Button(button_frame, text="Change Type", 
                  command=lambda:self.swap_out_widgets(app_frame,web_frame,self.list_frame,side='top')).grid(row=0,column=0)
        ttk.Button(button_frame,text='Remove Selected',command=self.remove_replacement).grid(row=0,column=1)
        self.shuffle_select=ttk.Button(button_frame, text='Change to Queue', 
                                      command=lambda:self.swap_out_widgets(queue_select,self.shuffle_select,self.list_frame,side='top') )
        queue_select= ttk.Button(button_frame, text='Change to Shuffle',
                                command=lambda:self.swap_out_widgets(queue_select,self.shuffle_select,self.list_frame,side='top') )
        queue_select.grid(row=0,column=2)

        ttk.Button(button_frame, text='Exit', command=lambda:dialog.destroy(), width= 7).grid(row=0,column=3)
        self.replacement_list.pack(side="left")
        ttk.Button(button_frame, text='Force Sleep', command=lambda: self.enter_replacement("#Sleep PC")).grid(row=1,column=1)
        ttk.Button(button_frame, text='Force Shutdown', command=lambda: self.enter_replacement("#Shutdown PC")).grid(row=1,column=2)
        submit_entry.pack()    
        button_frame.pack(side="bottom")
        
        self.list_frame.pack()
        
    def open_audio_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Audio Settings")
        dialog.geometry("350x220+700+400")
        dialog.transient(self.root)
        if vars.configs["audio"]== False:
            messagebox.askyesno("Addon Has Not Been Purchased ", "Audio Settings are part of the Voice Packs addon. Please purchase the addon to access this feature.")
            dialog.destroy()
            return
        button_frame=tk.Frame(dialog, name='voice')
        active_bool=tk.BooleanVar(value=vars.configs["enabled"])
        tk.Checkbutton(button_frame,name="enable audio",text="Enable 'The Voices'",variable=active_bool,command=lambda: self.update_audio_settings(active_bool.get(), "enable audio")).pack()
        for voice in vars.configs['owned']:
            if voice in vars.configs['active']:
                bool_var=tk.BooleanVar(value=True)
            else:
                bool_var=tk.BooleanVar(value=False)
            tk.Checkbutton(button_frame,text=voice,variable=bool_var,command=lambda voice=voice, voice_var=bool_var: self.update_audio_settings(voice_var.get(), voice)).pack()
        tk.Button(button_frame,text="Exit",command=lambda: dialog.destroy()).pack()
        button_frame.pack()
    def update_audio_settings(self, bool_var:bool,name=None):
        if name== "enable audio":
            vars.configs["enabled"]= bool_var
            
        else:
            active_voices = vars.configs.setdefault('active', [])
            if bool_var and name not in active_voices:
                active_voices.append(name)
            elif not bool_var and name in active_voices:
                active_voices.remove(name)
        with open(vars.config_path, 'w') as f:
            json.dump(vars.configs, f, indent=4)
        
        
    def find_steam_games_helper(self):  
        steam_games= helper_funcs.find_steam_games()
        if steam_games:
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Steam Games")
            dialog.geometry("400x300+700+400")
            dialog.transient(self.root)
            
            listbox = tk.Listbox(dialog, selectmode=tk.MULTIPLE)
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for game in steam_games:
                listbox.insert(tk.END, game)
            
            def add_selected_games():
                selected_indices = listbox.curselection()
                for index in selected_indices:
                    game_path = steam_games[index]
                    if game_path not in vars.time_group[vars.time_var]['programs']:
                        vars.time_group[vars.time_var]['programs'].append(game_path)
                
                self.update_time_display()
                dialog.destroy()
                messagebox.showinfo("Added", "Selected games have been added to the blocklist")
            
            ttk.Button(dialog, text="Add Selected Games", command=add_selected_games).pack(pady=10)
            ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)
            ttk.Button(dialog, text="Select All", command=lambda: listbox.select_set(0, tk.END)).pack(pady=5)
        else:
            messagebox.showinfo("No Games Found", "No Steam games were found on this computer.")
            
    def find_epic_games_helper(self):
        epic_games= helper_funcs.find_epic_games()
        if epic_games:
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Epic Games")
            dialog.geometry("400x300+700+400")
            dialog.transient(self.root)
            
            listbox = tk.Listbox(dialog, selectmode=tk.MULTIPLE)
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for game in epic_games:
                listbox.insert(tk.END, game)
            
            def add_selected_games():
                selected_indices = listbox.curselection()
                for index in selected_indices:
                    game_path = epic_games[index]
                    if game_path not in vars.time_group[vars.time_var]['programs']:
                        vars.time_group[vars.time_var]['programs'].append(game_path)
                
                self.update_time_display()
                dialog.destroy()
                messagebox.showinfo("Added", "Selected games have been added to the blocklist")
            
            ttk.Button(dialog, text="Add Selected Games", command=add_selected_games).pack(pady=10)
            ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)
            ttk.Button(dialog, text="Select All", command=lambda: listbox.select_set(0, tk.END)).pack(pady=5)
        else:
            messagebox.showinfo("No Games Found", "No Epic games were found on this computer.")      
             
    def remove_replacement(self):
            selection = self.replacement_list.curselection()
            selection: str= self.replacement_list.get(selection[0])
            if selection in vars.time_group[vars.time_var]["productive"]:
                vars.time_group[vars.time_var]["productive"].remove(selection)
                self.update_replacement_listbox()
            else:
                messagebox.showerror("Error!", "The selected item does not exist or there was no selection",icon='error')
    
    def swap_out_widgets(self, obj1, obj2, obj3=None,**kwargs):
        if obj1.winfo_ismapped():
            obj2.pack(**kwargs)
            obj1.pack_forget()
        else:
            obj1.pack(**kwargs)
            obj2.pack_forget()
        if obj3 != None:
            obj3.pack_forget()
            obj3.pack(side='bottom')
            
    def enter_replacement(self, entry:str): 
        if entry==  "#Sleep PC" or entry== "#Shutdown PC":
            if messagebox.askyesno("New Addition", f"Would you like to add '{entry[1:]}' to the list of replacements?", icon= "warning"):
                vars.time_group[vars.time_var]["productive"].append(entry)
                vars.time_group[vars.time_var]["select_type"]= 'Queue'  if not self.shuffle_select.winfo_ismapped() else "Random"
                self.update_replacement_listbox()
        elif entry!= "Enter Website" or entry !=''or ' ' in entry:
            domain= entry.split('/')[:min(2,len(entry.split('/')))]
            entry= ''.join(domain)
            entry= entry if entry.startswith("www.") else "www." + entry
            if messagebox.askokcancel("Testing", "Opening Website for confirmation...\n OK to open website. Cancel to skip this step."):
                webbrowser.open(entry)
            if messagebox.askyesno("New Addition", "Would you like to add this to the list of replacements?"):
                
                vars.time_group[vars.time_var]["productive"].append(entry)
                vars.time_group[vars.time_var]["select_type"]= 'Queue'  if not self.shuffle_select.winfo_ismapped() else "Random"
                
                self.update_replacement_listbox()
            
        else:
            messagebox.showwarning("Error!", "The input must be non-empty without spaces",icon='error')
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=vars.root_dir,
            title="Select a program executable",
            filetypes=[ ("All files", "*.*"),("Executable files", "*.exe")]
        )
        if file_path!='':
            if messagebox.askokcancel("Testing", "Opening Website for confirmation..."):
                from win32api import ShellExecute
                ShellExecute(0, 'open',file_path,'','',1) 
            if messagebox.askyesno("New Addition", "Would you like to add this to the list of replacements?"):                
                vars.time_group[vars.time_var]["productive"].append(file_path)
                vars.time_group[vars.time_var]["select_type"]= 'Queue' if not self.shuffle_select.winfo_ismapped() else "Random"

                self.update_replacement_listbox()
        else:
            messagebox.showwarning("Error!", "There was no file given or it could be found",icon='error')
            
    def update_replacement_listbox(self):
        if self.replacement_list:
            self.replacement_list.delete(0,tk.END)
            self.replacement_list.insert(tk.END,*vars.time_group[vars.time_var]['productive'])
            
    def update_time_display(self):
        if vars.time_var and vars.time_var in vars.session_temp.get('time_list', {}):
            time_data = vars.time_group[vars.time_var]
             
            # Update name
            name = time_data.get('name', '')
            self.name_var.set(name)
            self.enabled_var.set(time_data.get('enabled', True))
             
            end_time = time_data.get('end_time', '00:00')
            allowed_time = time_data.get('allowed_time', 0)/360
             
            self.hour_var.set(vars.time_var[:2])
            self.minute_var.set(vars.time_var[3:])
            self.end_hour_var.set(end_time[:2])
            self.end_minute_var.set(end_time[3:])
            self.allowed_hours.set(allowed_time)
            
            
            # Update program list
            self.program_listbox.delete(0, tk.END)
            for program in time_data.get('programs', []):
                self.program_listbox.insert(tk.END, program)
    
    def add_program(self):
        program = self.program_entry.get().strip()
        if program == "":
            messagebox.showwarning("Input Error", "Program name cannot be empty")
            return
        if program and vars.time_var:
            if vars.time_var in vars.session_temp.get('time_list', {}):
                programs = vars.time_group[vars.time_var]['programs']
                if program not in programs:
                    programs.append(program)
                    self.program_entry.delete(0, tk.END)
                    self.update_time_display()
                    messagebox.showinfo("Success", f"Added {program}")
    
    def remove_program(self):
        program = self.select_program(None)
        programs = vars.time_group[vars.time_var]['programs']
        if program in programs:
            programs.remove(program)
            self.update_time_display()
            messagebox.showinfo("Removed", f"Removed {program}")

    def save_time_settings(self):
        try:
            if vars.time_var and vars.time_var in vars.session_temp.get('time_list', {}):
                time_data = vars.time_group[vars.time_var]
                
                # Save name
                name = self.name_var.get().strip()
                if name:
                    time_data['name'] = name
                
                # Validate and save time
                end_time = f"{self.end_hour_var.get().zfill(2)}:{self.end_minute_var.get().zfill(2)}"
                
                time_data['end_time'] = end_time
                
                # Save enabled state
                time_data['enabled'] = self.enabled_var.get()

                # Save action when finished
                time_data['on_finish']= self.finish_options.index(self.finish_var.get())
                
                # Save days
                selected_days = [day for day, var in self.day_vars.items() if var.get()]
                vars.session_temp['days'] = selected_days
                 
                # Save allowed time
                allowed_time = self.allowed_hours.get()
                time_data['allowed_time'] = float(allowed_time)*360

                # Save to JSON
                with open(vars.json_path, "w", encoding="utf-8") as f:
                    json.dump(vars.session_temp, f, indent=2)
                
                messagebox.showinfo("Saved", "Time settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")
    
    def update_blacklist_display(self):
        if self.blacklist_display:
            self.blacklist_display.delete(0, tk.END)
            if vars.session_temp.get('time_list'):
                for time_key, time_data in vars.time_group.items():
                    # Get name and programs
                    name = time_data.get('name')
                    end_time = time_data.get('end_time', '23:59')
                    programs = time_data.get('programs', [])
                    
                    # Display nickname if given, otherwise show time_key
                    status = " [DISABLED]" if not time_data.get('enabled', True) else ""
                    if name:
                        self.blacklist_display.insert(tk.END, f"{name} ({time_key} - {end_time}){status}")
 
                    # Always show time range
                    else:
                        self.blacklist_display.insert(tk.END, f"{time_key} - {end_time}{status}")
                    
                    # Show only first 2 programs
                    for i, program in enumerate(programs[:2]):
                        self.blacklist_display.insert(tk.END, f"  - {program}")
                    
                    # Add ellipsis if there are more than 2 programs
                    if len(programs) > 2:
                        self.blacklist_display.insert(tk.END, f"  ...")
                    
                    # Add blank line between time groups
                    self.blacklist_display.insert(tk.END, "")
    
    def update_time_list(self):
        if self.time_listbox:
            self.time_listbox.delete(0, tk.END)
            for time_key in vars.time_group:
                end = vars.time_group[time_key].get('end_time', '23:59')
                status = " [DISABLED]" if not vars.time_group[time_key].get('enabled', True) else ""
                if vars.time_group[time_key].get('name'):
                    display_name = vars.time_group[time_key]['name']
                    self.time_listbox.insert(tk.END, f"{display_name} ({time_key} - {end}){status}")
                else:
                    self.time_listbox.insert(tk.END, f"{time_key} - {end}{status}")
    
   
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def exit(self):
        try:
            with open(vars.json_path, "w", encoding="utf-8") as f:
                json.dump(vars.session_temp, f, indent=2)
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")


def main():
    
    root = tk.Tk()
    app = FocusModeUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
