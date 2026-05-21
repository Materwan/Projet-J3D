import logging
import traceback
import os
import sys
import pygame

from utils import resource_path, DefaultManager
from menu import (
    Principal_Menu,
    Setting_Menu,
    Play_Menu,
    Join_Multi_Menu,
    Pause_Menu,
    Solo_Menu,
    Multiplayer_Menu,
    Death_Screen,
)
from game import Game
from sound import SoundController
from loading import GameLoadingScreen, WaitingGuestScreen

pygame.init()
pygame.mixer.init()
pygame.display.set_caption("MoleTale")

FPS = 60
TAILLE_ECRAN = (500, 500)  # (500, 500) pour petit ecran (0, 0) pour plein ecran

SOUND_PATH = resource_path("Ressources/Musics/")
MUSIC_HOLDER = os.path.join(SOUND_PATH, "placeholder.mp3")
SOUND_AMBIANCE = os.path.join(SOUND_PATH, "ambiance.mp3")
SOUND_FOOTSTEP = os.path.join(SOUND_PATH, "footstep.mp3")
SOUND_ATTACK = os.path.join(SOUND_PATH, "attack.mp3")
SOUND = {
    "main_music": SoundController(MUSIC_HOLDER),
    "ambiance": SoundController(SOUND_AMBIANCE),
    "footstep": SoundController(SOUND_FOOTSTEP, 1),
    "attack": SoundController(SOUND_ATTACK, 1),
}

screen = pygame.display.set_mode(TAILLE_ECRAN, pygame.RESIZABLE)
if TAILLE_ECRAN == (0, 0):
    TAILLE_ECRAN = screen.get_size()


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
            "MENU_SOLO": Solo_Menu(self.screen, self),
            "MENU_MULTIPLAYER": Multiplayer_Menu(self.screen, self),
            "DEATH_SCREEN": Death_Screen(self.screen, self),
            "LOADING": GameLoadingScreen(self.screen, self),
            "WAITING_GUEST": WaitingGuestScreen(self.screen, self),
        }
        self.state: DefaultManager = self.states["MENU_P"]

        self.fps = False
        self.font = pygame.font.SysFont(None, 24)  # texte pour fps
        self.clock = pygame.time.Clock()
        self.last_screen_size = TAILLE_ECRAN

    def resize(self, size, current: str | None = None):
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        for value in self.states.values():
            value.set_screen(screen)
        if current is None:
            pass
        elif current == "MENU_PAUSE":
            self.state = self.states["MENU_SETTING_PAUSE"]
        else:
            self.state = self.states["MENU_SETTING"]

    def change_state(self, name: str):
        self.state = self.states[name]
        if name == "GAME" or name == "WAITING_GUEST":
            SOUND["main_music"].stop_sound()
            SOUND["ambiance"].plays_sound()
        else:
            SOUND["ambiance"].stop_sound()
            SOUND["main_music"].plays_sound()

    def change_volume(self, change_volume: bool):
        """True = increase the volume of all sounds | False = decrease the volume of all sounds"""
        if change_volume:
            for key in SOUND.keys():
                SOUND[key].volume_increase()
        else:
            for key in SOUND.keys():
                SOUND[key].volume_decrease()

    def debug(self):

        # -- Game --
        if self.state == self.states["GAME"]:
            self.state._debug(self.font)

        # -- Menu --
        else:
            self.screen.blit(
                self.font.render(
                    f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255)
                ),
                (10, 10),
            )
            for key, value in self.states.items():
                if value == self.state:
                    self.screen.blit(
                        self.font.render(key, True, (255, 255, 255)), (10, 32)
                    )
                    pos = pygame.mouse.get_pos()
                    self.screen.blit(
                        self.font.render(
                            str(pos),
                            True,
                            (255, 255, 255),
                        ),
                        (10, 54),
                    )

    def run(self):
        while self.running:

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                    self.fps = not self.fps
            self.state.event(events)

            if self.last_screen_size != self.screen.get_size():
                self.resize(self.screen.get_size())
                self.last_screen_size = self.screen.get_size()
            self.state.update()

            self.state.display()

            if self.fps:
                self.debug()

            pygame.display.flip()

            self.clock.tick(FPS)  # à ne pas toucher

        self.states["GAME"].close_network()


manager = Manager()

# écran de chargement
police_text = pygame.font.SysFont("segoeui", 100, bold=True)
larg, haut = screen.get_size()
fond_noir = pygame.Surface((larg, haut))
fond_noir.fill((0, 0, 0))

title = police_text.render("MoleTale", True, (230, 210, 160))
pos_title = (larg // 2 - title.get_width() // 2, haut // 2 - title.get_height() + 40)


def check_quit_during_loading():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


for alpha in range(255, -1, -4):
    check_quit_during_loading()

    screen.fill((14, 14, 22))
    screen.blit(title, pos_title)

    fond_noir.set_alpha(alpha)
    screen.blit(fond_noir, (0, 0))
    pygame.display.flip()
    manager.clock.tick(60)

for _ in range(60):
    check_quit_during_loading()
    manager.clock.tick(60)

for alpha in range(0, 256, 4):
    check_quit_during_loading()

    screen.fill((14, 14, 22))
    screen.blit(title, pos_title)

    fond_noir.set_alpha(alpha)
    screen.blit(fond_noir, (0, 0))
    pygame.display.flip()
    manager.clock.tick(60)

SOUND["main_music"].plays_sound()

for alpha in range(255, -1, -4):
    check_quit_during_loading()

    manager.states["MENU_P"].display()

    fond_noir.set_alpha(alpha)
    screen.blit(fond_noir, (0, 0))
    pygame.display.flip()
    manager.clock.tick(60)

try:
    manager.run()
except (Exception, KeyboardInterrupt):
    manager.running = False
    manager.states["MENU_MULTI"].udp_event.clear()
    manager.states["GAME"].close_network()
    logging.error(traceback.format_exc())
finally:
    pygame.quit()
