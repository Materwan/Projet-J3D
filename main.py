import logging
import traceback

import pygame

from menu import (
    Principal_Menu,
    Setting_Menu,
    Play_Menu,
    Join_Multi_Menu,
    Pause_Menu,
    Reprendre_Menu,
    Creer_Menu,
)
from game import Game
from player import HostController, GuestController
from sound import SoundController

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("MoleTale")

FPS = 60
TAILLE_ECRAN = (500, 500)  # (500, 500) pour petit ecran (0, 0) pour plein ecran

SOUND_PATH = "Ressources/Musics/"
MUSIC_HOLDER = SOUND_PATH + "placeholder.mp3"
SOUND_AMBIANCE = SOUND_PATH + "ambiance.mp3"
SOUND_FOOTSTEP = SOUND_PATH + "footstep.mp3"
SOUND_ATTACK = SOUND_PATH + "attack.mp3"
SOUND = {
    "main_music": SoundController(MUSIC_HOLDER),
    "ambiance": SoundController(SOUND_AMBIANCE),
    "footstep": SoundController(SOUND_FOOTSTEP, 1),
    "attack": SoundController(SOUND_ATTACK, 1),
}

screen = pygame.display.set_mode(TAILLE_ECRAN)


class Manager:
    """Gestionnaire des états du jeu."""

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
            "MENU_REPRENDRE": Reprendre_Menu(self.screen, self),
            "MENU_CREER": Creer_Menu(self.screen, self),
        }
        self.state = self.states["MENU_P"]

        self.fps = False
        self.font = pygame.font.SysFont(None, 24)  # fps
        self.clock = pygame.time.Clock()
        SOUND["main_music"].plays_sound()

    def change_state(self, name):
        self.state.update()
        self.state = self.states[name]
        if name == "GAME":
            SOUND["main_music"].stop_sound()
            SOUND["ambiance"].plays_sound()
        else:
            SOUND["ambiance"].stop_sound()
            SOUND["main_music"].plays_sound()

    def run(self):
        while self.running:

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
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

    def change_volume(self, change_volume: bool):
        """True = increase the volume of all sounds | False = decrease the volume of all sounds"""
        if change_volume:
            for key in SOUND.keys():
                SOUND[key].volume_increase()
        else:
            for key in SOUND.keys():
                SOUND[key].volume_decrease()


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
