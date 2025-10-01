# import win32gui,win32con,win32process
# import psutil
# win = win32gui.GetForegroundWindow()
# print(win)
# id=win32process.GetWindowThreadProcessId(win)
# print(psutil.Process(id[1]))
# dict= {
#    '1':[1,2,3],
#     '2':['wasd','qwe','asd','zxc','sdf'],
#    "3": [213,123,321,213,123,]
# }
# l=dict['1']
# l.append(6)
# print(dict['1'])

# o=dict['1']+dict['3']
# for i in o:
#    print(i)
# set_hour=0
# set_minute=100
# import datetime
# print(datetime.datetime.now().hour)
# if datetime.datetime.now().replace(hour=set_hour,minute=set_minute)> datetime.datetime.now():
#    pass
# import pygame
# pygame.init()
# font=pygame.font.SysFont("Arial",20)
# this="This is long text for this box   "

# def shorten(text:str,box_width:int)-> str:
#     render=font.render(text,True,(255,255,255))
#     while render.get_width()>box_width:
#        text=text[:-1]
#        render=font.render(text+'...',True,(255,255,255))
#     text=text.rstrip()
#     text=text+'...'
#     return text
# print(shorten(this,200))
# import pygame

# pygame.init()
# screen = pygame.display.set_mode((640, 480))
# clock = pygame.time.Clock()

# def main():
#    while True:
#       for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                pygame.quit()
#                return
#             elif event.type == pygame.MOUSEWHEEL:
#                print(event)
#                print(event.x, event.y)
#                print(event.flipped)
            
#                # can access properties with
#                # proper notation(ex: event.y)
#       clock.tick(60)

# # Execute game:
# # main()
# from datetime import datetime
# datetime.now().replace(hour=17,minute=10)
# foo={
# }
# foo['a']
# print(foo)
s="9"
s.capitalize()
print(s)