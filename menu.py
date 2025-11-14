import pygame as p

p.init()

p.font.init()
my_font = p.font.SysFont('Comic Sans MS', 30)

WINDOWS = p.display.get_desktop_sizes()[0]   #fullscreen

screen = p.display.set_mode(WINDOWS)


class Text:

    def __init__(self,name,size,text,t_color,antialias=False):
        self.text = p.font.SysFont(name,size).render(text,antialias,t_color)
    
    def draw_text(self,coordonninate):
        screen.blit(self.text,coordonninate)

class Bouton:

    def __init__(self,left,top,width,height,color,text=Text('',0,'',(0,0,0))):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = p.Color(color)
        self.rec = p.Rect(left, top, width, height)
        self.surface = p.Surface((width, height))
        self.text = text


    def draw(self):                     #affiche le bouton
        self.surface.fill(self.color)
        screen.blit(self.surface, (self.left, self.top))
        self.text.draw_text((self.left+(self.width//4),self.top+(self.height//3)+10))

class Menu:

    def __init__(self):
        self.screen = screen
        self.clock = p.time.Clock()
        self.running = True
        self.bouton = Bouton(WINDOWS[0]-200,0,200,200,(0, 0, 255),Text('Comic Sans MS',30,'Quitter',(255,0,0)))

    def event(self):
        events = p.event.get()
        for event in events:
            if event.type == p.QUIT:
                self.running = False

            if event.type == p.MOUSEBUTTONDOWN: #si bouton est cliqué alors on ferme le menu
                if self.bouton.rec.collidepoint(p.mouse.get_pos()):
                    self.running = False
    
    def update(self):
        p.display.update()

    def display(self):
        self.screen.fill((0, 0, 0)) #background
        self.bouton.draw()

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.display()

            self.clock.tick(60)


Menu().run()
p.quit()