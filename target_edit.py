import pygame
import sys, os, random
import json

import new_window as nw
import sprite_gen as sg
from os.path import dirname,abspath,join
from tkinter import filedialog
error_text=""
parent_path = dirname(abspath(__file__))
path=join(parent_path,"blacklist.json")


with open(path, "r",encoding="utf-8") as f:
    session_temp=json.load(f)
no_list=session_temp['added_list']
allowed_chars=session_temp['allowed_chars']
json_blacklist=session_temp['blacklist']
sent_list=json_blacklist+no_list
sent_list.sort()
while len(sent_list)<20:
    test=random.randint(0,244)
    sent_list.append(str(test))
list_end=15

pygame.init()

screen = pygame.display.set_mode((800, 700))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)
large_font = pygame.font.SysFont("Arial", 50)

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, text:str='',func=None,args=None,text_color=(0,0,0)):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.y=y
        self.rect.center = (x, y)
        self.text=text
        self.color = color
        self.font = pygame.font.SysFont("Arial", 20)
        self.text_sur = self.font.render(shorten(self.text,self.rect.width-10), True,(0,0,0))
        self.text_color=text_color
        self.func =func
        self.args=args

    def update(self,event,pos,refresh=False):
        if not refresh:
            if self.rect.collidepoint(pos):
                self.color = (150,150,255)
                self.image.fill(self.color)
                # checks for a function and executes it with or without its params
                if event.type == pygame.MOUSEBUTTONDOWN: 
                    if self.args != None and self.func != None:
                        self.func(self.args)
                    elif self.func != None:
                        self.func()
                    self.color = (0,0,255)
                    self.image.fill(self.color)
            else:
                self.color = (255,0,0)
                self.image.fill(self.color)
            self.rect = self.image.get_rect(topleft=self.rect.topleft) 
            self.text_sur = self.font.render(shorten(self.text,self.rect.width-10), True, self.text_color)
            self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
        else:
            self.rect = self.image.get_rect(topleft=self.rect.topleft) 
            self.text_sur = self.font.render(shorten(self.text,self.rect.width-10), True, self.text_color)
            self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
class Text_Edit(Button):
    
    def __init__(self, x, y, width, height, color, text,muteable=True,text_color=(0,0,0)):
        super().__init__(x, y, width, height, color, text,func=None,args=None) 
        self.active = False
        self.muteable=muteable
        self.text_color=text_color
        self.back_pressed=False
    def update(self,event,pos):
        
        if self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active
            
            super().update(event,pos) #calls button update method
        if not self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = False
            self.color = (255,255,255)
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
        if text!= "Enter Program Name":
            no_list.append(text)
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
    global sent_list
    file_path = filedialog.askopenfilename(
        initialdir=parent_path[0:3]+"Program Files",
    title="Select a file",
    filetypes=[ ("Executeable files", "*.exe"),("All files", "*.*")]
    )
    print(file_path)
    file_path=file_path.split("/")[-1]
    print(file_path)
    sent_list.append(file_path)
    
def remove_from_blacklist():
    print("remove distraction")
    
def help():
    print("help")
    
error=False

def save():
    global error,error_text
    valid=time_is_valid()
    if valid:
        exit()
    else:
        print("Error")
        error =True
        error_text="Error! Please enter a valid time."

def time_is_valid() ->bool:
    # insures that the input is a number and that is within the range of timedate
    numbers=['1','2','3','4','5','6','7','8','9','0']
   
    if 0>len(hour_box.text)>2 or 0>len(minute_box.text)>2:
        return False
    combined=hour_box.text+minute_box.text
    for i in hour_box and combined:
        if i in numbers:
            continue 
        else: 
            return False
    if int(hour_box.text)>24 and int(minute_box.text)>60:
        return False
    
    return True
    
def exit():
    #no direct links to the program other than through 
    # save to ensure the data doesnt have to be rentered
    session_temp['added_list']=no_list
    session_temp['set_hour']=hour_box.text.lstrip("0") if hour_box.text.lstrip("0") !="0" else "0"
    session_temp['set_minute']=minute_box.text.lstrip("0")if minute_box.text.lstrip("0") !="0" else "0"
    with open(path, "w",encoding="utf-8") as f:
        json.dump(session_temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()
    
def enter():
   if distraction_input.enter(distraction_input.text):
       sent_list.append(distraction_input.text)
    
blacklist=pygame.sprite.Group()
# generates the right hand list that displays the banned list of programs.
gui_blacklist=sg.generate_line(blacklist,Text_Edit,list_end,550,25,350,45,None,46,True,text=sent_list[list_end-15:list_end],color=(255,255,255),muteable=False)
buttons = pygame.sprite.Group()
buttons.add(Button(100, 50, 175, 50, (255,0,0), "Add To List",add_to_blacklist))
buttons.add(Button(100, 150, 175, 50, (255,0,0), "Remove From List",remove_from_blacklist))
buttons.add(Button(100, 250, 175, 50, (255,0,0), "Help",help))
buttons.add(Button(100, 350, 175, 50, (255,0,0), "Save & Exit",save))
buttons.add(Button(100, 450, 175, 50, (255,0,0), "Enter",enter))

distraction_input=Text_Edit(133,550,251,50,(255,255,255),"Enter Program Name")
hour_box=Text_Edit(45,650,75,50,(255,255,255),session_temp['set_hour'])
minute_box=Text_Edit(150,650,75,50,(255,255,255),session_temp['set_minute'])
text_boxes= pygame.sprite.Group()
text_boxes.add(distraction_input,hour_box,minute_box)

error_message=nw.Popup_Window(250,400,400,150,(0,0,0),"Error!") 
frames=0

def draw():
    global frames,error
    screen.fill((75,75,75))
    buttons.draw(screen)        
    text_boxes.draw(screen)
    gui_blacklist.draw(screen)
    time_sep=large_font.render(":",True,(0,0,0))
    screen.blit(time_sep,(87,615))
    # makes an error popup with a dynamic message that lasts for 3 seconds
    if error and frames<210:
        screen.blit(error_message.image,error_message.rect)
        error_message.update([error_text])
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
        buttons.update(event=event,pos=pos)
        text_boxes.update(pos=pos,event=event)
        gui_blacklist.update(pos=pos,event=event)
        if event.type == pygame.QUIT:
            save()
        if event.type == pygame.MOUSEWHEEL:
            print(event.y)
            if event.y==1 and list_end>15: #going up the list/ up the screen
                list_end-=1
            elif event.y==-1 and list_end<len(sent_list): #going down the list/ down the screen
                list_end+=1
                
            gui_blacklist=sg.generate_line(blacklist,Text_Edit,15,550,25,350,45,None,46,True,text=sent_list[list_end-15:list_end],color=(255,255,255),muteable=False)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save()
    draw()
    

