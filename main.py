import pygame
from menu import *
from game import *
from player import HostController, GuestController
import logging
import traceback

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("MoleTale")


class Manager:

    def __init__(self):
        self.screen = pygame.display.set_mode((500, 500))
        self.running = True

        self.states = {
            "MENU_P": Principal_Menu(self.screen, self),
            "MENU_SETTING": Setting_Menu(self.screen, self),
            "MENU_SETTING_PAUSE": Setting_Menu(self.screen, self, "MENU_PAUSE"),
            "GAME": Game(self.screen, self),
            "MENU_PLAY": Play_Menu(self.screen, self),
            "MENU_MULTI": Join_Multi_Menu(self.screen, self),
            "MENU_PAUSE": Pause_Menu(self.screen, self),
        }
        self.state = self.states["MENU_P"]

        self.font = pygame.font.SysFont(None, 24)  # fps
        self.clock = pygame.time.Clock()

    def change_state(self, name):
        self.state = self.states[name]
        if name == "GAME":
            self.state.initialize()

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

        # Arrêt les processus multijoueur
        if isinstance(
            self.states["GAME"].player_controller, (HostController, GuestController)
        ):
            # Arrête les processus de communication
            self.states["GAME"].player_controller.close = True
            # Si c'est le serveur, arrête d'accepter les connexions
            if (
                isinstance(self.states["GAME"].player_controller, HostController)
                and self.states["GAME"].player_controller.serveur.is_serving()
            ):
                self.states["GAME"].player_controller.serveur.close()


manager = Manager()

try:
    manager.run()
except Exception as e:
    # Arrête le jeu en cas d'erreure
    manager.running = False
    manager.states["MENU_MULTI"].udp_event.clear()
    if manager.states["GAME"].player_controller != None and isinstance(
        manager.states["GAME"].player_controller, (HostController, GuestController)
    ):
        manager.states["GAME"].player_controller.close = True
        if isinstance(manager.states["GAME"].player_controller, HostController):
            manager.states["GAME"].player_controller.udp_event.clear()

    logging.error(traceback.format_exc())  # affiche quand-même l'erreure
finally:
    pygame.quit()
