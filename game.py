"""Module pour la gestion du jeu."""

import time
from random import randint
from typing import Dict, List, Any, Tuple
import json

import pygame

from player import SoloPlayerController, HostController, GuestController
from moteur import Moteur
from map import Map
from camera_system import Camera
from inventory import Item, Inventaire, InventaireUI, InventaireManager
from ennemis import Ennemi
from particle_system_2 import spawn_local_particle


def serialize_ennemis(ennemis: Dict[int, Ennemi]) -> Dict[int, Any]:
    """Transforme une liste d'ennemis en dictionnaire pour réseau."""

    dic = {}
    for key, ennemi in ennemis.items():
        dic[key] = {
            "position": ennemi.position.tolist(),
            "velocity": ennemi.velocity.tolist(),
            "attack": ennemi.attack,
        }

    return dic


class Game:
    """Classe de gestion du jeu : joueur et carte."""

    def __init__(self, screen: pygame.Surface, manager):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.manager = manager
        self.playing_mode = None
        self.player_controller = None

        # -- Raccourcis --
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "attack": pygame.K_SPACE,
        }

        # -- Camera --
        width, height = self.screen.get_size()
        self.camera = Camera(width, height, 0, 0)

        # -- Particules --
        self.particles = pygame.sprite.Group()

        # -- Map --
        self.map = None
        self.map: Map
        self.nb_chunks = (8, 8)
        self.chunk_size = (32, 32)
        self.octaves = (8, 8)
        self.seed = 0

        # -- Moteur --
        self.moteur: Moteur | None = None

        # -- Ennemis --
        self.ennemis: Dict[int, Ennemi] | None = {}
        self.ennemis_id: List[int] | None = []

        # -- Réseau --
        self.address = "0.0.0.0"
        self.port = 8888

        # -- Inventaire -- : touche I pour ouvrir et fermer l'inventaire
        largeur, hauteur = self.screen.get_size()
        self.inv_joueur = Inventaire(rows=4, cols=8)
        self.ui_joueur = InventaireUI(
            self.screen,
            name="Sac du joueur",
            inv=self.inv_joueur,
            pos=((largeur - 486) // 2, hauteur - 293),
            image_path="Ressources/inv_assets/chest.png",
            slot_size=52,
            slot_margin=4,
            padding=21,
            title_height=11,
            visible=False,
            is_merchant=False,
        )
        self.drag_mgr = InventaireManager(self.screen, [self.ui_joueur])

        # Items de départ :
        self.inv_joueur.add_item(Item.create("Potion Rouge", 3))

    def _on_use(self, item: Item, slot, ui: InventaireUI):
        """Appelé au clic droit sur un consommable."""

        if item.item_type == "Consommable" and item.effect is not None:
            ui.inv.remove_item(slot[0], slot[1], 1)
            print(f"You've suck dry your potion : {item.effect:+d} PV")
            # self.player_controller.player.hp += item.effect par exemple

    def initialize(self):
        """Initialise le moteur, le controlleur à utiliser, les keybinds et la camera."""

        # -- Moteur --
        self.moteur = Moteur()

        # -- Client --
        if self.playing_mode == "guest":

            # -- Controlleur --
            self.player_controller = GuestController(
                self.screen, self.moteur, self.map, self.address, self.port
            )

            # -- Connexion host --
            while not self.player_controller.loaded:
                time.sleep(0.2)
            if self.player_controller.close:
                self.manager.state = self.manager.states["MENU_MULTI"]
            else:

                # -- Map --
                self.map = self.player_controller.map  # recupere la map de client
                self.moteur.map = (
                    self.map
                )  # donner à moteur pour Client-side prediction

                # -- Camera --
                self.player_controller.keybinds = self.keybinds
                self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
                self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
                self.player_controller.set_camera(self.camera)

        # -- Hote / Solo --
        else:

            # -- Map --
            self.map = Map(
                self.nb_chunks,
                self.chunk_size,
                self.octaves,
                (32, 32),
                r"Ressources\Pixel Art Top Down - Basic v1.2.3",
                self.screen,
                self.seed,
            )

            # -- Controlleur --
            if self.playing_mode == "solo":
                self.player_controller = SoloPlayerController(
                    self.screen, self.moteur, self.map, (4096, 4096)
                )
            elif self.playing_mode == "host":
                self.player_controller = HostController(
                    self.screen, self.moteur, self.map, (4000, 4096)
                )

            # -- Camera --
            self.player_controller.keybinds = self.keybinds
            self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
            self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
            self.player_controller.set_camera(self.camera)

            # -- Ennemis --
            ennemi = Ennemi(self.screen, (3500, 3500), 1, 32, self.map)
            self.ennemis_id.append(0)
            self.ennemis[0] = ennemi

    def event(self, events: List[pygame.event.Event]) -> bool:
        """Gére les entré de l'utilisateur."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:  # Si quitte
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.ui_joueur.visible:  # Ferme inventaire
                        self.ui_joueur.visible = False
                    else:  # Pause
                        self.manager.change_state("MENU_PAUSE")
                elif event.key == self.keybinds["attack"]:  # Attaque
                    if self.camera:
                        self.camera.start_shake(intensity=2, duration=10)
                    self.player_controller.attaque = True
                elif event.key == pygame.K_0:
                    self.save()

                elif event.key == pygame.K_F2:  # Debug F2
                    self.player_controller.toggle_hitbox()
                elif event.key == pygame.K_i:  # Ouvre inventaire
                    self.ui_joueur.visible = not self.ui_joueur.visible

            self.drag_mgr.handle_event(event, mouse_pos, on_use=self._on_use)

        self.player_controller.event(pygame.key.get_pressed())

    def update(self):
        """Met à jour le jeu."""
        dt = self.clock.tick(60) / 1000.0

        # -- Joueur --
        self.player_controller.update()
        self.camera.update(self.player_controller.hitbox)

        if self.player_controller.close:
            if isinstance(self.player_controller, HostController):
                if self.player_controller.serveur.is_serving():
                    self.player_controller.serveur.close()
            self.manager.state = self.manager.states["MENU_P"]

        # -- Ennemis --
        if isinstance(self.player_controller, SoloPlayerController):
            # -- Solo --
            for ennemi in self.ennemis.values():
                ennemi.update(self.player_controller.position)

        if isinstance(self.player_controller, HostController):
            # -- Host --
            for ennemi in self.ennemis.values():
                ennemi.update(
                    self.player_controller.position,
                    self.player_controller.guest.position,
                )
            self.player_controller.ennemis_data = serialize_ennemis(self.ennemis)

        elif isinstance(self.player_controller, GuestController):
            # -- Guest --
            for key, ennemi in self.player_controller.ennemis_data.items():
                if not key in self.ennemis_id:
                    self.ennemis[key] = Ennemi(
                        self.screen, ennemi["position"], -1, -1, None
                    )
                    self.ennemis[key].update_variables(ennemi)
                    self.ennemis_id.append(key)
                    self.ennemis[key].update_animation()
                else:
                    self.ennemis[key].update_variables(ennemi)
                    self.ennemis[key].update_animation()

        # -- Particules --
        if len(self.particles) < 50:  # Limite pour les performances

            # On récupère les coordonnées du monde actuellement à l'écran
            # On prend une marge de 100 pixels pour que les particules
            # n'apparaissent pas "magiquement" sur le bord
            margin = 100

            # Le top-left de la caméra est en négatif (ex: -4000),
            # on l'inverse pour avoir la position monde
            visible_world_x = -self.camera.camera.x
            visible_world_y = -self.camera.camera.y

            # On définit la zone de spawn
            spawn_x = randint(
                int(visible_world_x - margin),
                int(visible_world_x + self.screen.get_width() + margin),
            )
            spawn_y = randint(
                int(visible_world_y - margin),
                int(visible_world_y + self.screen.get_height() + margin),
            )
            spawn_local_particle(
                self.particles,
                sprite_path="Ressources/particles/dust.png",
                pos=(spawn_x, spawn_y),
                size=10,
                speed_range=(25, 45),
                chaos=0.2,
                shrink_range=(2, 15),
                rot=10,
            )
        self.particles.update(dt)

    def display(self):
        """Affiche tout les éléments."""
        # -- Reset --
        self.screen.fill((100, 100, 100))

        # -- Map --
        self.camera.display_map(self.map)

        # -- Joueur --
        self.player_controller.display()

        # -- Ennemis --
        for ennemi in self.ennemis.values():
            ennemi.display(self.camera)

        # -- Particules --
        for sprite in self.particles:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

        # -- Inventaire --
        self.drag_mgr.draw(pygame.mouse.get_pos())

    def save(self, file: str | None = "save.json"):

        if isinstance(self.player_controller, SoloPlayerController):
            data = {
                "playing_mode": "solo",
                "map": {
                    "seed": self.map.seed,
                    "nb_chunks": self.map.nb_chunks.tolist(),
                    "chunk_size": self.map.chunk_size_tile.tolist(),
                    "octaves": self.map.octaves,
                },
                "player": {
                    "position": list(self.player_controller.position),
                },
            }
        else:
            data = {
                "playing_mode": "multi",
                "map": {
                    "seed": self.map.seed,
                    "nb_chunks": self.map.nb_chunks,
                    "chunk_size": self.map.chunk_size_tile,
                    "octaves": self.map.octaves,
                },
                "host": {
                    "position": list(self.player_controller.position),
                },
                "guest": {
                    "position": list(self.player_controller.guest.position),
                },
            }

        with open(file, "w") as f:

            raw = json.dumps(data, indent="\t")
            f.write(raw)

    def load_save(self, file: str):

        with open(file, "r") as f:

            raw = f.read()
            data = json.loads(raw)

        self.nb_chunks = data["map"]["nb_chunks"]
        self.chunk_size = data["map"]["chunk_size"]
        self.octaves = data["map"]["octaves"]
        self.seed = data["map"]["seed"]
        self.playing_mode = data["playing_mode"]
