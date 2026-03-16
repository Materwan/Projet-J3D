import pygame
from player import SoloPlayerController, HostController, GuestController
from moteur import Moteur
from map import Map
import time
from camera_system import Camera


class Game:
    """Classe de gestion du jeu : joueur et carte."""

    def __init__(self, screen: pygame.Surface, manager):
        self.screen = screen
        self.manager = manager
        self.playing_mode = None
        self.player_controller = None
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }

        # on initialise la camera à 0 pour pas que ça plante
        width, height = self.screen.get_size()
        self.camera = Camera(width, height, 0, 0)

        self.map = None
        self.map: Map
        self.address = "0.0.0.0"
        self.port = 8888

    def initialize(self):
        """Initialise le moteur, le controlleur à utiliser, les keybinds et la camera"""
        self.moteur = Moteur()

        if self.playing_mode == "guest":
            self.player_controller = GuestController(
                self.screen, self.moteur, self.map, self.address, self.port
            )
            while not self.player_controller.loaded:
                time.sleep(0.2)
            self.map = self.player_controller.map  # recupere la map de client
            self.moteur.map = self.map  # donner à moteur pour Client-side prediction
        else:
            self.map = Map((256, 256), (8, 8), (32, 32), (32, 32), 0, self.screen)
            if self.playing_mode == "solo":
                self.player_controller = SoloPlayerController(
                    self.screen, self.moteur, self.map, (4096, 4096)
                )
            elif self.playing_mode == "host":
                self.player_controller = HostController(
                    self.screen, self.moteur, self.map, (4000, 4096)
                )

        self.player_controller.keybinds = self.keybinds
        self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
        self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
        self.player_controller.set_camera(self.camera)

    def event(self, events: list[pygame.event.Event]) -> bool:
        """Gére les entré de l'utilisateur."""
        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.play(-1)
                    self.manager.states["MENU_PAUSE"].surface_copie = self.screen.copy()
                    self.manager.change_state("MENU_PAUSE")
                elif event.key == pygame.K_SPACE:
                    self.player_controller.attaque = True
                elif event.key == pygame.K_F2:
                    self.player_controller.toggle_hitbox()

        self.player_controller.event(pygame.key.get_pressed())

    def update(self):
        """Met à jour le jeu."""
        self.player_controller.update()
        self.camera.update(self.player_controller.hitbox)

        if self.player_controller.close:
            self.manager.running = False

    def display(self):
        """Affiche tout les éléments."""
        self.screen.fill((100, 100, 100))
        self.camera.display_map(self.map)
        self.player_controller.display()
