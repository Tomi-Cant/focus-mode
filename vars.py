from os.path import dirname, abspath, join
import json
import pygame
screen:pygame.surface.Surface
clock : pygame.time.Clock

selected_days = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
title_text = ""
help_open = False
time_selected = False
time_var = ''
parent_path = dirname(abspath(__file__))
path = join(parent_path, "blacklist.json")
with open(path, "r", encoding="utf-8") as f:
    session_temp = json.load(f)
time_group = session_temp['time_list']
sent_list = []
gui_blacklist :pygame.sprite.Group = pygame.sprite.Group()
gui_timelist :pygame.sprite.Group = pygame.sprite.Group()
active_window = "main"
font :pygame.font.Font

large_font : pygame.font.Font

list_end = 15

