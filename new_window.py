import pygame
from Button import Button
import vars

class Popup_Window(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color, title='', window_type='', txt_lines: list[str] = []):
        super().__init__()
        self.window_type = window_type
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.color = color
        self.y = y
        self.x = x
        self.active = False
        self.exit_btn =  Button(
    width-35, 35, 40, 40, (0, 69, 69, 0), vars.font, "X", self.close_win)
        self.txt_lines = txt_lines
        self.font = pygame.font.SysFont("Arial", 20)
        self.title = title
        if window_type == 'error':
            self.timer = 0
        if title != None:
            self.title_text = pygame.font.SysFont(
                "Arial", 20).render(title, True, (255, 255, 255))
            self.image.blit(self.title_text, self.title_text.get_rect(center=(width//2-30, 30)))
            
    def close_win(self):
        self.active = False
        
        
    def update(self, event, pos, sprites=[]):
        
        pos= (pos[0]-self.rect.x, pos[1]-self.rect.y)
        if self.active:
            self.exit_btn.update(event, pos,self.window_type)
            if self.window_type == 'error':
                self.timer += 1
                if self.timer > 180:  # auto close after 3 seconds
                    self.active = False
                    self.timer = 0
            for sprite in sprites:
                sprite.update(event, pos,self.window_type)
            if self.exit_btn.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
                self.active = False

    def draw(self, screen: pygame.surface.Surface, sprites=[]):

        for sprite in sprites:
            sprite.draw(self.image)
        for i in self.txt_lines:
            temp = self.font.render(i, True, (255, 255, 255))
            self.image.blit(temp, temp.get_rect(topleft=(10, 100))) #fix needed pos and whatnot
        self.exit_btn.draw(self.image)
        screen.blit(self.image, self.rect)
