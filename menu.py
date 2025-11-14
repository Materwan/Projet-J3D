import pygame as p

p.init()

WINDOWS = p.display.get_desktop_sizes()[0]   #fullscreen

screen = p.display.set_mode(WINDOWS)
clock = p.time.Clock()
running = True

class Bouton:

    def __init__(self, left, top, width, height, color):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = p.Color(color)
        self.rec = p.Rect(left, top, width, height)
        self.surface = p.Surface((width, height))


    def draw(self):                     #display the button
        self.surface.fill(self.color)
        screen.blit(self.surface, (self.left, self.top))

bouton = Bouton(WINDOWS[0]-200,0,200,200,(0, 0, 255))

while running:
    
    screen.fill((0, 0, 0)) #background

    for event in p.event.get():
        if event.type == p.QUIT:
            running = False

        if event.type == p.MOUSEBUTTONDOWN: #si bouton est cliqué alors on ferme le menu
            x,y = p.mouse.get_pos()
            if bouton.rec.collidepoint(x,y):
                running = False

    bouton.draw()

    p.display.update()


    clock.tick(60)

p.quit()