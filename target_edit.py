# you were about to...do help and remove <= forgot to do this / potentially added an inverted tag to invert the timeframe
# ive decided im doing JS :D ( i dont wanna do JS but it would be nice). [this is for the help tab and documentation if needed]. also days of the week.
import pygame
import sys
import json
from Text_Edit import Text_Edit
from Button import Button 
import new_window as nw
import sprite_gen as sg
import webbrowser
from os.path import dirname,abspath,join
from tkinter import filedialog
error_text=""
help_open=False
time_selected=False
time_var=''
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
parent_path = dirname(abspath(__file__))
path=join(parent_path,"blacklist.json")
with open(path, "r",encoding="utf-8") as f:
    session_temp=json.load(f)
time_group=session_temp['time_list']
added_list=session_temp['added_list']


list_end=15

pygame.init()

screen = pygame.display.set_mode((800, 700))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)

large_font = pygame.font.SysFont("Arial", 50)


def shorten(text:str,box_width:int)-> str:
    render=font.render(text,True,(0,0,0))
    if render.get_width()<=box_width:
        return text
    while render.get_width()>box_width:
        text=text[:-1]
        render=font.render(text+'...',True,(0,0,0))
    
    text=text.rstrip()
    text=text+'...'
    return text

# takes user into file explorer and parses the executable from the output
def add_to_blacklist():
    global sent_list, error,error_text
    file_path = filedialog.askopenfilename(
        initialdir=parent_path[:3],
        title="Select a file",
        filetypes=[("Executeable files", "*.exe"),("All files", "*.*")]
    )
    
    file_path=file_path.split("/")[-1]
    
    if file_path in added_list:
        error_text="Error! Please select a file that is not already in the list."
        error=True
   
    for i in range(len(sent_list),0,-1):
        if sent_list[i]!='' or i==0:
            sent_list.insert(i+1,file_path)
            added_list.append(file_path)
    
def exit_window():
    for i in windows.sprites():
        if i.active:
            i.active=False

def remove_from_blacklist():
    selected=0
    global error,error_text
    for i in gui_blacklist.sprites():
        if i.active and not i.muteable:
            if i.text!='':
                selected+=1
                sent_list.remove(i.text)
                sent_list.append('')
                session_temp['time_list'][time_var]['programs'].remove(i.text)
    if selected==0:
        error_text="Error! Please select a program to remove."
        error=True
        
    
def help():
    webbrowser.open('https://github.com')
    
error=False

def save():
    global error,error_text
    valid=time_is_valid()
    if valid:
        exit()
    else:
        error =True
        error_text="Error! Please enter a valid time."

def time_is_valid() ->tuple[bool,str]:
    # insures that the input is a number and that is within the range of timedate
    numbers=['1','2','3','4','5','6','7','8','9','0']
   
    if 0>len(hour_box.text)>2 or 0>len(minute_box.text)>2:
        return False,''
    combined=f'{hour_box.text}:{minute_box.text}'
    for i in combined:
        if i in numbers:
            continue 
        else: 
            return False,''
    if int(hour_box.text)>24 and int(minute_box.text)>60:
        return False,''
    
    return True,combined

def select():
    global time_selected,error,error_text,sent_list,json_blacklist,added_list,time_var,gui_blacklist
    for i in gui_timelist.sprites():
        if i.active:
            time_selected=True
            time_var=i.text.strip()
            json_blacklist=session_temp['time_list'][time_var]['programs']
            added_list=sorted(added_list)
            json_blacklist=sorted(json_blacklist)
            sent_list=json_blacklist+added_list
            if len(sent_list)>20:
                sent_list.append(' '*5)
            while len(sent_list)<20:
                sent_list.append(' ')
            gui_blacklist=sg.generate_line(blacklist,Text_Edit,list_end,550,25,350,45,None,46,True,text=sent_list[list_end-15:list_end],color=(255,255,255),muteable=False,font=font)
            break
    if  not time_selected:
        error =True
        error_text="Error! Please select a valid box."   
        
def back():
    global time_selected
    time_selected=False  
    session_temp['time_list'][time_var]['end_time']=time_is_valid()[1]    
 
def exit():
    #no direct links to the program other than through 
    # save to ensure the data doesnt have to be rentered
    
    with open(path, "w",encoding="utf-8") as f:
        json.dump(session_temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()

def enter(added_list,time_var):
    if time_selected:
        if distraction_input.enter(distraction_input.text,added_list,time_var):
            sent_list.append(distraction_input.text)
        if time_is_valid()[0]: 
            if int(time_is_valid()[1][:2]) < int(hour_box.text) and int(time_is_valid()[1][:2]) < int(minute_box.text): # and not less than key time
                session_temp['time_list'][time_var]['end_time']=time_is_valid()[1]            
    else:
        if time_is_valid()[0] and time_is_valid()[1] not in time_group: # is not already a set valid time
            time_group[f'{hour_box.text}:{minute_box.text}']={
                "programs":[],
                "end_time":"23:59",
                "days": ["Monday","Tuesday","Wednesday", "Thursday", "Friday","Saturday","Sunday"]
                }

    
gui_timelist=pygame.sprite.Group()
gui_timelist.add(sg.generate_line(gui_timelist,Text_Edit,len(time_group),550,25,350,45,None,46,True,text=list(time_group.keys()),color=(255,255,255),muteable=False,font=font))
# generates the right hand list that displays the banned list of programs.
blacklist=pygame.sprite.Group()
time_buttons = pygame.sprite.Group()
blacklist_buttons = pygame.sprite.Group()
days_list= pygame.sprite.Group()

add_button=Button(100, 50, 175, 50, (255,0,0),font, "Add To List",add_to_blacklist)
remove_button=Button(100, 150, 175, 50, (255,0,0),font, "Remove From List",remove_from_blacklist)
help_button=Button(100, 350, 175, 50, (255,0,0),font, "Help",help)
save_button=Button(100, 450, 175, 50, (255,0,0),font, "Save & Exit",save)
enter_button=Button(100, 250, 175, 50, (255,0,0),font, "Enter",enter)
back_button=Button(100, 550, 175, 50, (255,0,0),font, "Back",back)  
select_button=Button(100, 550, 175, 50, (255,0,0),font, "Select",select)
days_button=Button(100,625,175, 50,(255,0,0), font,'Choose Days') # returns true
blacklist_buttons.add(back_button,enter_button,add_button,remove_button,help_button,save_button)
time_buttons.add(select_button,save_button,help_button)

distraction_input=Text_Edit(133,595,251,50,(255,255,255),font=font,text="Enter Program Name")
hour_box=Text_Edit(45,650,75,50,(255,255,255),font=font,text="00")
minute_box=Text_Edit(150,650,75,50,(255,255,255),font=font,text="00")
text_boxes= pygame.sprite.Group()
text_boxes.add(hour_box,minute_box)
windows = pygame.sprite.Group()
help_window=nw.Popup_Window(250,600,600,150,(0,0,0),"How To Use")
error_window=nw.Popup_Window(250,400,400,150,(0,0,0),"An error has occured!")
day_select_window= nw.Popup_Window(150,150,650,400,(200,30,30), "Select Days of the week")
windows.add(help_window,error_window)
window_exit_btn=Button(100,550,175,50,(69,69,69,0),large_font,"X",exit_window) #move to be in the corner of any window ( in the creation do width - w.e)
frames=0
days_list=sg.generate_line(days_list,Text_Edit,7,450,200, 125,50,0,51,True,text=["Monday","Tuesday","Wednesday", "Thursday", "Friday","Saturday","Sunday"],muteable=False,color=(255,255,255),font=font)
def draw():
    global frames,error
    screen.fill((75,75,75))
    
    # resposible for separating the time and the blacklist to avoid overlap/ clutter
    if time_selected==True:
        distraction_input.draw(screen)
        blacklist_buttons.draw(screen)
        gui_blacklist.draw(screen) 
        back_button.draw(screen)
    else:
        time_buttons.draw(screen)
        gui_timelist.draw(screen)
        time_sep=large_font.render(":",True,(0,0,0))
        
        screen.blit(time_sep,(87,615))
    text_boxes.draw(screen)      
    # makes an error popup with a dynamic message that lasts for 3 seconds
    if error and frames<210:
        screen.blit(error_window.image,error_window.rect)
        error_window.update([error_text],window_exit_btn)
        frames+=1
    if frames>=210:
        frames=0
        error=False
    pygame.display.update()
    clock.tick(60)
    
while True:
   
    added_list=sorted(added_list)
    if time_selected:
        sent_list= json_blacklist+added_list
        if len(sent_list)>20:
            sent_list.append(' '*5)
        while len(sent_list)<20:
            sent_list.append(' ')
    draw()
    pos=pygame.mouse.get_pos()
    for event in pygame.event.get():
        if time_selected:
            blacklist_buttons.update(event=event,pos=pos,time_selected=True)
            distraction_input.update(event=event,pos=pos,time_selected=True)
            gui_blacklist.update(pos=pos,event=event,time_selected=True)
        else:
            time_buttons.update(event, pos, time_selected=False)
            gui_timelist.update(pos=pos,event=event,time_selected=False)
        text_boxes.update(pos=pos,event=event,time_selected=False)
        if event.type == pygame.QUIT:
            save()
        if event.type == pygame.MOUSEWHEEL and time_selected:            
            if event.y>0 and list_end>15: #going up the list/ up the screen
                list_end-=event.y # scales with scroll speed
                list_end=max(list_end,15)
            elif event.y<0 and list_end<len(sent_list): #going down the list/ down the screen
                list_end-=event.y # scales with scroll speed
                list_end=min(len(sent_list),list_end)
            gui_blacklist=sg.generate_line(blacklist,Text_Edit,15,550,25,350,45,None,46,True,text=sent_list[list_end-15:list_end],color=(255,255,255),muteable=False,font=font)
            gui_blacklist.update(pos=pos,event=event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save()
    draw()
    

