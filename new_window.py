import pygame

class new_window(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,color,text:list[str],text_start:tuple[int,int]):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.color = color

    def update(self,txt_lines:list[dict]):
        for i in txt_lines:
            self.image.blit(i['text'],i['position'],i['size'])
            