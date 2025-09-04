import pygame
def generate_matrix(group:pygame.sprite.Group,obj,num:int,rows:int,x,y,width,height,x_step,y_step,**kwargs)-> tuple[pygame.sprite.Group,list]:
    matrix=[]
    length=num//rows
    
    temp_x=x
    for row in range(rows):
        temp_list=[]
        for sprite in range(length):

            temp_list.append(group.add(obj(x,y,width,height,**kwargs)))
            temp_x+=x_step
        y+=y_step
        temp_x=x
        matrix.append(temp_list)
    return group,matrix

def generate_line(group:pygame.sprite.Group,obj,num:int,x,y,width,height,x_step,y_step,up_down:bool=False,**kwargs)-> pygame.sprite.Group:
    #change to choose direction up/down or left/right
    for sprite in range(num):
        group.add(obj(x,y,width,height,**kwargs))
        if up_down:
            y+=y_step
        else:
            x+=x_step
    return group
# make def for text
def generate_text(group:pygame.sprite.Group,surface:pygame.surface.Surface,text:str,x,y,width,height,x_step,y_step,updown:bool=True,**kwargs):
    font = pygame.font.SysFont("Arial", 20)
    for line in text:
        temp_text= font.render(line, True, (255,255,255))
        temp_text.blit(surface,(x,y))
        if updown:
            y+=y_step
        else:
            x+=x_step
            
class test(pygame.sprite.Sprite):
    def __init__(self,*args):
        super().__init__()
print(generate_matrix(pygame.sprite.Group(),test,10,2,2,10,23,100,100,10))