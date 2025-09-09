import pygame
import sys, os
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
pygame.init()

screen = pygame.display.set_mode((800, 800))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)

class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, text:str,func,args=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.y=y
        self.rect.center = (x, y)
        self.text=text
        self.color = color
        self.font = pygame.font.SysFont("Arial", 20)
        self.text_sur = self.font.render(text, True, (255,255,255))  
        self.func =func
        self.args=args

    def update(self,event,pos):
        if self.rect.collidepoint(pos):
            self.color = (0,0,200)
            self.image.fill(self.color)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.args != None and self.func != None:
                    self.func(self.args)
                elif self.func != None:
                    self.func()
                self.color = (0,0,100)
                self.image.fill(self.color)
        else:
            self.color = (255,0,0)
            self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=self.rect.topleft) 
        self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))


class Text_Edit(Button):
    
    def __init__(self, x, y, width, height, color, text):
        super().__init__(x, y, width, height, color, text,func=None)
        self.active = False
        
    def update(self,event,pos):
        if self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active
            super().update(event,pos)
        if not self.rect.collidepoint(pos):
            self.active = False
            self.color = (255,255,255)
        if self.active:
            self.color = (0,0,255)
            if event.type == pygame.KEYUP:
                if pygame.key.name(event.key) in allowed_chars:
                    self.text += pygame.key.name(event.key)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    self.active = False
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    print(f"{self.text =}")   
        elif not self.active:
            self.color = (255,255,255)
            self.image.fill(self.color)
        self.text_sur = self.font.render(self.text, True, (0,0,0))
        self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
        
    
    def enter(self,text):
        global error, error_text
        if text!= "Enter Program Name":
            no_list.append(text)
        else:
            error_text="Error! Please enter a program name."
            error=True
        
def add_to_blacklist():
    file_path = filedialog.askopenfilename(
    title="Select a file",
    filetypes=[("All files", "*.*"), ("Text files", "*.txt"), ("Executeable files", "*.exe")]
    )
    print(file_path)
def remove_from_blacklist():
    print("remove distraction")
def help():
    print("help")
error=False
def save():
    global error,error_text
    valid=time_is_valid()
    if valid:
        print("save and exit")
        exit()
    else:
        print("Error")
        error =True
        error_text="Error! Please enter a valid time."

    
def time_is_valid() ->bool:
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
    session_temp['added_list']=no_list
    session_temp['set_hour']=hour_box.text.lstrip("0") if hour_box.text.lstrip("0") !="0" else "0"
    session_temp['set_minute']=minute_box.text.lstrip("0")if minute_box.text.lstrip("0") !="0" else "0"
    with open(path, "w",encoding="utf-8") as f:
        json.dump(session_temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()
    
def enter():
    distraction_input.enter(distraction_input.text)
buttons = pygame.sprite.Group()
buttons.add(Button(100, 50, 175, 50, (255,0,0), "Add To List",add_to_blacklist))
buttons.add(Button(100, 150, 175, 50, (255,0,0), "Remove From List",remove_from_blacklist))
buttons.add(Button(100, 250, 175, 50, (255,0,0), "Help",help))
buttons.add(Button(100, 350, 175, 50, (255,0,0), "Save & Exit",save))
buttons.add(Button(100, 450, 175, 50, (255,0,0), "Enter",enter))
distraction_input=Text_Edit(133,550,251,50,(255,255,255),"Enter Program Name")
hour_box=Text_Edit(150,650,75,50,(255,255,255),session_temp['set_hour'])
minute_box=Text_Edit(45,650,75,50,(255,255,255),session_temp['set_minute'])
text_boxes= pygame.sprite.Group()
text_boxes.add(distraction_input,hour_box,minute_box)
error_message=nw.Popup_Window(250,400,400,150,(0,0,0),"Error!") 

frames=0
def draw():
    global frames,error
    screen.fill((75,75,75))
    buttons.draw(screen)        
    text_boxes.draw(screen)
    if error and frames<210:
        screen.blit(error_message.image,error_message.rect)
        error_message.update([error_text])
        frames+=1
    if frames>=210:
        frames=0
        
        error=False
   # sg.generate_line(buttons,button,1,400,50,175,50,0,0,color=(255,0,0),text="Set Hours")
    pygame.display.update()
    clock.tick(60)
    
def main():
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            buttons.update(event=event,pos=pos)
            text_boxes.update(pos=pos,event=event)
            if event.type == pygame.QUIT:
               save()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                   save()
        draw()
        


if __name__ == "__main__":
    main()  