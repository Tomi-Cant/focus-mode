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
        self.active = False
         #self.exit_btn = Button(
    # 100, 550, 30, 30, (69, 69, 69, 69), large_font, "X", self.active)
        # self.exit_btn.rect.topleft = (width - 40, 10)
        
        self.txt_lines = txt_lines
        self.font = pygame.font.SysFont("Arial", 20)
        self.title = title
        if window_type == 'error':
            self.timer = 0
        if title != None:
            self.title_text = pygame.font.SysFont(
                "Arial", 20).render(title, True, (255, 255, 255))
            self.image.blit(self.title_text, (125, 0))

    def update(self, event, pos, screen: pygame.surface.Surface, sprites=[]):
        if self.active:
            # self.exit_btn.update(event, pos,self.window_type)
            if self.window_type == 'error':
                self.timer += 1
            for sprite in sprites:
                sprite.update(event, pos,self.window_type)
            # if self.exit_btn.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
                self.active = False

    def draw(self, screen: pygame.surface.Surface, sprites=[]):

        
        screen.blit(self.image, self.image.get_rect(topleft=(200, 200)))
        for sprite in sprites:
            sprite.draw(screen)
        for i in self.txt_lines:
            temp = self.font.render(i, True, (255, 255, 255))
            self.image.blit(temp, temp.get_rect(topleft=(10, 100)))
        # self.exit_btn.draw(self.image)
