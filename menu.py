import pygame as p
from game import Game

p.init()

p.font.init()

WINDOWS = p.display.get_desktop_sizes()[0]   #fullscreen

screen = p.display.set_mode(WINDOWS)


class Text:

    def __init__(self, name, size, text, t_color, antialias=False):
        self.font = p.font.SysFont(name, size)
        self.text = self.font.render(text, antialias, t_color)
        self.l = self.text.get_size()
    
    def draw_text(self, coordonninate):
        screen.blit(self.text, coordonninate)

class Bouton:

    def __init__(self, left, top, width, height, color, text=Text('', 0, '', (0, 0, 0))):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = p.Color(color)
        self.rec = p.Rect(left, top, width, height)
        self.rec2 = p.Rect(left+15, top+15, width-30, height-30)
        self.text = text


    def draw(self):                     #affiche le bouton
        p.draw.rect(screen, self.color, self.rec)
        p.draw.rect(screen, (0, 0, 0), self.rec2)
        self.text.draw_text(((self.width-self.text.l[0])//2+self.left,(self.height -self.text.l[1])//2+self.top))

class Menu:

    def __init__(self):
        self.screen = screen
        self.clock = p.time.Clock()
        self.running = True
        self.start = Bouton(WINDOWS[0]//2 -100, WINDOWS[1]//2-150, 200, 100, (61, 239, 73), Text('Impact', 30, 'Start', (255, 0, 0)))
        self.settings = Bouton(WINDOWS[0]//2 -100, WINDOWS[1]//2-25, 200, 100, (61, 239, 73), Text('Impact', 30, 'Settings', (255, 0, 0)))
        self.quitter = Bouton(WINDOWS[0]//2-100, WINDOWS[1]//2 +100, 200, 100, (61, 239, 73), Text('Impact', 30, 'Quitter', (255, 0, 0)))
        self.pagemenu = True
        self.settingstext = Text('Impact', 50, 'Page pour changer les touches', (255, 0, 0))
        self.retour = Bouton(0, 0, 200, 100, (61, 239, 73), Text('Impact', 30, '<--', (255, 0, 0)))
        

    def event(self):
        events = p.event.get()
        for event in events:
            if event.type == p.QUIT:
                self.running = False

            if self.pagemenu:
                if event.type == p.MOUSEBUTTONDOWN: #si bouton est cliqué alors on ferme le menu
                    coord = p.mouse.get_pos()
                    if self.quitter.rec.collidepoint(coord):
                        self.running = False
                    elif self.start.rec.collidepoint(coord):
                        Game().run()
                    elif self.settings.rec.collidepoint(coord):
                        self.pagemenu = False
            else:
                if event.type == p.KEYDOWN:
                    if event.key == p.K_ESCAPE:
                        self.pagemenu = True
                if event.type == p.MOUSEBUTTONDOWN:
                    coord = p.mouse.get_pos()
                    if self.retour.rec.collidepoint(coord):
                        self.pagemenu = True

    
    def update(self):
        p.display.flip()

    def display(self):
        self.screen.fill((0, 0, 0))#background
        if self.pagemenu:
            self.start.draw()
            self.settings.draw()
            self.quitter.draw()
        else:
            self.settingstext.draw_text(((WINDOWS[0]-self.settingstext.l[0])//2,(WINDOWS[1]-self.settingstext.l[1])//2))
            self.retour.draw()

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.display()

            self.clock.tick(60)
