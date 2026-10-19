# Made By: Tomi Banjoko
# Purpose: helps users focus by closing programs at set times and days, can be used for work, school, or just to limit distractions
# Date: 08/12/2025

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import shutil
from tkinter import dialog
from urllib.parse import urlparse
import helper_funcs
import webbrowser

# Import custom modules
from Button import Button
import vars


def _strip_non_ascii(text: str) -> str:
    return text.encode("ascii", "ignore").decode("ascii")


class FocusModeUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Focused Up")
        self.root.iconbitmap("focused_up_logo.ico")
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

        self.root.geometry("800x620+500+100")
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        palette = {
            "canvas": "#F1F5F1",
            "ink": "#183B36",
            "muted": "#60736D",
            "teal": "#187B70",
            "teal_hover": "#12665D",
            "coral": "#C6534C",
            "coral_hover": "#A9403A",
            "gold": "#E3A63A",
            "gold_hover": "#C88C25",
            "blue": "#397B8A",
            "blue_hover": "#2D6572",
            "orange": "#D8753C",
            "orange_hover": "#BD5F2D",
            "slate": "#526A68",
            "slate_hover": "#405654",
        }

        header = tk.Frame(main_container, bg=palette["ink"], padx=18, pady=14)
        header.pack(fill=tk.X, padx=5, pady=(0, 12))
        tk.Label(
            header,
            text="Focused Up",
            font=("Segoe UI", 22, "bold"),
            fg="#FFFFFF",
            bg=palette["ink"],
        ).pack(anchor=tk.W)
        tk.Frame(header, bg=palette["gold"], height=3).pack(fill=tk.X, pady=(8, 0))

        content_frame = tk.Frame(main_container, bg=palette["canvas"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_panel = tk.Frame(content_frame, bg=palette["canvas"], width=185)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14), pady=5)
        left_panel.pack_propagate(False)

        self.blacklist_buttons_frame = ttk.Frame(left_panel)
        self.blacklist_buttons_frame.pack(fill=tk.X, pady=(0, 8))

        def add_action_button(row, text, command, color, hover, foreground="#FFFFFF"):
            button = Button(
                self.blacklist_buttons_frame,
                x=row,
                y=0,
                text=text,
                command=command,
                bg_color=color,
                fg_color=foreground,
                font=("Segoe UI", 10),
                width=14,
                height=2,
            )
            button.configure(
                relief=tk.FLAT,
                borderwidth=0,
                activebackground=hover,
                activeforeground=foreground,
                cursor="hand2",
            )
            button.bind("<Enter>", lambda event, shade=hover: event.widget.configure(bg=shade))
            button.bind("<Leave>", lambda event, shade=color: event.widget.configure(bg=shade))
            return button

        add_action_button(0, "Add", self.add_to_time_list, palette["teal"], palette["teal_hover"])
        add_action_button(1, "Remove", self.remove_from_timelist, palette["coral"], palette["coral_hover"])
        add_action_button(
            2,
            "Edit Properties",
            self.create_time_settings_view,
            palette["gold"],
            palette["gold_hover"],
            foreground=palette["ink"],
        )
        add_action_button(4, "Save & Exit", self.exit, palette["teal"], palette["teal_hover"])
        add_action_button(
            5,
            "Contact Support",
            helper_funcs.contact_support,
            palette["blue"],
            palette["blue_hover"],
        )
        add_action_button(6, "Help", self.create_tutorial_view, palette["orange"], palette["orange_hover"])
        add_action_button(
            7,
            "Sound Settings",
            self.open_audio_settings,
            palette["slate"],
            palette["slate_hover"],
        )

        right_panel = tk.Frame(content_frame, bg=palette["canvas"])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)

        list_label = tk.Label(
            right_panel,
            text="Your schedules",
            font=("Segoe UI", 13, "bold"),
            fg=palette["ink"],
            bg=palette["canvas"],
            anchor=tk.W,
        )
        list_label.pack(fill=tk.X, padx=2, pady=(0, 7))

        list_frame = tk.Frame(right_panel, bg=palette["canvas"])
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.blacklist_display = tk.Listbox(
            list_frame,
            height=18,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg=palette["ink"],
            selectbackground=palette["teal"],
            selectforeground="#FFFFFF",
            activestyle="none",
            highlightthickness=1,
            highlightbackground="#D5E0DA",
            highlightcolor=palette["teal"],
            relief=tk.FLAT,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(right_panel, orient=tk.VERTICAL, command=self.blacklist_display.yview)
        self.blacklist_display.config(yscrollcommand=scrollbar.set)
        self.blacklist_display.pack(in_=list_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.blacklist_display.bind("<<ListboxSelect>>", self.select)
        scrollbar.bind("<MouseWheel>", lambda event: self.blacklist_display.yview_scroll(int(-1*(event.delta/120)), "units"))

        scrollbar.pack(in_=list_frame, side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            right_panel,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg=palette["coral"],
            bg=palette["canvas"],
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, pady=(7, 0))

        self.toggle_enabled_button = add_action_button(
            3,
            "Disable",
            self.toggle_time_group_enabled,
            palette["slate"],
            palette["slate_hover"],
        )
        self.toggle_enabled_button.grid_remove()

        self.update_blacklist_display()
    
    def create_time_settings_view(self):
        self.clear_window()
        self.current_view = "time_settings"
        self.root.geometry("800x620+500+100")

        palette = {
            "canvas": "#F1F5F1",
            "ink": "#183B36",
            "muted": "#60736D",
            "teal": "#187B70",
            "teal_hover": "#12665D",
            "gold": "#E3A63A",
            "slate": "#526A68",
            "slate_hover": "#405654",
            "border": "#D5E0DA",
        }

        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header = tk.Frame(main_container, bg=palette["ink"], padx=18, pady=12)
        header.pack(fill=tk.X, padx=5, pady=(0, 10))
        tk.Label(
            header,
            text="Time Settings",
            font=("Segoe UI", 20, "bold"),
            fg="#FFFFFF",
            bg=palette["ink"],
        ).pack(anchor=tk.W)
        tk.Frame(header, bg=palette["gold"], height=3).pack(fill=tk.X, pady=(7, 0))

        def make_action_button(parent, text, command, color, hover, foreground="#FFFFFF"):
            button = tk.Button(
                parent,
                text=text,
                command=command,
                font=("Segoe UI", 10),
                bg=color,
                fg=foreground,
                activebackground=hover,
                activeforeground=foreground,
                relief=tk.FLAT,
                borderwidth=0,
                padx=12,
                pady=7,
                cursor="hand2",
            )
            button.bind("<Enter>", lambda event, shade=hover: event.widget.configure(bg=shade))
            button.bind("<Leave>", lambda event, shade=color: event.widget.configure(bg=shade))
            return button

        button_frame = tk.Frame(main_container, bg=palette["canvas"])
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(8, 0))
        make_action_button(
            button_frame,
            "Back",
            self.create_main_view,
            palette["slate"],
            palette["slate_hover"],
        ).pack(side=tk.RIGHT, padx=(6, 0))
        make_action_button(
            button_frame,
            "Save",
            self.save_time_settings,
            palette["teal"],
            palette["teal_hover"],
        ).pack(side=tk.RIGHT)

        notebook_style = ttk.Style(self.root)
        notebook_style.configure("FocusedUp.TNotebook", tabmargins=(0, 2, 0, 0))
        notebook_style.configure(
            "FocusedUp.TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 8),
        )
        notebook = ttk.Notebook(main_container, style="FocusedUp.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        schedule_tab = ttk.Frame(notebook)
        programs_tab = ttk.Frame(notebook)
        notebook.add(schedule_tab, text="Schedule")
        notebook.add(programs_tab, text="Programs to Block")

        def create_scrollable_tab(tab):
            canvas = tk.Canvas(tab, bg=palette["canvas"], highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            content = tk.Frame(canvas, bg=palette["canvas"], padx=10, pady=10)
            content_window = canvas.create_window((0, 0), window=content, anchor="nw")
            content.bind(
                "<Configure>",
                lambda event, target=canvas: target.configure(scrollregion=target.bbox("all")),
            )
            canvas.bind(
                "<Configure>",
                lambda event, target=canvas, window=content_window: target.itemconfigure(
                    window, width=event.width
                ),
            )
            
            return canvas, content

        schedule_canvas, schedule_content = create_scrollable_tab(schedule_tab)
        programs_canvas, programs_content = create_scrollable_tab(programs_tab)

        groups_frame = ttk.LabelFrame(schedule_content, text="Time Groups", padding=8)
        groups_frame.pack(fill=tk.X, pady=(0, 8))

        list_frame = ttk.Frame(groups_frame)
        list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        groups_frame.columnconfigure(0, weight=1)
        groups_frame.rowconfigure(0, weight=1)

        self.time_listbox = tk.Listbox(
            list_frame,
            height=3,
            width=30,
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg=palette["ink"],
            selectbackground=palette["teal"],
            selectforeground="#FFFFFF",
            activestyle="none",
            highlightthickness=1,
            highlightbackground=palette["border"],
            highlightcolor=palette["teal"],
            relief=tk.FLAT,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.time_listbox.yview)
        self.time_listbox.config(yscrollcommand=scrollbar.set)
        self.time_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.time_listbox.bind("<<ListboxSelect>>", self.select_time)
        self.update_time_list()

        group_actions = ttk.Frame(groups_frame)
        group_actions.grid(row=0, column=1, rowspan=2, sticky="nsew")
        group_actions.columnconfigure(0, weight=1)
        make_action_button(
            group_actions,
            "Set Replacement Program/Site",
            self.change_replacement,
            palette["slate"],
            palette["slate_hover"],
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))
        make_action_button(
            group_actions,
            "New",
            self.new_time_group,
            palette["teal"],
            palette["teal_hover"],
        ).grid(row=1, column=0, sticky="ew", pady=(0, 4))
        make_action_button(
            group_actions,
            "Remove",
            self.remove_from_timelist,
            "#C6534C",
            "#A9403A",
        ).grid(row=2, column=0, sticky="ew")

        settings_frame = ttk.Frame(schedule_content)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)

        name_frame = ttk.LabelFrame(settings_frame, text="Group", padding=8)
        name_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.name_var = tk.StringVar(value="")
        ttk.Entry(name_frame, textvariable=self.name_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            name_frame,
            text="Enabled",
            variable=self.enabled_var,
            command=lambda: self.toggle_time_group_enabled(),
        ).grid(row=0, column=1, sticky=tk.W)
        name_frame.columnconfigure(0, weight=1)

        time_frame = ttk.LabelFrame(settings_frame, text="Time Range", padding=8)
        time_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4), pady=(0, 8))
        ttk.Label(time_frame, text="Start").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        ttk.Label(time_frame, text="End").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        ttk.Label(time_frame, text="Allowed hours").grid(
            row=2, column=0, sticky=tk.W, padx=4, pady=3
        )
        self.hour_var = tk.StringVar(value="00")
        self.minute_var = tk.StringVar(value="00")
        self.end_hour_var = tk.StringVar(value="00")
        self.end_minute_var = tk.StringVar(value="00")
        self.allowed_hours = tk.DoubleVar(value=0.0)

        ttk.Entry(time_frame, textvariable=self.hour_var, width=4).grid(row=0, column=1, padx=2)
        ttk.Label(time_frame, text=":").grid(row=0, column=2)
        ttk.Entry(time_frame, textvariable=self.minute_var, width=4).grid(row=0, column=3, padx=2)
        ttk.Entry(time_frame, textvariable=self.end_hour_var, width=4).grid(row=1, column=1, padx=2)
        ttk.Label(time_frame, text=":").grid(row=1, column=2)
        ttk.Entry(time_frame, textvariable=self.end_minute_var, width=4).grid(row=1, column=3, padx=2)
        ttk.Entry(time_frame, textvariable=self.allowed_hours, width=7).grid(
            row=2, column=1, columnspan=3, sticky="w", padx=2
        )

        days_frame = ttk.LabelFrame(settings_frame, text="Active Days", padding=8)
        days_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(0, 8))
        self.day_vars = {}
        for i, day in enumerate(vars.selected_days):
            var = tk.BooleanVar(value=True)
            self.day_vars[day] = var
            ttk.Checkbutton(days_frame, text=day, variable=var).grid(
                row=i // 2, column=i % 2, sticky=tk.W, padx=8, pady=3
            )
        days_frame.columnconfigure(0, weight=1)
        days_frame.columnconfigure(1, weight=1)

        warnings_frame = ttk.LabelFrame(settings_frame, text="Warnings Before End", padding=8)
        warnings_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.warning_vars = {
            minutes: tk.BooleanVar(value=True)
            for minutes in vars.warning_time_minutes
        }
        for index, minutes in enumerate(vars.warning_time_minutes):
            ttk.Checkbutton(
                warnings_frame,
                text=f"{minutes} min",
                variable=self.warning_vars[minutes],
            ).grid(row=index // 4, column=index % 4, sticky=tk.W, padx=8, pady=3)
        for column in range(4):
            warnings_frame.columnconfigure(column, weight=1)

        start_frame = ttk.LabelFrame(settings_frame, text="When Started", padding=8)
        start_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.start_var = tk.StringVar(value="Nothing")
        self.start_options = ["Nothing", "Custom"]
        ttk.OptionMenu(
            start_frame,
            self.start_var,
            "Nothing",
            *self.start_options,
            command=self.update_custom_start_controls,
        ).pack(fill=tk.X)

        self.start_type_var = tk.StringVar(value="website")
        self.start_target_var = tk.StringVar(value="")
        self.start_target_label_var = tk.StringVar(value="Website URL")
        self.custom_start_frame = ttk.Frame(start_frame)
        ttk.Label(self.custom_start_frame, text="Open:").grid(
            row=0, column=0, sticky=tk.W, pady=(6, 2)
        )
        ttk.Radiobutton(
            self.custom_start_frame,
            text="Website",
            variable=self.start_type_var,
            value="website",
            command=self.update_custom_start_controls,
        ).grid(row=0, column=1, sticky=tk.W, pady=(6, 2))
        ttk.Radiobutton(
            self.custom_start_frame,
            text="Application",
            variable=self.start_type_var,
            value="application",
            command=self.update_custom_start_controls,
        ).grid(row=0, column=2, sticky=tk.W, pady=(6, 2))
        ttk.Label(self.custom_start_frame, textvariable=self.start_target_label_var).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 6)
        )
        ttk.Entry(self.custom_start_frame, textvariable=self.start_target_var).grid(
            row=1, column=1, sticky="ew"
        )
        self.start_browse_button = ttk.Button(
            self.custom_start_frame,
            text="Browse...",
            command=self.browse_start_application,
        )
        self.start_browse_button.grid(row=1, column=2, padx=(6, 0))
        self.custom_start_frame.columnconfigure(1, weight=1)
        self.update_custom_start_controls()

        finish_frame = ttk.LabelFrame(settings_frame, text="When Finished", padding=8)
        finish_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.finish_var = tk.StringVar(value="Nothing")
        self.finish_options = ["Nothing", "Shutdown PC", "Sleep PC", "Custom"]
        ttk.OptionMenu(
            finish_frame,
            self.finish_var,
            "Nothing",
            *self.finish_options,
            command=self.update_custom_finish_controls,
        ).pack(fill=tk.X)

        self.finish_type_var = tk.StringVar(value="website")
        self.finish_target_var = tk.StringVar(value="")
        self.finish_target_label_var = tk.StringVar(value="Website URL")
        self.custom_finish_frame = ttk.Frame(finish_frame)
        ttk.Label(self.custom_finish_frame, text="Open:").grid(
            row=0, column=0, sticky=tk.W, pady=(6, 2)
        )
        ttk.Radiobutton(
            self.custom_finish_frame,
            text="Website",
            variable=self.finish_type_var,
            value="website",
            command=self.update_custom_finish_controls,
        ).grid(row=0, column=1, sticky=tk.W, pady=(6, 2))
        ttk.Radiobutton(
            self.custom_finish_frame,
            text="Application",
            variable=self.finish_type_var,
            value="application",
            command=self.update_custom_finish_controls,
        ).grid(row=0, column=2, sticky=tk.W, pady=(6, 2))
        ttk.Label(self.custom_finish_frame, textvariable=self.finish_target_label_var).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 6)
        )
        ttk.Entry(self.custom_finish_frame, textvariable=self.finish_target_var).grid(
            row=1, column=1, sticky="ew"
        )
        self.finish_browse_button = ttk.Button(
            self.custom_finish_frame,
            text="Browse...",
            command=self.browse_finish_application,
        )
        self.finish_browse_button.grid(row=1, column=2, padx=(6, 0))
        self.custom_finish_frame.columnconfigure(1, weight=1)
        self.update_custom_finish_controls()

        programs_heading = tk.Frame(programs_content, bg=palette["canvas"])
        programs_heading.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            programs_heading,
            text="Block list",
            font=("Segoe UI", 14, "bold"),
            fg=palette["ink"],
            bg=palette["canvas"],
        ).pack(anchor=tk.W)

        programs_frame = tk.Frame(
            programs_content,
            bg="#FFFFFF",
            highlightthickness=1,
            highlightbackground=palette["border"],
        )
        programs_frame.pack(fill=tk.BOTH, expand=True)
        self.program_listbox = tk.Listbox(
            programs_frame,
            height=12,
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg=palette["ink"],
            selectbackground=palette["teal"],
            selectforeground="#FFFFFF",
            activestyle="none",
            highlightthickness=1,
            highlightbackground=palette["border"],
            highlightcolor=palette["teal"],
            relief=tk.FLAT,
            borderwidth=0,
        )
        prog_scrollbar = ttk.Scrollbar(programs_frame, orient=tk.VERTICAL, command=self.program_listbox.yview)
        self.program_listbox.config(yscrollcommand=prog_scrollbar.set)
        self.program_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        prog_input_frame = ttk.LabelFrame(programs_content, text="Manage programs", padding=8)
        prog_input_frame.pack(fill=tk.X, pady=(8, 0))
        prog_input_frame.columnconfigure(0, weight=1)
        self.program_entry = ttk.Entry(prog_input_frame)
        self.program_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=4)
        make_action_button(
            prog_input_frame,
            "Enter",
            self.add_program,
            palette["teal"],
            palette["teal_hover"],
        ).grid(row=0, column=1, padx=3, pady=4)
        make_action_button(
            prog_input_frame,
            "Browse...",
            self.add_to_blacklist,
            palette["slate"],
            palette["slate_hover"],
        ).grid(row=0, column=2, padx=3, pady=4)
        make_action_button(
            prog_input_frame,
            "Remove Selected",
            self.remove_program,
            "#C6534C",
            "#A9403A",
        ).grid(row=0, column=3, padx=(8, 0), pady=4)

        game_search_frame = ttk.LabelFrame(programs_content, text="Game libraries", padding=8)
        game_search_frame.pack(fill=tk.X, pady=(8, 0))
        game_search_frame.columnconfigure(0, weight=1, uniform="game-search")
        game_search_frame.columnconfigure(1, weight=1, uniform="game-search")
        make_action_button(
            game_search_frame,
            "Search Steam",
            self.find_steam_games_helper,
            palette["teal"],
            palette["teal_hover"],
        ).grid(row=0, column=0, sticky="ew", padx=(0, 3))
        make_action_button(
            game_search_frame,
            "Search Epic Games",
            self.find_epic_games_helper,
            palette["teal"],
            palette["teal_hover"],
        ).grid(row=0, column=1, sticky="ew", padx=(3, 0))

        def bind_tab_mousewheel(widget, canvas):
            if not isinstance(widget, tk.Listbox):
                widget.bind(
                    "<MouseWheel>",
                    lambda event, target=canvas: target.yview_scroll(
                        -int(event.delta / 120), "units"
                    ),
                    add="+",
                )
            for child in widget.winfo_children():
                bind_tab_mousewheel(child, canvas)

        bind_tab_mousewheel(schedule_content, schedule_canvas)
        bind_tab_mousewheel(programs_content, programs_canvas)

        if vars.time_group:
            self.time_listbox.select_set(0)
            vars.time_var = list(vars.time_group.keys())[0]
            self.update_time_display()
    
    def create_tutorial_view(self):
        self.clear_window()
        self.current_view = "tutorial"
        self.root.geometry("800x620+500+100")

        palette = {
            "canvas": "#F1F5F1",
            "ink": "#183B36",
            "teal": "#187B70",
            "teal_hover": "#12665D",
            "gold": "#E3A63A",
            "orange": "#D8753C",
            "orange_hover": "#BD5F2D",
            "slate": "#526A68",
            "slate_hover": "#405654",
            "border": "#D5E0DA",
        }

        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header = tk.Frame(main_container, bg=palette["ink"], padx=18, pady=14)
        header.pack(fill=tk.X, padx=5, pady=(0, 12))
        tk.Label(
            header,
            text="Focused Up Tutorial",
            font=("Segoe UI", 22, "bold"),
            fg="#FFFFFF",
            bg=palette["ink"],
        ).pack(anchor=tk.W)
        tk.Frame(header, bg=palette["gold"], height=3).pack(fill=tk.X, pady=(8, 0))

        content_frame = tk.Frame(main_container, bg=palette["canvas"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_panel = tk.Frame(content_frame, bg=palette["canvas"], width=185)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14), pady=5)
        left_panel.pack_propagate(False)

        self.blacklist_buttons_frame = ttk.Frame(left_panel)
        self.blacklist_buttons_frame.pack(fill=tk.X, pady=(0, 8))

        def add_action_button(row, text, command, color, hover, foreground="#FFFFFF"):
            button = Button(
                self.blacklist_buttons_frame,
                x=row,
                y=0,
                text=text,
                command=command,
                bg_color=color,
                fg_color=foreground,
                font=("Segoe UI", 10),
                width=14,
                height=2,
            )
            button.configure(
                relief=tk.FLAT,
                borderwidth=0,
                activebackground=hover,
                activeforeground=foreground,
                cursor="hand2",
            )
            button.bind("<Enter>", lambda event, shade=hover: event.widget.configure(bg=shade))
            button.bind("<Leave>", lambda event, shade=color: event.widget.configure(bg=shade))
            return button

        add_action_button(0, "Add", self.tutorial_add, palette["teal"], palette["teal_hover"])
        add_action_button(1, "Remove", self.remove_from_timelist, palette["slate"], palette["slate_hover"])
        add_action_button(
            2,
            "Edit Properties",
            self.create_time_settings_view,
            palette["gold"],
            palette["gold"],
            foreground=palette["ink"],
        )
        add_action_button(3, "Save & Exit", self.exit, palette["teal"], palette["teal_hover"])
        add_action_button(
            4,
            "Sound Settings",
            self.open_audio_settings,
            palette["slate"],
            palette["slate_hover"],
        )
        add_action_button(
            5,
            "Back to Main Menu",
            self.create_main_view,
            palette["orange"],
            palette["orange_hover"],
        )

        right_panel = tk.Frame(content_frame, bg=palette["canvas"])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)

        list_label = tk.Label(
            right_panel,
            text="Tutorial overview",
            font=("Segoe UI", 13, "bold"),
            fg=palette["ink"],
            bg=palette["canvas"],
            anchor=tk.W,
        )
        list_label.pack(fill=tk.X, padx=2, pady=(0, 7))

        list_frame = tk.Frame(right_panel, bg=palette["canvas"])
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.blacklist_display = tk.Listbox(
            list_frame,
            height=18,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg=palette["ink"],
            selectbackground=palette["teal"],
            selectforeground="#FFFFFF",
            activestyle="none",
            highlightthickness=1,
            highlightbackground="#D5E0DA",
            highlightcolor=palette["teal"],
            relief=tk.FLAT,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.blacklist_display.yview)
        self.blacklist_display.config(yscrollcommand=scrollbar.set)
        self.blacklist_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.blacklist_display.bind("<<ListboxSelect>>", self.select)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar.bind("<MouseWheel>", lambda event: self.blacklist_display.yview_scroll(int(-1*(event.delta/120)), "units"))

        self.intro = tk.Toplevel(self.root)
        self.intro.geometry("450x200+775+100")
        self.intro.title("Tutorial")
        self.intro.transient(self.root)
        self.intro.configure(bg=palette["canvas"])
        tk.Label(
            self.intro,
            text="Welcome to Focus Mode!\nThis tutorial will guide you through the main features of the application.\nClick Add to get started",
            font=("Segoe UI", 11),
            bg=palette["canvas"],
            fg=palette["ink"],
            justify=tk.CENTER,
        ).pack(padx=20, pady=18)

        self.update_blacklist_display()

    def tutorial_add(self):
        self.intro.destroy()
        self.add_to_time_list()
        tutorial= tk.Toplevel(self.root)
        self.tutorial_window = tutorial
        tutorial.geometry("420x260+750+100")
        tutorial.title("Tutorial")
        tutorial.transient(self.root)
        tutorial.configure(bg="#F1F5F1")

        header = tk.Frame(tutorial, bg="#183B36", padx=16, pady=12)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Focus Mode Guide",
            font=("Segoe UI", 16, "bold"),
            fg="#FFFFFF",
            bg="#183B36",
        ).pack(anchor=tk.W)
        tk.Frame(header, bg="#E3A63A", height=3).pack(fill=tk.X, pady=(8, 0))

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
        self.label = ttk.Label(tutorial, text=dialogs[self.index], wraplength=360, font=("Segoe UI", 11), justify=tk.LEFT)
        self.label.pack(fill=tk.BOTH, expand=True, padx=18, pady=(12, 8))
        self.video_link = tk.Label(
            tutorial,
            text="Watch video tutorial",
            fg="#187B70",
            bg="#F1F5F1",
            font=("Segoe UI", 10, "underline"),
            cursor="hand2",
            pady=4,
        )
        self.video_link.bind("<Button-1>", lambda event: webbrowser.open("https://example.com/focus-mode-video"))
        self.video_link.pack(anchor=tk.W, padx=18)
        self.video_link.pack_forget()
        button_frame = ttk.Frame(tutorial)
        button_frame.pack(pady=(0, 12))
        self.back_button = ttk.Button(button_frame, text="Back", command=lambda: self.next_dialog(-1))
        self.back_button.pack(side=tk.LEFT, padx=5)
        self.next_button = ttk.Button(button_frame, text="Next", command=lambda: self.next_dialog(1))
        self.next_button.pack(side=tk.LEFT, padx=5)

        def close_tutorial():
            tutorial.destroy()

        ttk.Button(button_frame, text="Close", command=close_tutorial).pack(side=tk.LEFT, padx=5)
        self.back_button.config(state=tk.DISABLED)

    def next_dialog(self, direction=1):
        is_last = self.index == len(self.tutorial_dialogs) - 1
        if direction > 0 and is_last:
            self.tutorial_window.destroy()
            return
        self.index = max(0, min(self.index + direction, len(self.tutorial_dialogs) - 1))
        self.label.config(text=self.tutorial_dialogs[self.index])
        self.video_link.pack_forget() if self.index != len(self.tutorial_dialogs) - 1 else self.video_link.pack(anchor=tk.W, padx=18)
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
            executable = _strip_non_ascii(file_path.split("\\")[-1])
            if not executable or executable.lower() == ".exe":
                messagebox.showwarning(
                    "Invalid program",
                    "The program name must contain at least one ASCII character.",
                )
                return
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
        cleaned = time_str.strip()
        if " [" in cleaned:
            return cleaned.split(" [", 1)[0].strip()
        if " (" in cleaned and " - " in cleaned:
            return cleaned.split(" (", 1)[0].strip()
        if " - " in cleaned:
            return cleaned.split(" - ", 1)[0].strip()
        return cleaned
    
    def remove_from_timelist(self):
        if self.current_view == "time_settings":
            selection = self.select_time(None)
            if selection and selection in vars.time_group:
                del vars.time_group[selection]
                if vars.time_var not in vars.time_group:
                    if vars.time_group:
                        vars.time_var = next(iter(vars.time_group))
                self.update_time_list()
                self.update_time_display()
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

    def update_custom_start_controls(self, *_):
        if self.start_var.get() == "Custom":
            if not self.custom_start_frame.winfo_manager():
                self.custom_start_frame.pack(fill=tk.X, pady=(6, 0))
        else:
            self.custom_start_frame.pack_forget()

        is_application = self.start_type_var.get() == "application"
        self.start_target_label_var.set("Application" if is_application else "Website URL")
        self.start_browse_button.configure(state=tk.NORMAL if is_application else tk.DISABLED)

    def update_custom_finish_controls(self, *_):
        if self.finish_var.get() == "Custom":
            if not self.custom_finish_frame.winfo_manager():
                self.custom_finish_frame.pack(fill=tk.X, pady=(6, 0))
        else:
            self.custom_finish_frame.pack_forget()

        is_application = self.finish_type_var.get() == "application"
        self.finish_target_label_var.set("Application" if is_application else "Website URL")
        self.finish_browse_button.configure(state=tk.NORMAL if is_application else tk.DISABLED)

    def browse_start_application(self):
        file_path = filedialog.askopenfilename(
            initialdir=vars.root_dir,
            title="Select an application",
            filetypes=[("Applications", "*.exe"), ("All files", "*.*")],
        )
        if file_path:
            self.start_type_var.set("application")
            self.start_target_var.set(file_path)
            self.update_custom_start_controls()

    def browse_finish_application(self):
        file_path = filedialog.askopenfilename(
            initialdir=vars.root_dir,
            title="Select an application",
            filetypes=[("Applications", "*.exe"), ("All files", "*.*")],
        )
        if file_path:
            self.finish_type_var.set("application")
            self.finish_target_var.set(file_path)
            self.update_custom_finish_controls()
   
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
                
                start_time = f"{hour:02d}:{minute:02d}"
                
                group_name = name_var.get().strip() or vars.get_next_group_name(vars.time_group)
                if group_name in vars.time_group:
                    messagebox.showwarning("Duplicate", f"Group name {group_name} already exists")
                    return
                
                # Add new time group with default values
                vars.time_group[group_name] = {
                    "name": group_name,
                    "start_time": start_time,
                    "warning_times": vars.default_warning_times.copy(),
                    "programs": [],
                    "end_time": "23:59",
                    "days": vars.selected_days.copy(),
                    "productive":[],
                    "select_type":"Queue",
                    'allowed_hours': 0.0,
                    'time_left': 0.0,
                    'on_start': 0,
                    'on_finish': 0,  #either 0: nothing, 1: shutdown, 2: sleep 
                    'enabled': True
                }
                
                self.update_time_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Created new time group: {group_name}")
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
        scrollbar.bind("<MouseWheel>", lambda event: self.blacklist_display.yview_scroll(int(-1*(event.delta/120)), "units"))
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
        dialog.geometry("460x360+700+350")
        dialog.transient(self.root)
        dialog.minsize(380, 260)

        owns_expansion = vars.configs.get("owned", [])
        if not owns_expansion:
            messagebox.askyesno("Addon Has Not Been Purchased ", "Audio Settings are part of the Voice Packs addon. Please purchase the addon to access this feature.")
            dialog.destroy()
            return

        main = ttk.Frame(dialog, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Voice Pack Settings", font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 8))

        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        button_canvas = tk.Canvas(canvas_frame, height=220, highlightthickness=0)
        button_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=button_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        button_canvas.configure(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(button_canvas)
        button_canvas.create_window((0, 0), window=button_frame, anchor="nw")
        button_frame.bind(
            "<Configure>",
            lambda event: button_canvas.configure(scrollregion=button_canvas.bbox("all")),
        )
        button_canvas.bind(
            "<Configure>",
            lambda event: button_canvas.itemconfigure("all", width=event.width),
        )
        button_canvas.bind(
            "<MouseWheel>",
            lambda event: button_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )

        active_bool = tk.BooleanVar(value=vars.configs.get("enabled", False))
        ttk.Checkbutton(
            button_frame,
            text="Enable 'The Voices'",
            variable=active_bool,
            command=lambda: self.update_audio_settings(active_bool.get(), "enable audio"),
        ).pack(anchor=tk.W, pady=(0, 8))

        voices_by_folder = {}
        for voice in vars.configs.get("owned", []):
            folder = os.path.dirname(os.path.abspath(voice))
            voices_by_folder.setdefault(folder, []).append(voice)

        active_voices = set(vars.configs.get("active", []))
        for folder, voices in sorted(voices_by_folder.items()):
            folder_frame = ttk.Frame(button_frame)
            folder_frame.pack(fill=tk.X, anchor=tk.W, pady=(0, 4))

            folder_var = tk.BooleanVar(value=any(voice in active_voices for voice in voices))
            voice_vars = {}
            child_frame = ttk.Frame(button_frame)
            child_frame.pack(fill=tk.X, anchor=tk.W, padx=(22, 0))

            ttk.Checkbutton(
                folder_frame,
                text=os.path.basename(folder) or folder,
                variable=folder_var,
                command=lambda voices=voices, folder_var=folder_var, child_frame=child_frame, voice_vars=voice_vars: self.update_audio_folder(
                    voices, folder_var.get(), voice_vars, child_frame
                ),
            ).pack(side=tk.LEFT, anchor=tk.W)

            for voice in voices:
                voice_var = tk.BooleanVar(value=voice in active_voices)
                voice_vars[voice] = voice_var

                voice_row = ttk.Frame(child_frame)
                voice_row.pack(fill=tk.X, pady=2)
                ttk.Checkbutton(
                    voice_row,
                    text=os.path.basename(voice),
                    variable=voice_var,
                    command=lambda voice=voice, voice_var=voice_var: self.update_audio_file(
                        voice, voice_var.get()
                    ),
                ).pack(side=tk.LEFT, anchor=tk.W, expand=True)
                ttk.Button(
                    voice_row,
                    text="Play",
                    command=lambda voice=voice: helper_funcs.play_voice(voice),
                    width=8,
                ).pack(side=tk.RIGHT)

            if not folder_var.get():
                child_frame.pack_forget()

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=(10, 12))

    def update_audio_folder(self, voices, enabled, voice_vars, child_frame):
        active_voices = vars.configs.setdefault("active", [])
        for voice in voices:
            if enabled and voice not in active_voices:
                active_voices.append(voice)
            elif not enabled and voice in active_voices:
                active_voices.remove(voice)
            # voice_vars[voice].set(enabled)
        if enabled:
            child_frame.pack(fill=tk.X, anchor=tk.W, padx=(22, 0))
        else:
            child_frame.pack_forget()
        self._save_audio_settings()

    def update_audio_file(self, voice, enabled):
        active_voices = vars.configs.setdefault("active", [])
        if enabled and voice not in active_voices:
            active_voices.append(voice)
        elif not enabled and voice in active_voices:
            active_voices.remove(voice)
        self._save_audio_settings()

    def update_audio_settings(self, bool_var:bool,name:str):
        if name== "enable audio":
            vars.configs["enabled"]= bool_var
            
        else:
            active_voices = vars.configs.setdefault('active', [])
            if bool_var and name not in active_voices:
                active_voices.append(name)
            elif not bool_var and name in active_voices:
                active_voices.remove(name)
        self._save_audio_settings()

    def _save_audio_settings(self):
        with open(vars.config_path, 'w') as f:
            json.dump(vars.configs, f, indent=2)
        
        
    def find_steam_games_helper(self):  
        steam_games= helper_funcs.find_steam_games()
        if not steam_games:
            messagebox.showinfo("No Games Found", "No Steam games were found on this computer.")
            return
         
        if steam_games:
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Steam Games")
            dialog.geometry("400x300+700+400")
            dialog.transient(self.root)
            
            listbox = tk.Listbox(dialog, selectmode=tk.MULTIPLE)
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=listbox.yview)
            scrollbar.bind("<MouseWheel>", lambda event: self.blacklist_display.yview_scroll(int(-1*(event.delta/120)), "units"))
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for game in steam_games:
                listbox.insert(tk.END, game)
            
            def add_selected_games():
                selected_indices = listbox.curselection()
                for index in selected_indices:
                    game = _strip_non_ascii(steam_games[index])
                    if not game:
                        messagebox.showwarning(
                            "Invalid program",
                            "A selected program name contained no ASCII characters and was skipped.",
                        )
                        continue
                    if game not in vars.time_group[vars.time_var]['programs']:
                        vars.time_group[vars.time_var]['programs'].append(game)
                
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
            scrollbar.bind("<MouseWheel>", lambda event: self.blacklist_display.yview_scroll(int(-1*(event.delta/120)), "units"))
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            for game in epic_games:
                listbox.insert(tk.END, game)
            
            def add_selected_games():
                selected_indices = listbox.curselection()
                for index in selected_indices:
                    game = _strip_non_ascii(epic_games[index])
                    if not game:
                        messagebox.showwarning(
                            "Invalid program",
                            "A selected program name contained no ASCII characters and was skipped.",
                        )
                        continue
                    if game not in vars.time_group[vars.time_var]['programs']:
                        vars.time_group[vars.time_var]['programs'].append(game)
                
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
        if vars.time_var and vars.time_var in vars.time_group:
            time_data = vars.time_group[vars.time_var]
             
            # Update name
            name = time_data.get('name', vars.time_var)
            self.name_var.set(name)
            self.enabled_var.set(time_data.get('enabled', True))

            start_action = time_data.get('on_start', 0)
            if isinstance(start_action, dict) and start_action.get('type') == 'custom':
                self.start_var.set('Custom')
                start_type = start_action.get('target_type', 'website')
                self.start_type_var.set(
                    start_type if start_type in ('website', 'application') else 'website'
                )
                self.start_target_var.set(start_action.get('target', ''))
            else:
                self.start_var.set('Nothing')
                self.start_type_var.set('website')
                self.start_target_var.set('')
            self.update_custom_start_controls()

            finish_action = time_data.get('on_finish', 0)
            if isinstance(finish_action, dict) and finish_action.get('type') == 'custom':
                self.finish_var.set('Custom')
                finish_type = finish_action.get('target_type', 'website')
                self.finish_type_var.set(
                    finish_type if finish_type in ('website', 'application') else 'website'
                )
                self.finish_target_var.set(finish_action.get('target', ''))
            elif isinstance(finish_action, int) and 0 <= finish_action < 3:
                self.finish_var.set(self.finish_options[finish_action])
                self.finish_type_var.set('website')
                self.finish_target_var.set('')
            else:
                self.finish_var.set('Nothing')
                self.finish_type_var.set('website')
                self.finish_target_var.set('')
            self.update_custom_finish_controls()
             
            end_time = time_data.get('end_time', '00:00')
            allowed_time = time_data.get('allowed_time', 0)/360
             
            start_time = time_data.get('start_time', '00:00')
            self.hour_var.set(start_time[:2])
            self.minute_var.set(start_time[3:])
            self.end_hour_var.set(end_time[:2])
            self.end_minute_var.set(end_time[3:])
            self.allowed_hours.set(allowed_time)
            for day in vars.selected_days:
                self.day_vars[day].set(day in time_data.get('days', []))
            warning_times = time_data.get('warning_times', vars.default_warning_times)
            for minutes, var in self.warning_vars.items():
                var.set(minutes * 60 in warning_times)
            
            # Update program list
            self.program_listbox.delete(0, tk.END)
            for program in time_data.get('programs', []):
                self.program_listbox.insert(tk.END, program)
    
    def add_program(self):
        program = _strip_non_ascii(self.program_entry.get().strip())
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
            if vars.time_var and vars.time_var in vars.time_group:
                current_group = vars.time_var
                current_time = vars.time_group[current_group].get('start_time', '00:00')
                try:
                    start_hour = int(self.hour_var.get())
                    start_minute = int(self.minute_var.get())
                    if not 0 <= start_hour <= 23 or not 0 <= start_minute <= 59:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Invalid Start Time", "Hour must be 0-23 and minute must be 0-59")
                    return

                new_time = f"{start_hour:02d}:{start_minute:02d}"
                if new_time != current_time and any(
                    group_data.get('start_time') == new_time
                    for group_name, group_data in vars.time_group.items()
                    if group_name != current_group
                ):
                    messagebox.showerror("Duplicate Start Time", f"A time group already starts at {new_time}")
                    return

                new_name = self.name_var.get().strip() or vars.get_next_group_name(vars.time_group)
                if new_name != current_group and new_name in vars.time_group:
                    messagebox.showerror("Duplicate Group Name", f"A group named {new_name} already exists")
                    return

                if self.start_var.get() == 'Custom':
                    start_target = self.start_target_var.get().strip()
                    start_type = self.start_type_var.get()
                    if not start_target:
                        messagebox.showerror("Missing Target", "Enter a website URL or select an application.")
                        return
                    if start_type == 'website':
                        parsed_url = urlparse(start_target)
                        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
                            messagebox.showerror(
                                "Invalid Website",
                                "Enter a complete website URL beginning with http:// or https://.",
                            )
                            return
                    elif not os.path.isfile(start_target) and shutil.which(start_target) is None:
                        messagebox.showerror(
                            "Invalid Application",
                            "Select an existing application file or enter an application available on PATH.",
                        )
                        return
                    start_action = {
                        'type': 'custom',
                        'target_type': start_type,
                        'target': start_target,
                    }
                else:
                    start_action = 0

                if self.finish_var.get() == 'Custom':
                    finish_target = self.finish_target_var.get().strip()
                    finish_type = self.finish_type_var.get()
                    if not finish_target:
                        messagebox.showerror("Missing Target", "Enter a website URL or select an application.")
                        return
                    if finish_type == 'website':
                        parsed_url = urlparse(finish_target)
                        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc:
                            messagebox.showerror(
                                "Invalid Website",
                                "Enter a complete website URL beginning with http:// or https://.",
                            )
                            return
                    elif not os.path.isfile(finish_target) and shutil.which(finish_target) is None:
                        messagebox.showerror(
                            "Invalid Application",
                            "Select an existing application file or enter an application available on PATH.",
                        )
                        return
                    finish_action = {
                        'type': 'custom',
                        'target_type': finish_type,
                        'target': finish_target,
                    }
                else:
                    finish_action = self.finish_options.index(self.finish_var.get())

                if current_group != new_name:
                    time_data = vars.time_group.pop(current_group)
                    time_data['name'] = new_name
                    vars.time_group[new_name] = time_data
                    vars.time_var = new_name
                else:
                    time_data = vars.time_group[current_group]

                time_data['name'] = new_name
                time_data['start_time'] = new_time
                
                # Validate and save time
                end_time = f"{self.end_hour_var.get().zfill(2)}:{self.end_minute_var.get().zfill(2)}"
                
                time_data['end_time'] = end_time
                
                # Save enabled state
                time_data['enabled'] = self.enabled_var.get()

                # Save actions for when the group starts and finishes
                time_data['on_start'] = start_action
                time_data['on_finish'] = finish_action
                
                # Save days
                enabled_days = [day for day, var in self.day_vars.items() if var.get()==1]
                time_data["days"] = enabled_days

                time_data["warning_times"] = [
                    minutes * 60
                    for minutes, var in self.warning_vars.items()
                    if var.get()
                ]

                # Save allowed time
                allowed_time = self.allowed_hours.get()
                time_data['allowed_time'] = float(allowed_time)*360

                # Save to JSON
                with open(vars.json_path, "w", encoding="utf-8") as f:
                    json.dump(vars.session_temp, f, indent=2)

                self.update_time_list()
                selected_index = list(vars.time_group).index(vars.time_var)
                self.time_listbox.selection_clear(0, tk.END)
                self.time_listbox.selection_set(selected_index)
                self.update_time_display()
                
                messagebox.showinfo("Saved", "Time settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving: {str(e)}")
    
    def update_blacklist_display(self):
        if self.blacklist_display:
            self.blacklist_display.delete(0, tk.END)
            if vars.session_temp.get('time_list'):
                for group_name, time_data in vars.time_group.items():
                    name = time_data.get('name', group_name)
                    start_time = time_data.get('start_time', '00:00')
                    end_time = time_data.get('end_time', '23:59')
                    programs = time_data.get('programs', [])

                    status = " [DISABLED]" if not time_data.get('enabled', True) else ""
                    self.blacklist_display.insert(tk.END, f"{name} [{start_time} - {end_time}]{status}")
                    
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
            for group_name, time_data in vars.time_group.items():
                start_time = time_data.get('start_time', '00:00')
                end = time_data.get('end_time', '23:59')
                status = " [DISABLED]" if not time_data.get('enabled', True) else ""
                display_name = time_data.get('name', group_name)
                self.time_listbox.insert(tk.END, f"{display_name} [{start_time} - {end}]{status}")
    
   
    
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
    helper_funcs.check_audio_files()
    main()
