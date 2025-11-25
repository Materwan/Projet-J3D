import pygame
from menu import Menu
from game import Game

pygame.init()

screen = pygame.display.set_mode((0, 0))


class Loop:

    def __init__(self, screen):
        self.running = True
        self.screen = screen
        self.menu = Menu(screen)
        self.game = Game(screen)
        self.run_menu = True
        self.run_game = False
        self.clock = pygame.time.Clock()

    def event(self):

        for event in pygame.event.get():

            if self.run_menu:

                self.run_game = self.menu.event(event)

            elif self.run_game:

                self.run_menu = self.game.event(event)

    def update(self):

        if self.run_menu:

            self.menu.update()

        elif self.run_game:

            self.game.update()

    def display(self):

        if self.run_menu:

            self.menu.display()

        elif self.run_game:

            self.game.display()

    def run(self):

        while self.running:

            self.event()
            self.update()
            self.display()

            self.clock.tick(60)


Loop(screen).run()

pygame.quit()
