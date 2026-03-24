"""
Focus Mode - Program Blacklist Manager
Tkinter-based UI for managing application blocking schedules
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import webbrowser
import sys
from datetime import datetime

# Import custom modules
from Text_Edit import Text_Edit
from Button import Button
import vars
from helper_funcs import get_active_texts


class FocusModeUI:
    """Main UI class for Focus Mode"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Mode")
        self.root.geometry("800x700")
        vars.root = root
        
        # Initialize state
        self.time_buttons_frame = None
        self.blacklist_buttons_frame = None
        self.current_view = "main"
        
        # Create main UI
        self.create_main_view()
    
    def create_main_view(self):
        """Create the main blacklist management view"""
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
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Buttons (smaller, fixed width)
        left_panel = ttk.Frame(content_frame, width=150)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_panel.pack_propagate(False)
        
        self.blacklist_buttons_frame = ttk.Frame(left_panel)
        self.blacklist_buttons_frame.pack(fill=tk.X)
        
        Button(self.blacklist_buttons_frame, x=0, y=0, text="Add", 
               command=self.add_to_time_list, bg_color="red", fg_color="white", font=("Arial", 9), width=12) #change to adda new time on other screen
        Button(self.blacklist_buttons_frame, x=1, y=0, text="Remove", 
               command=self.remove_from_timelist, bg_color="red", fg_color="white", font=("Arial", 9), width=12)
        Button(self.blacklist_buttons_frame, x=2, y=0, text="Settings", 
               command=self.enter_time_settings, bg_color="orange", fg_color="white", font=("Arial", 9), width=12)
        Button(self.blacklist_buttons_frame, x=3, y=0, text="Help", 
               command=self.help, bg_color="blue", fg_color="white", font=("Arial", 9), width=12)
        Button(self.blacklist_buttons_frame, x=4, y=0, text="Save & Exit", 
               command=self.exit, bg_color="green", fg_color="white", font=("Arial", 9), width=12)
        
        # Right panel - List display (smaller)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        list_label = tk.Label(right_panel, text="Ban start times", font=("Arial", 11,))
        list_label.pack(fill=tk.X)
        
        # Listbox for blacklist (reduced size)
        self.blacklist_display = tk.Listbox(right_panel, height=15, width=35, font=("Arial", 9))
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.blacklist_display.yview)
        self.blacklist_display.config(yscrollcommand=scrollbar.set)
        self.blacklist_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.blacklist_display.bind("<<ListboxSelect>>", self.select)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.update_blacklist_display()
    
    def create_time_settings_view(self):
        """Create the time settings management view"""
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
        left_panel.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=5, pady=5, anchor=tk.NW)
        
        tk.Label(left_panel, text="Time Groups", font=("Arial", 12, "bold")).pack(fill=tk.X)
        
        # Frame for listbox and scrollbar
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.Y, expand=False, padx=0, pady=5)
        
        self.time_listbox = tk.Listbox(list_frame, height=30, width=30)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.time_listbox.yview)
        self.time_listbox.config(yscrollcommand=scrollbar.set)
        self.time_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.time_listbox.bind("<<ListboxSelect>>", self.select_time)
        
        self.update_time_list()
        
        # Button frame for actions
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(button_frame, text= "Set Replacement Program/Site",command= self.change_replacement).pack( padx=2, fill=tk.X,side= 'top')
        ttk.Button(button_frame, text="New", command=self.new_time_group).pack(side=tk.LEFT, padx=2, fill=tk.X)
        
        # Right panel - Settings (visible by default)
        right_panel = ttk.Frame(main_container,width=10)
        right_panel.pack(side=tk.RIGHT,  padx=5, pady=5, anchor =tk.N)
        
        # Name input section
        name_frame = ttk.LabelFrame(right_panel, text="Name")
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        self.name_var = tk.StringVar(value="")
        ttk.Entry(name_frame, textvariable=self.name_var, width=20).pack(fill=tk.X, padx=5, pady=5)
        
        # Time input section
        time_frame = ttk.LabelFrame(right_panel, text="Time Range")
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(time_frame, text="Start Time (HH:MM):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(time_frame, text="End Time (HH:MM):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.end_hour_var = tk.StringVar(value="00")
        self.end_minute_var = tk.StringVar(value="00")
        
        ttk.Entry(time_frame, textvariable=self.hour_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(time_frame, text=":").grid(row=0, column=2)
        ttk.Entry(time_frame, textvariable=self.minute_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Entry(time_frame, textvariable=self.end_hour_var, width=5).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(time_frame, text=":").grid(row=1, column=2)
        ttk.Entry(time_frame, textvariable=self.end_minute_var, width=5).grid(row=1, column=3, padx=5, pady=5)
        
        # Day selection
        days_frame = ttk.LabelFrame(right_panel, text="Active Days")
        days_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.day_vars = {}
        for i, day in enumerate(vars.selected_days):
            var = tk.BooleanVar(value=True)
            self.day_vars[day] = var
            ttk.Checkbutton(days_frame, text=day, variable=var).grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=3)
        
        # Program blacklist for this time
        programs_frame = ttk.LabelFrame(right_panel, text="Programs to Block")
        programs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.program_listbox = tk.Listbox(programs_frame, height=8)
        prog_scrollbar = ttk.Scrollbar(programs_frame, orient=tk.VERTICAL, command=self.program_listbox.yview)
        self.program_listbox.config(yscrollcommand=prog_scrollbar.set)
        self.program_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Program input
        prog_input_frame = ttk.Frame(right_panel)
        prog_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.program_entry = ttk.Entry(prog_input_frame)
        self.program_entry.grid(row=1, column=1, padx=5)
        
        ttk.Button(prog_input_frame, text="Enter", command=self.add_program).grid(row=1, column=2, padx=5)
        ttk.Button(prog_input_frame, text="Browse...", command=self.add_to_blacklist).grid(row=1, column=3, padx=5)
        ttk.Button(prog_input_frame, text="Remove Selected", command=self.remove_program).grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self.save_time_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back", command=self.create_main_view).pack(side=tk.LEFT, padx=5)
    
    
    def add_to_blacklist(self):
        """Add a program to the blacklist"""
        file_path = filedialog.askopenfilename(
            initialdir="C:\\",
            title="Select a program executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            executable = file_path.split("\\")[-1]
            if vars.session_temp.get('time_list', {}) and vars.time_var in vars.session_temp['time_list']:
                programs = vars.session_temp['time_list'][vars.time_var]['programs']
                if executable not in programs:
                    programs.append(executable)
                    self.update_blacklist_display()
                    messagebox.showinfo("Success", f"Added {executable} to blacklist")
                else:
                    messagebox.showwarning("Duplicate", f"{executable} is already in the list")
   
    def add_to_time_list(self):
        self.new_time_group()
        
    def parse_selected_time(self, time_str:str) -> str:
        """Parse time string to extract key"""
        if " (" in time_str:
            return time_str.split(" (")[1].split(" - ")[0]
        return time_str.split(" - ")[0]
    
    def remove_from_timelist(self):
        """Remove selected program from blacklist"""
        if self.current_view == "main":
            if self.select(None)!=False: #test this
                item = self.select(None)
                if vars.session_temp.get('time_list', {}) and vars.time_var in vars.session_temp['time_list']:
                    times = vars.session_temp['time_list']
                    if item in times:
                        times.remove(item)
                        self.update_blacklist_display()
                        messagebox.showinfo("Removed", f"Removed {item}")
    
    def enter_time_settings(self):
        """Enter time settings view"""
        if vars.session_temp.get('time_list'):
            self.create_time_settings_view()
        else:
            messagebox.showwarning("No Times", "Please add time groups first")
            
    def select(self,event):
        """Select a time group"""
        selection = self.blacklist_display.curselection()
    
        if selection:
            selection :str = self.blacklist_display.get(selection[0])
            selection =self.parse_selected_time(selection)
            vars.time_var = selection
            return selection
        return False
            
    def select_time(self, event):
        """Select a time group"""
        selection = self.time_listbox.curselection()
    
        if selection:
            selection :str = self.time_listbox.get(selection[0])
            selection =self.parse_selected_time(selection)
            vars.time_var = selection
            self.update_time_display()
            return selection
        return False
    
   
    def new_time_group(self):
        """Create a new time group"""
        # Create a dialog for time and name input
        dialog = tk.Toplevel(self.root)
        dialog.title("New Time Group")
        dialog.geometry("350x220")
        dialog.transient(self.root)
        dialog.grab_set()
        
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
                
                if time_key in vars.session_temp['time_list']:
                    messagebox.showwarning("Duplicate", f"Time {time_key} already exists")
                    return
                
                name = name_var.get().strip() or time_key
                
                # Add new time group with default values
                vars.session_temp['time_list'][time_key] = {
                    "name": name,
                    "programs": [],
                    "end_time": "23:59",
                    "days": vars.selected_days.copy()
                }
                
                self.update_time_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Created new time group: {time_key}")
                
            except ValueError:
                messagebox.showerror("Invalid", "Please enter valid numbers for time")
        
        ttk.Button(button_frame, text="Create", command=add_time).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def change_replacement(self):
        pass
    
    
    def update_time_display(self):
        """Update the time and program display"""
        if vars.time_var and vars.time_var in vars.session_temp.get('time_list', {}):
            time_data = vars.session_temp['time_list'][vars.time_var]
            
            # Update name
            name = time_data.get('name', vars.time_var)
            self.name_var.set(name)
            
            # start_time = time_data.get('start_time', '00:00')
            end_time = time_data.get('end_time', '00:00')
            
            self.hour_var.set(vars.time_var[:2])
            self.minute_var.set(vars.time_var[3:])
            self.end_hour_var.set(end_time[:2])
            self.end_minute_var.set(end_time[3:])
            
            # Update program list
            self.program_listbox.delete(0, tk.END)
            for program in time_data.get('programs', []):
                self.program_listbox.insert(tk.END, program)
    
    def add_program(self):
        """Add a program to the current time group"""
        program = self.program_entry.get().strip()
        if program and vars.time_var:
            if vars.time_var in vars.session_temp.get('time_list', {}):
                programs = vars.session_temp['time_list'][vars.time_var]['programs']
                if program not in programs:
                    programs.append(program)
                    self.program_entry.delete(0, tk.END)
                    self.update_time_display()
                    messagebox.showinfo("Success", f"Added {program}")
    
    def remove_program(self):
        """Remove selected program from current time group"""
        if self.select_time(None):
            program = self.select_time(None)
            programs = vars.session_temp['time_list'][vars.time_var]['programs']
            if program in programs:
                programs.remove(program)
                self.update_time_display()
                messagebox.showinfo("Removed", f"Removed {program}")
    
    def save_time_settings(self):
        """Save time settings"""
        try:
            if vars.time_var and vars.time_var in vars.session_temp.get('time_list', {}):
                time_data = vars.session_temp['time_list'][vars.time_var]
                
                # Save name
                name = self.name_var.get().strip()
                if name:
                    time_data['name'] = name
                
                # Validate and save time
                end_time = f"{self.end_hour_var.get().zfill(2)}:{self.end_minute_var.get().zfill(2)}"
                
                time_data['end_time'] = end_time
                
                # Save days
                selected_days = [day for day, var in self.day_vars.items() if var.get()]
                vars.session_temp['days'] = selected_days
                
                # Save to JSON
                with open(vars.json_path, "w", encoding="utf-8") as f:
                    json.dump(vars.session_temp, f, indent=2)
                
                messagebox.showinfo("Saved", "Time settings saved successfully")
                self.create_main_view()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")
    
    def update_blacklist_display(self):
        """Update the blacklist display"""
        if self.blacklist_display:
            self.blacklist_display.delete(0, tk.END)
            if vars.session_temp.get('time_list'):
                for time_key, time_data in vars.session_temp['time_list'].items():
                    # Get name and programs
                    name = time_data.get('name')
                    end_time = time_data.get('end_time', '23:59')
                    programs = time_data.get('programs', [])
                    
                    # Display nickname if given, otherwise show time_key
                    if name:
                        self.blacklist_display.insert(tk.END, f"{name} ({time_key} - {end_time})")

                    # Always show time range
                    else:
                        self.blacklist_display.insert(tk.END, f"{time_key} - {end_time}")
                    
                    # Show only first 2 programs
                    for i, program in enumerate(programs[:2]):
                        self.blacklist_display.insert(tk.END, f"  - {program}")
                    
                    # Add ellipsis if there are more than 2 programs
                    if len(programs) > 2:
                        self.blacklist_display.insert(tk.END, f"  ...")
                    
                    # Add blank line between time groups
                    self.blacklist_display.insert(tk.END, "")
    
    def update_time_list(self):
        """Update time list display"""
        if self.time_listbox:
            self.time_listbox.delete(0, tk.END)
            for time_key in vars.time_group:
                end = vars.time_group[time_key].get('end_time', '23:59')
                if vars.time_group[time_key].get('name'):
                    display_name = vars.time_group[time_key]['name']
                    
                    self.time_listbox.insert(tk.END, f"{display_name} ({time_key} - {end})")
                else:
                    self.time_listbox.insert(tk.END, f"{time_key} - {end}")
    
    def help(self):
        """Open help"""
        webbrowser.open('https://github.com/Tomi-Cant/focus_mode') # remember to change it
    
    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def exit(self):
        """Save and exit"""
        try:
            with open(vars.json_path, "w", encoding="utf-8") as f:
                json.dump(vars.session_temp, f, indent=2)
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FocusModeUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
