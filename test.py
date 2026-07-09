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

# import datetime
# print(datetime.date.today().strftime("%a")) # sends abbrivated version of day of the week. %A for full day name
# foo={
# }
# foo['a']
# print(foo)
# s="9"
# s.capitalize()
# print(s)
# now=str(datetime.datetime.now())
# now=now.split(' ')[0]
# print(now)


# import webbrowser,webob
# from urllib import parse
# parse.
# import pyautogui,time
# while True:
    
#     print(pyautogui.position())
#     time.sleep(.5)

# import psutil

# for conn in psutil.net_connections():
#     for proc in psutil.process_iter(['pid', 'name']):
#         if proc.info['pid'] == conn.pid:
#             if 'opera' in proc.info['name'].lower():
#                 print(f"Port: {conn.laddr} → {conn.raddr} Status: {conn.status}")
                
                
# import urllib.request
# import subprocess
# url = "https://npcap.com/dist/npcap-1.79.exe"
# def download_npcap():
#     url = "https://npcap.com/dist/npcap-1.79.exe"
#     urllib.request.urlretrieve(url, "npcap-installer.exe")
#     subprocess.run(["npcap-installer.exe", "/S", "/winpcap_mode=yes"])
# print(url.split('z'))
import re
instances =[ 'Minecraft* 1.20.4', 'Minecraft 1.20.3', 'Minecraft 1.19.4', 'Minecraft 1.18.2', 'Minecraft 1.17.1', 'Minecraft 1.16.5', 'Minecraft 1.15.2', 'Minecraft 1.14.4', 'Minecraft 1.13.2', 'Minecraft 1.12.2', 'Minecraft 1.11.2', 'Minecraft 1.10.2', 'Minecraft 1.9.4', 'Minecraft 1.8.9', 'Minecraft 1.7.10', "Minecraft 1.9", "Minecraft 1.8", "Minecraft 1.7", "Minecraft 1.6", "Minecraft 1.5", "Minecraft 1.4", "Minecraft 1.3", "Minecraft 1.2", "Minecraft 1.1", "Minecraft 1.0"]
pattern = r"Minecraft\*?\s\d+\.\d+\.?\d+?"
for instance in instances:
    print(re.findall(pattern,instance))
