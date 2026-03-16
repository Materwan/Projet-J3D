import pygame

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("MoleTale")
FPS = 60
TAILLE_ECRAN = (500, 500)  # (0, 0) pour plein écran
screen = pygame.display.set_mode(TAILLE_ECRAN)

from menu import *
from game import *
from player import HostController, GuestController
import logging
import traceback


class Manager:

    def __init__(self):
        self.screen = screen
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

        self.fps = False
        self.font = pygame.font.SysFont(None, 24)  # fps
        self.clock = pygame.time.Clock()

    def change_state(self, name):
        self.state = self.states[name]

    def run(self):
        while self.running:

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        self.fps = not self.fps
            self.state.event(events)

            self.state.update()

            self.state.display()

            if self.fps:  # fps
                self.screen.blit(
                    self.font.render(
                        f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255)
                    ),
                    (10, 10),
                )

            pygame.display.flip()

            self.clock.tick(FPS)  # à ne pas toucher

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
                self.states["GAME"].player_controller.stop_server()


manager = Manager()

try:
    manager.run()
except Exception as e:
    # Arrête le jeu en cas d'erreure
    manager.running = False
    manager.states["MENU_MULTI"].udp_event.clear()
    if isinstance(
        manager.states["GAME"].player_controller, (HostController, GuestController)
    ):
        manager.states["GAME"].player_controller.close = True
        if isinstance(manager.states["GAME"].player_controller, HostController):
            manager.states["GAME"].player_controller.asyncio_loop.call_soon_threadsafe(
                manager.states["GAME"].player_controller.serveur.close()
            )

    logging.error(traceback.format_exc())  # affiche quand-même l'erreure

except KeyboardInterrupt:

    manager.running = False
    manager.states["MENU_MULTI"].udp_event.clear()
    if isinstance(
        manager.states["GAME"].player_controller, (HostController, GuestController)
    ):
        manager.states["GAME"].player_controller.close = True
        if isinstance(manager.states["GAME"].player_controller, HostController):
            manager.states["GAME"].player_controller.asyncio_loop.call_soon_threadsafe(
                manager.states["GAME"].player_controller.serveur.close()
            )

    logging.error(traceback.format_exc())  # affiche quand-même l'erreure

else:
    if isinstance(
        manager.states["GAME"].player_controller, (HostController, GuestController)
    ):
        manager.states["GAME"].player_controller.close = True

finally:
    pygame.quit()
