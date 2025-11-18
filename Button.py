import pygame
from helper_funcs import shorten
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color,font:pygame.font.Font, text:str='',func=None,args=None,text_color=(0,0,0)):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([width, height], pygame.SRCALPHA)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.y=y
        self.rect.center = (x, y)
        self.text=text
        self.color = color
        self.font = font
        self.text_sur = self.font.render(shorten(self.text,self.rect.width-10,self.font), True,(0,0,0))
        self.text_color=text_color
        self.func =func
        self.args=args

    def update(self,event,pos,refresh=False,time_selected=True):
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
                    else:
                        return True
                    self.color = (0,0,255)
                    self.image.fill(self.color)
            else:
                self.color = (255,0,0)
                self.image.fill(self.color)
            self.rect = self.image.get_rect(topleft=self.rect.topleft) 
            self.text_sur = self.font.render(shorten(self.text,self.rect.width-10,self.font), True, self.text_color)
            self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
        else:
            self.rect = self.image.get_rect(topleft=self.rect.topleft) 
            self.text_sur = self.font.render(shorten(self.text,self.rect.width-10,self.font), True, self.text_color)
            self.image.blit(self.text_sur, self.text_sur.get_rect(top=self.rect.top-self.y+40))
            
    def draw(self,screen):
        screen.blit(self.image,self.rect)
        

