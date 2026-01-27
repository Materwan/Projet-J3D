import pygame
from menu import Menu
from game import Game

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((0, 0))


class Loop:

    def __init__(self, screen):
        self.screen = screen
        self.running = True
        
        self.menu = Menu(screen)
        self.game = Game(screen)
        self.state = self.menu

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24) # fps

    def event(self):
        if self.state.event(pygame.event.get()): # si evenement important alors :
            prochaine_etat = self.state.prochaine_etat
            if prochaine_etat == "GAME":
                self.state = self.game
                self.game.player.keybinds = self.menu.keybinds
                pygame.mixer.music.stop()
            elif prochaine_etat == "MENU":
                self.state = self.menu
                pygame.mixer.music.play(-1)
            else: # <==> elif prochaine_etat == "CLOSE":
                self.running = False

    def update(self):
        self.state.update()

    def display(self):
        self.state.display()
        self.screen.blit(self.font.render(f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255)), (10, 10)) # fps
        pygame.display.flip()  # ne pas utiliser .update()

    def run(self):
        
        while self.running:

            self.event()
            self.update()
            self.display()

            self.clock.tick(60) # à ne pas toucher


Loop(screen).run()

pygame.quit()