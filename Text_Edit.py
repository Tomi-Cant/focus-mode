import Button
import pygame
import vars
from helper_funcs import shorten




allowed_chars = vars.session_temp['allowed_chars']
shift_parallel = vars.session_temp['shift_parallel']


class Text_Edit(Button.Button):
    def __init__(self, x, y, width, height, color, text, font, muteable=True, text_color=(0, 0, 0), active=False,win='main'):
        super().__init__(x, y, width, height, color, font, text, func=None, args=None,win='main')
        self.active = active
        self.muteable = muteable
        self.text_color = text_color
        self.back_pressed = False
        self.pressed_keys = []
        self.alt_code = []

    def update(self, event, pos, win:str = 'main', time_selected=False):

        if self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active

            super().update(event, pos, win)  # calls button update method
        if not self.rect.collidepoint(pos) and event.type == pygame.MOUSEBUTTONDOWN:
            if not time_selected and self.muteable:
                self.active = False
            super().update(event, pos, win)  # calls button update method
        if self.back_pressed:
            self.text = self.text[:-
                                  1] if self.text != "Enter Program Name" else ""
            self.active = True
            self.back_pressed = False
        if self.active:
            if self.text == "Enter Program Name" or self.text == '00':
                self.text = ""
            self.color = (150, 150, 255)
            # checks if meant to be a static textbox
            if self.muteable:

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_BACKSPACE:
                        self.back_pressed = True
                        self.active = False
                if event.type == pygame.KEYDOWN:
                    self.pressed_keys.append(pygame.key.name(event.key))
                    # checks if shift is pressed and doesnt print shift with char (need to do number symbols)
                    if "left alt" in self.pressed_keys or "right alt" in self.pressed_keys:
                        if (pygame.key.name(event.key).isdigit()):
                            self.alt_code.append(pygame.key.name(event.key))
                    elif pygame.key.name(event.key) in allowed_chars and "left shift" in self.pressed_keys or "right shift" in self.pressed_keys:
                        if len(pygame.key.name(event.key)) == 1:
                            self.text += shift_parallel[pygame.key.name(
                                event.key)]
                    # and "left alt" in self.pressed_keys or "right alt" in self.pressed_keys :
                    elif pygame.key.name(event.key) in allowed_chars and len(pygame.key.name(event.key)) == 1:
                        self.text += pygame.key.name(event.key)
                    if event.key == pygame.K_RETURN:
                        self.active = False
                if event.type == pygame.KEYUP:
                    self.pressed_keys.remove(pygame.key.name(event.key))
                    if event.key == pygame.K_LALT or event.key == pygame.K_RALT:
                        temp_str = ''

                        for i in self.alt_code:
                            temp_str += i
                        try:
                            self.text += chr(int(temp_str, 16))

                        except (ValueError):
                            pass
                        self.alt_code = []
                        # altcode doesnt exist error message

        elif not self.active:
            self.color = (255, 255, 255)
            self.image.fill(self.color)
        super().update(event, pos,self.win, True)  # calls button update method
        self.text_sur = self.font.render(
            shorten(self.text, self.rect.width-10, self.font), True, self.text_color)
        self.image.fill(self.color)  # thanks copilot
        self.image.blit(self.text_sur, self.text_sur.get_rect(
            top=self.rect.top-self.y+40))

    # meant for specific textboxes
    def enter(self, text, added_list) -> bool:

        if text != "Enter Program Name" or text != "":
            added_list.append(text)
            vars.session_temp['time_list'][vars.time_var]['programs'].append(text)

            return True
        else:
            error_text = "Error! Please enter a program name."
            error = True
            return False
