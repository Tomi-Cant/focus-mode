import tkinter as tk


class Button(tk.Button):
    """Custom Button class wrapping tkinter.Button for Focus Mode"""
    def __init__(self, parent, x=0, y=0, width=20, height=2, text="", command=None, 
                 bg_color="red", fg_color="black", font=None, args=None, win="main", **kwargs):
    
        if font is None:
            font = ("Arial", 10)
        
        # Handle font tuple
        if isinstance(font, tuple):
            font_config = (font[0], int(font[1]))
        else:
            font_config = ("Arial", 10)
        
        self.args = args
        self.win = win
        
        # Wrap command to handle args
        if command and args is not None:
            actual_command = lambda: command(args)
        else:
            actual_command = command
        
        super().__init__(
            parent,
            text=text,
            command=actual_command, #type: ignore
            width=width,
            height=height,
            bg=bg_color,
            fg=fg_color,
            font=font_config,
            relief=tk.RAISED,
            **kwargs
        )
        self.x = x
        self.y = y
        
        # Display the button using grid with the x, y coordinates
        self.grid(row=x, column=y, padx=5, pady=5, sticky="ew")

