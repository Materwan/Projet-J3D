import pygame
from menu import *
from game import *

pygame.init()
pygame.mixer.init()


class Manager:

    def __init__(self):
        self.screen = pygame.display.set_mode((0, 0))
        self.running = True

        self.states = {
            "MENU_P": Principal_Menu(self.screen, self),
            "MENU_SETTING": Setting_Menu(self.screen, self),
            "GAME": Game(self.screen, self),
            "MENU_PLAY": Play_Menu(self.screen, self),
            "MENU_MULTI": Join_Multi_Menu(self.screen, self),
        }
        self.state = self.states["MENU_P"]

        self.font = pygame.font.SysFont(None, 24)  # fps
        self.clock = pygame.time.Clock()

    def change_state(self, name):
        self.state = self.states[name]

    def run(self):
        while self.running:

            self.state.event(pygame.event.get())

            self.state.update()

            self.state.display()
            self.screen.blit(
                self.font.render(
                    f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255)
                ),
                (10, 10),
            )  # fps
            pygame.display.flip()

            self.clock.tick(60)  # à ne pas toucher


Manager().run()
pygame.quit()
