import tkinter as tk
from tkinter import ttk
import vars


allowed_chars = vars.session_temp.get('allowed_chars', 
    "abcdefghijklmnopqrstuvwxyz0123456789")


class Text_Edit(tk.Entry):
    """Custom Entry widget for Focus Mode"""
    def __init__(self, parent, x=0, y=0, width=20, text="Enter text", 
                 muteable=True, text_color="black", active=False, win='main', font=None, **kwargs):
        
        if font is None:
            font = ("Arial", 10)
        
        if isinstance(font, tuple):
            font_config = (font[0], int(font[1]))
        else:
            font_config = ("Arial", 10)
        
        super().__init__(
            parent,
            font=font_config,
            width=width,
            **kwargs
        )
        
        self.placeholder = text
        self.default_text = text
        self.active = active
        self.muteable = muteable
        self.text_color = text_color
        self.win = win
        self.x = x
        self.y = y
        
        # Set default text
        self.insert(0, text)
        
        # Bind events
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Return>", self._on_return)
        
        self.grid(row=x, column=y, padx=5, pady=5, sticky="ew")
    
    def _on_focus_in(self, event):
        """Handle focus in event"""
        if self.get() == self.placeholder or self.get() == "00":
            self.delete(0, tk.END)
            self.config(fg="black")
        self.active = True
    
    def _on_focus_out(self, event):
        """Handle focus out event"""
        if self.get() == "":
            self.insert(0, self.placeholder)
            self.config(fg="gray")
        self.active = False
    
    def _on_return(self, event):
        """Handle return key press"""
        self.active = False
    
    @property
    def text(self):
        """Get the text value"""
        content = self.get()
        if content == self.placeholder or content == "00":
            return ""
        return content
    
    @text.setter
    def text(self, value):
        """Set the text value"""
        self.delete(0, tk.END)
        self.insert(0, value)
    
    def enter(self, text, added_list) -> bool:
        """Add text to a list if valid"""
        if text != self.placeholder and text != "":
            added_list.append(text)
            if 'time_list' in vars.session_temp and vars.time_var in vars.session_temp['time_list']:
                vars.session_temp['time_list'][vars.time_var]['programs'].append(text)
            return True
        

        error = True
        return False
