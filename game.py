import pygame
from player import SoloPlayerController, HostController, GuestController
from moteur import Moteur
import asyncio


class Game:
    def __init__(
        self,
        screen: pygame.Surface,
        manager,
    ):
        self.screen = screen
        self.manager = manager
        largeur, hauteur = self.screen.get_size()
        self.playing_mode = None
        self.player_controller = None
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }

        # ceci est temporaire (remplace la carte)
        self.map = [
            pygame.Rect(0, 0, largeur, 5),
            pygame.Rect(0, hauteur - 5, largeur, 5),
            pygame.Rect(0, 0, 5, hauteur),
            pygame.Rect(largeur - 5, 0, 5, hauteur),
            pygame.Rect(largeur // 2 + 200, hauteur // 2 - 300, 300, 150),
            pygame.Rect(400, 200, 30, 400),
        ]
        self.adresse = "192.168.56.1"
        self.port = 8888

    def initialize(self):
        self.moteur = Moteur(self.screen)
        if self.playing_mode == "solo":
            self.player_controller = SoloPlayerController(
                self.screen, self.moteur, (100, 100)
            )
            self.player_controller.moteur.map = self.map
        elif self.playing_mode == "host":
            self.player_controller = HostController(
                self.screen, self.moteur, (100, 100)
            )
            self.player_controller.moteur.map = self.map
        elif self.playing_mode == "guest":
            self.player_controller = GuestController(
                self.screen, None, (100, 100), self.adresse, self.port
            )
        self.player_controller.keybinds = self.keybinds

    def event(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.play(-1)
                    self.manager.change_state("MENU_P")

        self.player_controller.event(pygame.key.get_pressed())
        return False

    def update(self):
        self.player_controller.update()
        if self.player_controller.close:
            self.manager.running = False

    def display(self):
        self.screen.fill((100, 100, 100))

        # ceci est temporaire (remplace la carte)
        for i in range(4):
            pygame.draw.rect(self.screen, "gold", self.map[i])
        pygame.draw.rect(self.screen, (0, 119, 190), self.map[4])
        pygame.draw.rect(self.screen, "black", self.map[5])
        # fin du temporaire

        self.player_controller.display()
