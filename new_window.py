import pygame

class new_window(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,color,title:str|None):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.color = color
        self.title=title
        active=False
        if title != None:
            self.title=pygame.font.SysFont("Arial", 20).render(title, True, (255,255,255))
            self.image.blit(self.title,(0,0))
        
    def update(self,txt_lines:list[dict]):
        
        for i in txt_lines:
            self.image.blit(i['text'],i['position'],i['size'])
            