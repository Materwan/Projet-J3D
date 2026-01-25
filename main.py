import pygame
from menu import Menu
from game import Game

pygame.init()
pygame.mixer.init()

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
        self.font = pygame.font.SysFont(None, 24) # fps

    def event(self):

        events = pygame.event.get()

        if self.run_menu:

            self.run_game, self.running = self.menu.event(events)
            if self.run_game:
                self.game.player.keybinds = self.menu.keybinds
                self.run_menu = False
                pygame.mixer.music.stop()

        elif self.run_game:

            self.run_menu = self.game.event(events)
            if self.run_menu:
                self.run_game = False
                pygame.mixer.music.play(-1)

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
