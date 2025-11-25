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
        self.keybinds = self.menu.keybinds
        self.game = Game(screen, self.keybinds)
        self.run_menu = True
        self.run_game = False
        self.clock = pygame.time.Clock()

    def event(self):

        events = pygame.event.get()

        if self.run_menu:

            self.run_game, self.running = self.menu.event(events)
            if self.run_game:
                self.run_menu = False

        elif self.run_game:

            self.run_menu, self.running = self.game.event(events)
            if self.run_menu:
                self.run_game = False

    def update(self):

        if self.run_menu:

            self.keybinds = self.menu.update()

        elif self.run_game:

            self.game.update(self.keybinds)

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
