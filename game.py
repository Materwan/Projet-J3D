import pygame
from player import SoloPlayerController, HostController, GuestController
from moteur import Moteur
from map import Map
import time


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
        self.attaque = False
        self.count = 0
        self.liste_ennemie = []
        self.attaque_rect = pygame.Rect(0, 0, 0, 0)
        # Configuration : { "direction": (decalage_x, decalage_y, largeur, hauteur) }
        self.attaque_config = {
            "right": (20, -60, 70, 80),
            "left": (-50, -60, 70, 80),
            "up": (-25, -70, 80, 70),
            "down": (-25, 0, 80, 70),
        }

        self.map = None
        self.map: Map
        self.address = "10.187.208.69"
        self.port = 8888

    def initialize(self):
        """Initialise le moteur et le controlleur à utiliser"""
        self.moteur = Moteur(self.screen)
        if self.playing_mode == "solo":
            self.map = Map((256, 256), (8, 8), (32, 32), (32, 32), 0, self.screen)
            self.player_controller = SoloPlayerController(
                self.screen, self.moteur, self.map, (4096, 4096)
            )
        elif self.playing_mode == "host":
            self.map = Map((256, 256), (8, 8), (32, 32), (32, 32), 0, self.screen)
            self.player_controller = HostController(
                self.screen, self.moteur, self.map, (4000, 4096)
            )
        elif self.playing_mode == "guest":
            self.player_controller = GuestController(
                self.screen, self.map, self.address, self.port
            )
            while not self.player_controller.loaded:
                time.sleep(0.2)
            self.map = self.player_controller.map
        self.player_controller.keybinds = self.keybinds

    def create_rect_attaque(self):
        dec_x, dec_y, wide, high = self.attaque_config[self.player_controller.direction]

        pos_joueur = self.player_controller.rel_position
        # pos_joueur = self.player_controller.abs_position
        return pygame.Rect(pos_joueur.x + dec_x, pos_joueur.y + dec_y, wide, high)

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
                    self.attaque = True
                    self.attaque_rect = self.create_rect_attaque()
                elif event.key == pygame.K_F1:
                    self.manager.fps = not self.manager.fps

        self.player_controller.event(pygame.key.get_pressed())
        return False

    def update(self):
        """Met à jour le jeu."""
        self.player_controller.update()

        if self.attaque:
            self.count += 1
            if any(
                self.attaque_rect.colliderect(obstacle)
                for obstacle in self.liste_ennemie
            ):
                self.attaque = False
                self.count = 0
                # + do something on the Rect obstacle
            elif self.count >= 10:
                self.count = 0
                self.attaque = False

        if self.playing_mode != "solo" and self.player_controller.close:
            self.manager.running = False

    def display(self):
        """Affiche tout les éléments."""
        self.screen.fill((100, 100, 100))

        self.map.display(
            self.player_controller.abs_position - self.player_controller.rel_position
        )

        self.player_controller.display()

        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            self.player_controller.rel_position,
            5,
        )

        # TEST affichage de l'attaque
        if self.attaque:
            pygame.draw.rect(self.screen, "red", self.attaque_rect, 2)
