import pygame

class Popup_Window(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,color,title:str|None):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.color = color
        self.y=y
        self.title=title
        self.active=False
        self.font=pygame.font.SysFont("Arial", 20)
        if title != None:
            self.title=pygame.font.SysFont("Arial", 20).render(title, True, (255,255,255))
            self.image.blit(self.title,(125,0))
        
    def update(self,txt_lines:list[str],exit_btn):
        # used to display the error message.
        for i in txt_lines:
            temp=self.font.render(i, True, (255,255,255))
            self.image.blit(temp,temp.get_rect(topleft=(10,100)))
            