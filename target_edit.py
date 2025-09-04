import pygame
import sys, os
import json
import new_window as nw
import sprite_gen as sg
from os.path import dirname,abspath,join
from tkinter import filedialog

parent_path = dirname(abspath(__file__))
path=join(parent_path,"blacklist.json")
error=False

with open(path, "r",encoding="utf-8") as f:
    temp=json.load(f)
no_list=temp['added_list']
allowed_chars=temp['allowed_chars']
pygame.init()

screen = pygame.display.set_mode((800, 800))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)

class button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, text,func,args=None):
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


class text_edit(button):
    
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
                    self.enter(self.text)
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    print(f"{self.text =}")   
        elif not self.active:
            self.color = (255,255,255)
            self.image.fill(self.color)
        self.text_sur = self.font.render(self.text, True, (0,0,0))
        self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
        
    
    def enter(self,text):
        no_list.append(text)
        
def add_to_blacklist():
    file_path = filedialog.askopenfilename(
    title="Select a file",
    filetypes=[("All files", "*.*"), ("Text files", "*.txt"), ("Executeable files", "*.exe")]
    #TODO: convert file to something for the blacklist
)
def remove_from_blacklist():
    print("remove distraction")
def help():
    print("help")
def save():
    if time_is_valid==True:
        print("save and exit")
        exit()
    else:
       error =True

    
    #TODO: make a time invalid message (prob with make window)
def time_is_valid() ->bool:
    numbers=['1','2','3','4','5','6','7','8','9','0']
   
    if 0<len(hour_box.text)<2 or 0<len(minute_box.text)<2:
        return False
    combined=hour_box.text+minute_box.text
    for i in hour_box and combined:
        if i in numbers:
            continue 
        else: 
            return False
    if int(hour_box.text)>24 and int(minute_box.text)>59:
        return False
    print(len(hour_box.text),len(minute_box.text))
    return True
    
def exit():
    with open(path, "w",encoding="utf-8") as f:
        json.dump(temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()
    
def enter():
    distraction_input.enter(distraction_input.text)
buttons = pygame.sprite.Group()
buttons.add(button(100, 50, 175, 50, (255,0,0), "Add To List",add_to_blacklist))
buttons.add(button(100, 150, 175, 50, (255,0,0), "Remove From List",remove_from_blacklist))
buttons.add(button(100, 250, 175, 50, (255,0,0), "Help",help))
buttons.add(button(100, 350, 175, 50, (255,0,0), "Save & Exit",save))
buttons.add(button(100, 450, 175, 50, (255,0,0), "Enter",enter))
distraction_input=text_edit(133,550,251,50,(255,255,255),"Enter Program Name")
hour_box=text_edit(100,650,175,50,(255,255,255),temp['set_hour'])
minute_box=text_edit(300,650,175,50,(255,255,255),temp['set_minute'])
text_boxes= pygame.sprite.Group()
text_boxes.add(distraction_input,hour_box,minute_box)
def draw():
    screen.blit(font.render("Focus Mode", True, (255, 255, 255)), (100, 100))
    screen.fill((75,75,75))
    buttons.draw(screen)        
    text_boxes.draw(screen)
    if error:
         nw.new_window(400,400,325,150,(255,255,255),"Error!") 
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