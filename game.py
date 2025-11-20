import pygame
from player import Player
from moteur import Moteur

class Game:
    def __init__(self):
        self.running = True
        self.screen = pygame.display.set_mode((0, 0))
        self.moteur = Moteur(self.screen)
        largeur, hauteur = self.screen.get_size()
        self.player = Player(self.screen, largeur//2 -30, hauteur//2 -20, self.moteur)
        self.clock = pygame.time.Clock()


    def event(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

        keys = pygame.key.get_pressed()
        self.player.event(keys)


    def update(self):
        self.player.update()


    def display(self):
        self.screen.fill((100, 100, 100))
        self.moteur.display()
        self.player.display()
        pygame.display.flip() # ne pas utiliser .update()


    def run(self):

        while self.running == True:

            self.event()
            self.update()
            self.display()

            self.clock.tick(60)  # à ne pas toucher
