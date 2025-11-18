def shorten(text:str,box_width:int,font)-> str:
    #condesnses text till it can fit within the given constraints of the surface
    render=font.render(text,True,(0,0,0))
    if render.get_width()<=box_width:
        return text
    while render.get_width()>box_width:
        text=text[:-1]
        render=font.render(text+'...',True,(0,0,0))
    
    text=text.rstrip()
    text=text+'...'
    return text

def cull_times(set, end,indx, time):
         if  time>=end[indx]: # checks if end time is passed if so remove from list with pair
                del end[indx]
                del set[indx]       

def time_seperator(time:str)-> tuple[str,str]:
        return time[:2],time[3:]
    