# you were about to...do help and remove <= forgot to do this / potentially added an inverted tag to invert the timeframe
# ive decided im doing JS :D ( i dont wanna do JS but it would be nice). [this is for the help tab and documentation if needed].
# also days of the week window (30%).
import pygame
import sys
import json

from tkinter import filedialog
import vars

'''
This will prompt a file explorer instance to open and ask for a an executeable (a .exe file).
This is only recomended if you know exactly where the file is located and the file has an odd name.
There is a way to find the program excutable within task manager... {do tutorial or w.e}
/ 
For each seletec program .exe or title it will be removed from the blacklist of programs once saved. (Multiple can be selected at one time).
/
ban lists have a start time and end time, the start time is part of the openning list and all programs in that time frame. 15 unique time groups can be made.
/
This text box uses the exact title of the program this can be much faster than sifting through files. If this doesn't seem to work double check the title name.
'''

pygame.init()

screen = pygame.display.set_mode((800, 700))
vars.screen=screen

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)
vars.font=font

large_font = pygame.font.SysFont("Arial", 50)
vars.large_font=large_font

from Text_Edit import Text_Edit
from Button import Button
import new_window as nw
import sprite_gen as sg
import webbrowser

# takes user into file explorer and parses the executable from the output
def add_to_blacklist() -> None:
    file_path = filedialog.askopenfilename(
        initialdir=vars.parent_path[:3],
        title="Select a file",
        filetypes=[("Executeable files", "*.exe"), ("All files", "*.*")]
    )

    executeable = file_path.split("/")[-1]

    if executeable in vars.session_temp['time_list'][vars.time_var]['programs']:
        error_window.title = "Error! Please select a file that is already in the list."
        error_window.active = True

    for i in range(len(vars.sent_list), 0, -1):
        if vars.sent_list[i] != '' or i == 0:
            vars.sent_list.insert(i+1, file_path)


def exit_window() -> None:
    for i in windows.sprites():
        if i.active:
            i.active = False


def remove_from_blacklist() -> None:
    selected = 0
    global title_text
    for i in vars.gui_blacklist.sprites():
        if i.active and not i.muteable:
            if i.text != '  ':
                selected += 1
                vars.sent_list.remove(i.text)
                vars.sent_list.append('  ')
                vars.session_temp['time_list'][vars.time_var]['programs'].remove(
                    i.text)
    if selected == 0:
        title_text = "Error! Please select a program to remove."
        error_window.active = True


def help() -> None:
    webbrowser.open('https://github.com')


def save() -> None:

    valid = time_is_valid()
    if valid:
        exit()
    else:
        error_window.active = True
        error_window.title = "Error! Please enter a valid time."


def time_is_valid() -> tuple[bool, str]:
    # insures that the input is a number and that is within the range of timedate
    numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
    i, l = len(hour_box.text), len(minute_box.text)
    if 0 == i or 0 == l:
        return False, ''
    combined = f'{hour_box.text}{minute_box.text}'
    for i in combined:
        if i in numbers:
            continue
        else:
            return False, ''
    if int(hour_box.text) > 24 and int(minute_box.text) > 60:
        return False, ''

    return True, hour_box.text+':'+minute_box.text


def select() -> None:
    for i in vars.gui_timelist.sprites():
        if i.active:
            vars.time_selected = True
            vars.time_var = i.text.strip()

            fill_list()
            vars.gui_blacklist = sg.generate_line(vars.gui_blacklist, Text_Edit, vars.list_end, 550, 25, 350, 45, None, 46,
                                             True, text=vars.sent_list[vars.list_end-15:vars.list_end], color=(255, 255, 255), muteable=False, font=font)
            break
    if not vars.time_selected:
        error_window.active = True
        error_window.title = "Error! Please select a valid box."


def fill_list() -> None:
    json_blacklist = vars.session_temp['time_list'][vars.time_var]['programs']
    vars.sent_list = sorted(json_blacklist)
    if len(vars.sent_list) > 20:
        vars.sent_list.append(' '*5)
    while len(vars.sent_list) < 20:
        vars.sent_list.append(' ')


def back() -> None:

    vars.time_selected = False
    vars.session_temp['time_list'][vars.time_var]['end_time'] = time_is_valid()[
        1]


def exit() -> None:
    # no direct links to the program other than through
    # save to ensure the data doesnt have to be rentered

    with open(vars.path, "w", encoding="utf-8") as f:
        json.dump(vars.session_temp, f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()


def delete_enteries(gui_list: list) -> None:
    for i in range(len(gui_list)):
        if gui_list[i].active:
            gui_list[i].text
            del vars.session_temp['time_list'][vars.time_var]['programs'][i]


def enter(days) -> None:

    if vars.time_selected:

        change_end_time()

    else:
        set_new_start_time(days)


def set_new_start_time(days) -> None:
    # is not already a set valid time
    if time_is_valid()[0] and time_is_valid()[1] not in vars.time_group:
        vars.time_group[time_is_valid()[1]] = {
            "programs": [],
            "end_time": "23:59",
            "days": days
        }
    vars.gui_timelist = sg.generate_line(vars.gui_timelist, Text_Edit, len(vars.time_group), 550, 25, 350, 45, None, 46, True, text=list(
        vars.time_group.keys()), color=(255, 255, 255), muteable=False, font=font)


def change_end_time() -> None:
    if time_is_valid()[0]:
        # and not less than key time
        if int(time_is_valid()[1][:2]) < int(hour_box.text) and int(time_is_valid()[1][3:]) < int(minute_box.text):
            vars.session_temp['time_list'][vars.time_var]['end_time'] = time_is_valid()[
                1]
            vars.time_group[time_is_valid()[1]] = {}

            vars.gui_timelist = sg.generate_line(vars.gui_timelist, Text_Edit, len(vars.time_group), 550, 25, 350, 45, None, 46, True, text=list(
                vars.time_group.keys()), color=(255, 255, 255), muteable=False, font=font)


def append_program()-> None:
    if distraction_input.enter(distraction_input.text, vars.session_temp['time_list'][vars.time_var]['programs']):
        vars.session_temp['time_list'][vars.time_var]['programs'].append(
            distraction_input.text)
        distraction_input.text = ''
        vars.gui_blacklist = sg.generate_line(vars.gui_blacklist, Text_Edit, 15, 550, 25, 350, 45, None, 46, True,
                                         text=vars.sent_list[vars.list_end-15:vars.list_end], color=(255, 255, 255), muteable=False, font=font)


vars.gui_timelist.add(sg.generate_line(vars.gui_timelist, Text_Edit, len(vars.time_group), 550, 25, 350, 45,
                 None, 46, True, text=list(vars.time_group.keys()), color=(255, 255, 255), muteable=False, font=font))
# generates the right hand list that displays the banned list of programs.

time_buttons = pygame.sprite.Group()
blacklist_buttons = pygame.sprite.Group()
days_list = pygame.sprite.Group()

add_button = Button(100, 50, 175, 50, (255, 0, 0), font,
                    "Add To List", add_to_blacklist)
remove_button = Button(100, 150, 175, 50, (255, 0, 0),
                       font, "Remove From List", remove_from_blacklist)
help_button = Button(100, 350, 175, 50, (255, 0, 0), font, "Help", help)
save_button = Button(100, 450, 175, 50, (255, 0, 0), font, "Save & Exit", save)
enter_button = Button(100, 250, 175, 50, (255, 0, 0),
                      font, "Enter", enter, args=vars.selected_days)
back_button = Button(100, 550, 175, 50, (255, 0, 0), font, "Back", back)
select_button = Button(100, 550, 175, 50, (255, 0, 0), font, "Select", select)
days_button = Button(100, 625, 175, 50, (255, 0, 0),
                     font, "Choose Days")  # returns true
blacklist_buttons.add(back_button, add_button,
                      remove_button, help_button, save_button)
time_buttons.add(select_button, save_button, help_button)

distraction_input = Text_Edit(
    133, 595, 251, 50, (255, 255, 255), font=font, text="Enter Program Name")
hour_box = Text_Edit(45, 650, 75, 50, (255, 255, 255), font=font, text="00")
minute_box = Text_Edit(150, 650, 75, 50, (255, 255, 255), font=font, text="00")
text_boxes = pygame.sprite.Group()
text_boxes.add(hour_box, minute_box)
windows = pygame.sprite.Group()
error_window = nw.Popup_Window(250, 400, 400, 150, (0, 0, 0),
                               "An error has occured!", window_type="error")
day_select_window = nw.Popup_Window(
    75, 150, 400, 450, (200, 30, 30), "Select Days of the week", 'days')
windows.add(day_select_window, error_window)

days_list = sg.generate_line(days_list, Text_Edit, 7, 190, 70, 150, 50, 0, 51, True,
                             text=vars.selected_days, muteable=False, color=(0, 255, 255), font=font, active=True,win='days')


def draw():
    screen.fill((75, 75, 75))
    # resposible for separating the time and the blacklist to avoid overlap/ clutter
    if vars.time_selected == True:
        distraction_input.draw(screen)
        blacklist_buttons.draw(screen)
        vars.gui_blacklist.draw(screen)
        back_button.draw(screen)
        days_button.draw(screen)
    else:
        time_buttons.draw(screen)
        vars.gui_timelist.draw(screen)
        time_sep = large_font.render(":", True, (0, 0, 0))
        screen.blit(time_sep, (87, 615))
    enter_button.draw(screen)
    text_boxes.draw(screen)
    if day_select_window.active:
        day_select_window.draw(screen, sprites=days_list.sprites())
        day_select_window.exit_btn.draw(day_select_window.image)
        vars.active_window = 'days'
    elif error_window.active:
        error_window.draw(screen)
        vars.active_window = 'error'
    else:
        vars.active_window = 'main'

def main():
    while True:
        draw()
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if vars.time_selected:
                blacklist_buttons.update(event, pos, vars.active_window)
                distraction_input.update(event, pos, vars.active_window)
                vars.gui_blacklist.update(event, pos, vars.active_window)
                day_select_window.active = days_button.update(
                    event, pos, vars.active_window, open=day_select_window.active)
            else:
                time_buttons.update(event, pos, vars.active_window)
                vars.gui_timelist.update(event, pos, vars.active_window)
            text_boxes.update(event, pos, vars.active_window)
            enter_button.update(event, pos, vars.active_window)

            windows.update(event, pos, sprites=days_list.sprites())
            if event.type == pygame.QUIT:
                save()
            if event.type == pygame.MOUSEWHEEL and vars.time_selected:
                if event.y > 0 and vars.list_end > 15:  # going up the list/ up the screen
                    vars.list_end -= event.y  # scales with scroll speed
                    vars.list_end = max(vars.list_end, 15)
                # going down the list/ down the screen
                elif event.y < 0 and vars.list_end < len(vars.sent_list):
                    vars.list_end -= event.y  # scales with scroll speed
                    vars.list_end = min(len(vars.sent_list), vars.list_end)
                vars.gui_blacklist.update(event, pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    save()
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
