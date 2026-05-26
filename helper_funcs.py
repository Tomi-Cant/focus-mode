import tkinter as tk
import vars

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


def cull_times(set, end, indx, time):
    """Remove time entries that have passed their end time"""
    if time >= end[indx]:
        del end[indx]
        del set[indx]


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
