import pygame
def shorten(text: str, box_width: int, font) -> str:
    tries=0
    # condesnses text till it can fit within the given constraints of the surface
    render = font.render(text, True, (0, 0, 0))
    
    if render.get_width() <= box_width:
        return text
    while render.get_width() > box_width and tries < 1000:
        tries+=1
        text = text[:-1]
        render = font.render(text+'...', True, (0, 0, 0))

    text = text.rstrip()
    text = text+'...'
    return text


def cull_times(set, end, indx, time):
    if time >= end[indx]:  # checks if end time is passed if so remove from list with pair
        del end[indx]
        del set[indx]


def time_seperator(time: str) -> tuple[str, str]:
    return time[:2], time[3:]

def get_active_texts(sprites: pygame.sprite.Group,func) -> list:
    output=[]
    if func!=None:
        for i in sprites.sprites():
            if i.active:
                output.append(func(i))
    else:
        for i in sprites.sprites():
            if i.active:
                output.append(i.text.strip())
            
    return output