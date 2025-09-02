import pygame
import sys, os
import json
from os.path import dirname,abspath,join
from tkinter import filedialog

parent_path = dirname(dirname(abspath(__file__)))
path=join(parent_path,"blacklist.json")

with open(path, "r",encoding="utf-8") as f:
    temp=json.load(f)
no_list=temp['added_list']
allowed_chars=temp['allowed_chars']
pygame.init()

screen = pygame.display.set_mode((800, 600))

pygame.display.set_caption("Focus Mode")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)

class button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, text,func,args):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.y=y
        self.rect.center = (x, y)
        self.text = text
        self.color = color
        self.font = pygame.font.SysFont("Arial", 20)
        self.text = self.font.render(self.text, True, (255,255,255))  
        self.func =func
        self.args=args

    def update(self,event,pos):
        if self.rect.collidepoint(pos):
            self.color = (0,0,200)
            self.image.fill(self.color)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.func != None:
                    self.func(self.args)
                self.color = (0,0,100)
                self.image.fill(self.color)
        else:
            self.color = (255,0,0)
            self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=self.rect.topleft)
        self.image.blit(self.text, self.text.get_rect(top=self.rect.top-self.y+40))
    
class button_group(pygame.sprite.Group):
    def __init__(self):
        pygame.sprite.Group.__init__(self)

class text_edit(button):
    
    def __init__(self, x, y, width, height, color, text):
        super().__init__(x, y, width, height, color, text,func=None,args=None)
        self.active = False
        self.text = text
        self.font = pygame.font.SysFont("Arial", 20)
    def update(self,pos,event):
        if self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active
            super().update(event,pos)
        if self.active:
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) in allowed_chars:
                    self.text += pygame.key.name(event.key)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.enter(self.text)
    def enter(self,text):
        no_list.append(text)
        
def add_distraction():
    file_path = filedialog.askopenfilename(
    title="Select a file",
    filetypes=[("All files", "*.*"), ("Text files", "*.txt"), ("Python files", "*.py")]
    #TODO: convert file to something for the blacklist
)
def remove_distraction():
    print("remove distraction")
def help():
    print("help")
def exit():
    with open(path, "w",encoding="utf-8") as f:
        json.dump(temp,f, ensure_ascii=False, indent=2)
    pygame.quit()
    sys.exit()
def enter():
    text_box.enter(text_box.text)
buttons = button_group()
buttons.add(button(100, 50, 175, 50, (255,0,0), "Add Distraction",add_distraction))
buttons.add(button(100, 150, 175, 50, (255,0,0), "Remove Distraction",remove_distraction))
buttons.add(button(100, 250, 175, 50, (255,0,0), "Help",help))
buttons.add(button(100, 350, 175, 50, (255,0,0), "Save & Exit",exit))
buttons.add(button(100, 450, 175, 50, (255,0,0), "Enter",enter))
text_box=text_edit(100,550,175,50,(255,0,0),"")

def draw():
    screen.blit(font.render("Focus Mode", True, (255, 255, 255)), (100, 100))
    screen.fill((75,75,75))
    buttons.draw(screen)        
    text_box.draw(screen)
    pygame.display.update()
    clock.tick(60)
    
def main():
    while True:
        pos=pygame.mouse.get_pos()
        for event in pygame.event.get():
            buttons.update(event,pos)
            
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    exit()
        draw()
        


if __name__ == "__main__":
    main()  