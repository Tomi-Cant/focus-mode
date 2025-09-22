# you were about to...do help and remove
import pygame
import sys, os
import json
import main
from buttons import Button as Button
import new_window as nw
import sprite_gen as sg
from os.path import dirname,abspath,join
from tkinter import filedialog
error_text=""
help_open=False
time_selected=False
parent_path = dirname(abspath(__file__))
path=join(parent_path,"blacklist.json")
with open(path, "r",encoding="utf-8") as f:
    session_temp=json.load(f)
time_group=session_temp['test']
added_list=session_temp['added_list']
removed_list=session_temp['removed_list']
allowed_chars=session_temp['allowed_chars']
json_blacklist=session_temp['blacklist']
added_list=sorted(added_list)
json_blacklist=sorted(json_blacklist)
sent_list=json_blacklist+added_list
if len(sent_list)>20:
    sent_list.append(''*5)
while len(sent_list)<20:
    sent_list.append('')

list_end=15

pygame.init()

screen = pygame.display.set_mode((800, 700))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)
large_font = pygame.font.SysFont("Arial", 50)



class Text_Edit(Button):
    
    def __init__(self, x, y, width, height, color, text,font,muteable=True,text_color=(0,0,0)):
        super().__init__(x, y, width, height, color,font, text,func=None,args=None) 
        self.active = False
        self.muteable=muteable
        self.text_color=text_color
        self.back_pressed=False
    def update(self,event,pos):
        
        if self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active
            
            super().update(event,pos) #calls button update method
        if not self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            if not time_selected and not self.muteable:
                self.active = False
            super().update(event,pos) #calls button update method
        if self.back_pressed:
                    self.text = self.text[:-1] if self.text!="Enter Program Name" else ""   
                    self.active=True
                    self.back_pressed=False
        if self.active:
            if self.text=="Enter Program Name": 
                self.text = ""
            self.color = (150,150,255)
            # checks if meant to be a static textbox
            if self.muteable:  
                if event.type == pygame.KEYDOWN:
                    print(f"{self.text = }")
                    if event.key == pygame.K_BACKSPACE:
                        self.back_pressed=True    
                        self.active=False          
                if event.type == pygame.KEYUP: 
                    if pygame.key.name(event.key) in allowed_chars:
                        self.text += pygame.key.name(event.key)
                    if event.key == pygame.K_RETURN:
                        self.active = False
                
        elif not self.active:
            self.color = (255,255,255)
            self.image.fill(self.color)
        super().update(event,pos,True) #calls button update method
        self.text_sur = self.font.render(shorten(self.text,self.rect.width-10), True, self.text_color)
        self.image.fill(self.color) #thanks copilot
        self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
        
    # meant for specific textboxes
    def enter(self,text)-> bool:
        global error, error_text
        if text!= "Enter Program Name" or text!="":
            added_list.append(text)
            return True
        else:
            error_text="Error! Please enter a program name."
            error=True
            return False

    #condesnses text till it can fit within the given constraints of the surface

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
        return
   
    for i in range(len(sent_list),0,-1):
        if sent_list[i]!='' or i==0:
            sent_list.insert(i+1,file_path)
            added_list.append(file_path)
    
def exit_window():
    global help_open
    help_open=False   

def remove_from_blacklist():
    selected=0
    global error,error_text
    for i in gui_blacklist.sprites():
        if i.active and not i.muteable:
            if i.text!='':
                selected+=1
                sent_list.remove(i.text)
                sent_list.append('')
                removed_list.append(i.text)
    if selected==0:
        error_text="Error! Please select a program to remove."
        error=True
        
    
def help():
    print("help")
    #do it
    
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
    global time_selected,error,error_text
    for i in gui_timelist.sprites():
        if i.active:
            time_selected=True
            break
    if  not time_selected:
        error =True
        error_text="Error! Please select a valid box."   
        
def back():
    global time_selected
    time_selected=False  
 
def exit():
    #no direct links to the program other than through 
    # save to ensure the data doesnt have to be rentered
    session_temp['added_list']=added_list
    session_temp['set_hour']=hour_box.text
    session_temp['set_minute']=minute_box.text
    
    with open(path, "w",encoding="utf-8") as f:
        json.dump(session_temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()

def enter():
    if time_selected:
        if distraction_input.enter(distraction_input.text):
            sent_list.append(distraction_input.text)
    else:
        if time_is_valid()[0] and time_is_valid()[1] not in time_group:
            time_group[f'{hour_box.text}:{minute_box.text}']

gui_timelist=pygame.sprite.Group()
gui_timelist.add(sg.generate_line(gui_timelist,Text_Edit,len(time_group),550,25,350,45,None,46,True,text=list(time_group.keys()),color=(255,255,255),muteable=False,font=font))
# generates the right hand list that displays the banned list of programs.
blacklist=pygame.sprite.Group()
gui_blacklist=sg.generate_line(blacklist,Text_Edit,list_end,550,25,350,45,None,46,True,text=sent_list[list_end-15:list_end],color=(255,255,255),muteable=False,font=font)
time_buttons = pygame.sprite.Group()
blacklist_buttons = pygame.sprite.Group()
add_button=Button(100, 50, 175, 50, (255,0,0),font, "Add To List",add_to_blacklist)
remove_button=Button(100, 150, 175, 50, (255,0,0),font, "Remove From List",remove_from_blacklist)
help_button=Button(100, 350, 175, 50, (255,0,0),font, "Help",help)
save_button=Button(100, 450, 175, 50, (255,0,0),font, "Save & Exit",save)
enter_button=Button(100, 250, 175, 50, (255,0,0),font, "Enter",enter)
back_button=Button(100, 550, 175, 50, (255,0,0),font, "Back",back)  
select_button=Button(100, 550, 175, 50, (255,0,0),font, "Select",select)
blacklist_buttons.add(back_button,enter_button,add_button,remove_button,help_button,save_button)
time_buttons.add(select_button,save_button,help_button)

distraction_input=Text_Edit(133,650,251,50,(255,255,255),font=font,text="Enter Program Name")
hour_box=Text_Edit(45,650,75,50,(255,255,255),font=font,text=session_temp['set_hour'])
minute_box=Text_Edit(150,650,75,50,(255,255,255),font=font,text=session_temp['set_minute'])
text_boxes= pygame.sprite.Group()
text_boxes.add(hour_box,minute_box)

help_window=nw.Popup_Window(250,600,600,150,(0,0,0),"Help")
error_window=nw.Popup_Window(250,400,400,150,(0,0,0),"An error has occured!")
window_exit_btn=Button(100,550,175,50,(255,0,0),font,"Exit",exit_window)
frames=0

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
        text_boxes.draw(screen)  
        screen.blit(time_sep,(87,615))
        
    # makes an error popup with a dynamic message that lasts for 3 seconds
    if error and frames<210:
        screen.blit(error_window.image,error_window.rect)
        error_window.update([error_text])
        frames+=1
    if frames>=210:
        frames=0
        error=False
    pygame.display.update()
    clock.tick(60)
    
while True:
    draw()
    pos=pygame.mouse.get_pos()
    for event in pygame.event.get():
        if time_selected:
            blacklist_buttons.update(event=event,pos=pos)
            distraction_input.update(event=event,pos=pos)
            gui_blacklist.update(pos=pos,event=event)
        else:
            time_buttons.update(event=event,pos=pos)
            text_boxes.update(pos=pos,event=event)
            gui_timelist.update(pos=pos,event=event)
        
        if event.type == pygame.QUIT:
            save()
        if event.type == pygame.MOUSEWHEEL:            
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
    

