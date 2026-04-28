"""Module pour la gestion du jeu."""

import pygame
import time
import datetime
import json
from random import randint
from typing import Dict, List, Any, Tuple, TYPE_CHECKING
import os

from player import SoloPlayerController, HostController, GuestController
from network import HostNetwork, GuestNetwork
from moteur import Moteur
from map import Map
from camera_system import Camera
from hud import HUD
from inventory import Item, Inventaire, InventaireUI, InventaireManager
from ennemis import Ennemi
from particule import spawn_local_particle

if TYPE_CHECKING:
    from main import Manager

INVENTORY_ASSET_DIRECTORY = r"Ressources\InventoryAsset"
RESPAWN_PV = 2
SPECTATE_DURATION = 15
RESPAWN_OFFSET = 50  # l'autre joueur respawn 50 pixel a droite de l'autre


def serialize_ennemis(ennemis: Dict[int, Ennemi]) -> Dict[int, Any]:
    """Transforme une liste d'ennemis en dictionnaire pour réseau."""

    dic = {}
    for key, ennemi in ennemis.items():
        dic[key] = {
            "position": ennemi.position.tolist(),
            "velocity": ennemi.velocity.tolist(),
            "attack": ennemi.attack,
            "death_time": ennemi.death_time,
            "PV": ennemi.pv,
            "dying": ennemi.dying,
        }

    return dic


class Game:
    """Classe de gestion du jeu : joueur et carte."""

    def __init__(self, screen: pygame.Surface, manager: "Manager"):
        self.clock = pygame.time.Clock()
        self.screen = screen
        self.manager = manager
        self.playing_mode: str = None
        self.player_controller: (
            SoloPlayerController | HostController | GuestController | None
        ) = None
        self.network: HostNetwork | GuestNetwork | None = None
        self.game_name = "tt"

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

        # -- HUD --
        self.hud = HUD(self.screen, self.camera)

        # -- Particules --
        self.particles = pygame.sprite.Group()

        # -- F2 --
        self.show_hitbox = False

        # -- Map --
        self.map: Map = None
        self.nb_chunks = (8, 8)
        self.chunk_size = (32, 32)
        self.octaves = (8, 8)
        self.seed = 0

        # -- Moteur --
        self.moteur: Moteur = None

        # -- Ennemis --
        self.paths = [[]]
        self.ennemis: Dict[int, Ennemi] = {}
        self.ennemis_id: List[int] = []

        # -- Réseau --
        self.address = "0.0.0.0"
        self.port = 8888

        # -- Mort / Spectateur --
        self.spectate_start: float | None = None

        # -- Inventaire -- : touche I pour ouvrir et fermer l'inventaire
        largeur, hauteur = self.screen.get_size()
        self.inv_joueur = Inventaire(rows=4, cols=8)
        self.ui_joueur = InventaireUI(
            self.screen,
            name="Sac du joueur",
            inv=self.inv_joueur,
            pos=((largeur - 486) // 2, hauteur - 293),
            is_merchant=False,
            is_visible=False,
        )
        self.drag_mgr = InventaireManager(self.screen, [self.ui_joueur])

        # Items de départ :
        self.inv_joueur.add_item(Item.create("Potion Rouge", 3))

    def _on_use(self, item: Item, slot: Tuple[int, int], ui: InventaireUI):
        """Inventaire : Appelé au clic droit sur un consommable."""

        if item.item_type == "Consommable" and item.effect is not None:
            ui.inv.remove_item(slot[0], slot[1], 1)
            print(f"You've suck dry your potion : {item.effect:+d} PV")
            # self.player_controller.pv += item.effect par exemple

    def initialize(self):
        """Initialise le moteur, la map, le contrôleur et le réseau."""

        # -- Moteur --
        self.moteur = Moteur()

        # -- Client --
        if self.playing_mode == "guest":

            # Réseau : connexion à l'hôte
            self.network = GuestNetwork(self.address, self.port)
            self.network.start()

            while not self.network.is_loaded():
                time.sleep(0.2)

            if self.network.is_closed():
                self.manager.change_state("MENU_MULTI")
                return

            # Récupération de la map envoyée par l'hôte
            map_data = self.network.get_map_data()
            self.map = Map(
                map_data["nb_chunks"],
                map_data["chunk_size"],
                map_data["octaves"],
                self.screen,
                map_data["seed"],
            )

            # Récupération de la position initiale du guest
            initial = self.network.get_initial_state()
            guest_start = tuple(initial.get("guest", {}).get("position", (0, 0)))
            host_start = tuple(initial.get("host", {}).get("position", (0, 0)))

            self.player_controller = GuestController(
                self.screen, self.camera, self.moteur, guest_start
            )

            # Position initiale du host répliqué
            self.player_controller.host.position.update(host_start)
            self.player_controller.host.hitbox.center = host_start
            self.player_controller.host.hitbox_damage.midbottom = host_start

        # ── Solo / Host ────────────────────────────────────────────────
        else:

            # -- Map --
            self.map = Map(
                self.nb_chunks,
                self.chunk_size,
                self.octaves,
                self.screen,
                self.seed,
            )

            # -- Controlleur --
            if self.playing_mode == "solo":
                self.player_controller = SoloPlayerController(
                    self.screen, self.camera, self.moteur, (4096, 4096)
                )

            elif self.playing_mode == "host":
                self.player_controller = HostController(
                    self.screen, self.camera, self.moteur, (4000, 4096)
                )

                # Réseau : construction de l'état initial avec la map
                initial_state = self.get_to_send_data_host(include_map=True)
                self.network = HostNetwork(self.port)
                self.network.start(initial_state)

            # -- Ennemis (pour test) --
            ennemi = Ennemi(
                self.screen, (3500, 3500), 1, 32, self.map, self.camera, self.moteur
            )
            self.ennemis_id.append(0)
            self.ennemis[0] = ennemi

        # -- Keybinds --
        self.player_controller.keybinds = self.keybinds

        # -- Finition de la caméra grâce à la map. --
        self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
        self.camera.map_height = self.map.size[1] * self.map.tile_size[1]

        # -- HUD --
        self.hud.player_controller = self.player_controller
        self.hud.max_pv = self.player_controller.max_pv
        self.hud.pv = self.player_controller.pv

        # -- Map -- Ne pas oublier de passer la map au moteur !
        self.moteur.map = self.map

    def get_camera_target(self) -> pygame.Rect:
        """Renvoie la hitbox cible pour la caméra."""
        if self.player_controller.is_dead:
            if isinstance(self.player_controller, HostController):
                return self.player_controller.guest.hitbox
            if isinstance(self.player_controller, GuestController):
                return self.player_controller.host.hitbox
        return self.player_controller.hitbox

    def get_position_target(self) -> pygame.Rect:
        """Renvoie la position cible pour la map."""
        if self.player_controller.is_dead:
            if isinstance(self.player_controller, HostController):
                return self.player_controller.guest.position
            if isinstance(self.player_controller, GuestController):
                return self.player_controller.host.position
        return self.player_controller.position

    def _handle_death(self):
        """Gère la mort des joueurs : spectateur 30 s puis respawn, ou écran de mort."""
        pc = self.player_controller

        if isinstance(pc, SoloPlayerController):
            if pc.is_dead:
                self.manager.change_state("DEATH_SCREEN")

        elif isinstance(pc, HostController):

            if pc.is_dead and pc.guest.is_dead:
                self.spectate_start = None
                self.manager.change_state("DEATH_SCREEN")

            elif pc.is_dead or pc.guest.is_dead:
                if self.spectate_start is None:
                    self.spectate_start = time.time()
                elif time.time() - self.spectate_start >= SPECTATE_DURATION:
                    if pc.is_dead:
                        pc.respawn(
                            (pc.guest.position.x + RESPAWN_OFFSET, pc.guest.position.y),
                            RESPAWN_PV,
                        )
                    else:
                        pc.guest.respawn(
                            (pc.position.x + RESPAWN_OFFSET, pc.position.y), RESPAWN_PV
                        )
                    self.spectate_start = None

        elif isinstance(pc, GuestController):
            if pc.is_dead and pc.host.is_dead:
                self.manager.change_state("DEATH_SCREEN")

    # Réseau

    def get_to_send_data_host(self, include_map: bool = False) -> Dict[str, Any]:
        """Construit le dictionnaire d'état envoyé par l'hôte au guest."""
        hc = self.player_controller  # hc pour HostController

        dic: Dict[str, Any] = {
            "host": {
                "position": list(hc.position),
                "moving_intent": hc.moving_intent,
                "direction": hc.direction,
                "attaque": hc.animation.current_state == "attack",
                "is_dead": hc.is_dead,
            },
            "guest": {
                "position": list(hc.guest.position),
                "pv": hc.guest.pv,
                "is_dead": hc.guest.is_dead,
            },
            "ennemis": serialize_ennemis(self.ennemis),
            "close": False,
        }

        if include_map:
            dic["map"] = {
                "nb_chunks": self.map.nb_chunks.tolist(),
                "chunk_size": self.map.chunk_size_tile.tolist(),
                "octaves": self.map.octaves,
                "seed": self.map.seed,
            }

        return dic

    def get_to_send_data_guest(self) -> Dict[str, Any]:
        """Construit le dictionnaire d'état envoyé par le guest à l'hôte."""
        gc = self.player_controller  # gc pour GuestController

        return {
            "guest": {
                "velocity": list(gc.velocity),
                "moving_intent": gc.moving_intent,
                "attaque": gc.animation.current_state == "attack",
            },
            "close": False,
        }

    def update_variables_host(self, data: Dict[str, Any]):
        """Applique les données reçues du guest sur le HostController."""
        if not data:
            return
        hc = self.player_controller  # hc pour HostController

        if "guest" in data:
            hc.guest.velocity = self.moteur.verif_velocity(data["guest"]["velocity"])
            hc.guest.moving_intent = data["guest"]["moving_intent"]
            hc.guest.attaque = data["guest"]["attaque"]

    def update_variables_guest(self, data: Dict[str, Any]):
        """Applique les données reçues de l'hôte sur le GuestController."""
        if not data:
            return
        gc = self.player_controller  # gc pour GuestController

        if "guest" in data:
            gc.target_pos = pygame.Vector2(data["guest"]["position"])
            gc.pv = data["guest"]["pv"]
            gc.is_dead = data["guest"]["is_dead"]

        if "host" in data:
            gc.host_target_pos = pygame.Vector2(data["host"]["position"])
            gc.host.moving_intent = data["host"]["moving_intent"]
            gc.host.direction = data["host"]["direction"]
            gc.host.attaque = data["host"]["attaque"]
            gc.host.is_dead = data["host"]["is_dead"]

        # Ennemis
        self.update_ennemis_guest(data["ennemis"])

    def _send_close_and_disconnect(self):
        """
        Permet au guest l'envoie d'un paquet {"close": True} à l'host pour signaler
        une déconnexion propre, évitant que l'host attende le timeout de 2 secondes.
        """
        if self.network is not None:
            self.network.request_close()

    def close_network(self):
        """
        Coupe proprement la connexion réseau et libère la référence."""
        if self.network is not None:
            try:
                self.network.close()
            except Exception:
                pass
            finally:
                self.network = None

    # Game basic

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
                elif (
                    event.key == self.keybinds["attack"]
                    and not self.player_controller.is_dead
                ):
                    self.player_controller.attaque = True
                elif event.key == pygame.K_0:
                    self.save()
                elif event.key == pygame.K_F2:  # Debug F2
                    self.show_hitbox = not self.show_hitbox
                elif event.key == pygame.K_i:  # Ouvre inventaire
                    self.ui_joueur.is_visible = not self.ui_joueur.is_visible

                # TEMPORAIRE !
                elif event.key == pygame.K_h:
                    self.player_controller.update_pv(-1)

            self.drag_mgr.handle_event(event, mouse_pos, on_use=self._on_use)

        self.player_controller.event(pygame.key.get_pressed())

    def update(self):
        """Met à jour le jeu."""

        # -- Réseau --
        if self.network is not None:

            if isinstance(self.player_controller, HostController):

                self.update_variables_host(
                    self.network.update(self.get_to_send_data_host())
                )

            elif isinstance(self.player_controller, GuestController):
                self.update_variables_guest(
                    self.network.update(self.get_to_send_data_guest())
                )

            # Host : si le guest s'est déconnecté on remet en écoute
            if (
                isinstance(self.network, HostNetwork)
                and self.network.is_guest_disconnected()
            ):
                print("[Host] Guest déconnecté — remise en écoute")
                self.network.restart_listening()

            # Si l'hôte quitte alors fermeture totale
            elif self.network.is_closed():
                self.close_network()
                self.reset()
                self.manager.change_state("MENU_P")
                return

        # -- Map --
        self.map.load_chunks(self.get_position_target())

        # -- Joueur --
        self.player_controller.update(self.ennemis)
        self.camera.update(self.get_camera_target())

        # -- Ennemis --
        self.paths = [[]]
        if isinstance(self.player_controller, SoloPlayerController):
            self.update_ennemis_solo()
        elif isinstance(self.player_controller, HostController):
            self.update_ennemis_host()
        # Guest : gerer dans update_ennemis_guest() et appeler via update_variables_guest

        # -- Particules --
        self.update_particles()

        # -- HUD --
        self.hud.update(self.manager.clock.get_time() / 1000)

        # -- Mort / Spectateur --
        self._handle_death()

    def update_ennemis_solo(self):
        del_key = []

        for key, ennemi in self.ennemis.items():
            self.paths.append(ennemi.update(self.player_controller))

            if ennemi.attaque_rect is not None:
                self.moteur.apply_attack(ennemi.attaque_rect, self.player_controller)

            self.spawn_death_particles(ennemi)

            if time.time() > ennemi.death_time:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]

        if self.player_controller.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.moteur.apply_attack(self.player_controller.attaque_rect, ennemi)

    def update_ennemis_host(self):
        del_key = []

        for key, ennemi in self.ennemis.items():
            self.paths.append(
                ennemi.update(self.player_controller, self.player_controller.guest)
            )

            if ennemi.attaque_rect is not None:
                if not self.player_controller.is_dead:
                    self.moteur.apply_attack(
                        ennemi.attaque_rect, self.player_controller
                    )
                if not self.player_controller.guest.is_dead:
                    self.moteur.apply_attack(
                        ennemi.attaque_rect, self.player_controller.guest
                    )

            self.spawn_death_particles(ennemi)

            if time.time() > ennemi.death_time:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]

        if self.player_controller.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.moteur.apply_attack(self.player_controller.attaque_rect, ennemi)

        if self.player_controller.guest.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.moteur.apply_attack(
                    self.player_controller.guest.attaque_rect, ennemi
                )

    def update_ennemis_guest(self, ennemis_data: Dict[str, Any]):
        """Côté guest : les ennemis sont pilotés par les données réseau."""
        del_key = []

        for key, ennemi_data in ennemis_data.items():

            if key not in self.ennemis_id:
                if ennemi_data["dying"]:
                    continue
                self.ennemis[key] = Ennemi(
                    self.screen,
                    ennemi_data["position"],
                    -1,
                    -1,
                    None,
                    self.camera,
                    None,
                )
                self.ennemis_id.append(key)

            self.ennemis[key].update_variables(ennemi_data)
            self.ennemis[key].update_animation()

            self.spawn_death_particles(self.ennemis[key])

            if time.time() > ennemi_data["death_time"]:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]
            if key in self.ennemis_id:
                self.ennemis_id.remove(key)

    def spawn_death_particles(self, ennemi: Ennemi):
        """Fait spawn des particules de mort si ennemi est mort"""
        if ennemi.dying and not ennemi.particles_spawned:
            ennemi.particles_spawned = True
            for _ in range(50):
                spawn_local_particle(
                    self.particles,
                    ennemi.position.tolist(),
                    r"Ressources\Particles\dust.png",
                    speed_range=(50, 150),
                    shrink_range=(20, 60),
                )

    def update_particles(self):
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
                sprite_path="Ressources/Particles/dust.png",
                pos=(spawn_x, spawn_y),
                size=10,
                speed_range=(25, 45),
                chaos=0.2,
                shrink_range=(2, 15),
                rot=10,
            )
        self.particles.update(self.manager.clock.get_time() / 1000)

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
            ennemi.display()

        # -- Particules --
        for sprite in self.particles:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

        # -- F2 : TOUTES les hitboxes --
        if self.show_hitbox:
            self.draw_debug_hitboxes()

        # -- Inventaire --
        self.drag_mgr.draw(pygame.mouse.get_pos())

        # -- HUD --
        self.hud.draw()

    def draw_debug_hitboxes(self):
        """
        Affiche l'hitbox des joueurs et des ennemies ainsi que leur hitbox
        d'attaque et les obstacles proches de toutes les entités vivantes.
        """
        entities = [self.player_controller]

        # En multi on rajoute l'autre joueur
        if isinstance(self.player_controller, HostController):
            entities.append(self.player_controller.guest)
        elif isinstance(self.player_controller, GuestController):
            entities.append(self.player_controller.host)

        # Affichage des hitbox et des zones d'attaque
        for entity in entities:
            pygame.draw.rect(self.screen, "green", self.camera.apply(entity.hitbox), 2)
            pygame.draw.rect(
                self.screen, "green", self.camera.apply(entity.hitbox_damage), 2
            )

            if entity.attaque_rect:
                pygame.draw.rect(
                    self.screen, "yellow", self.camera.apply(entity.attaque_rect), 2
                )

        all_hitboxes = [e.hitbox for e in entities]

        # Affichage des hitbox ennemie
        for ennemi in self.ennemis.values():
            if ennemi.hitbox:
                pygame.draw.rect(
                    self.screen, "orange", self.camera.apply(ennemi.hitbox), 2
                )
                pygame.draw.rect(
                    self.screen, "orange", self.camera.apply(ennemi.hitbox_damage), 2
                )
                all_hitboxes.append(ennemi.hitbox)
            if ennemi.attaque_rect:
                pygame.draw.rect(
                    self.screen, "yellow", self.camera.apply(ennemi.attaque_rect), 2
                )

        # Affichage des obstacles du jeu
        for hitbox in all_hitboxes:
            for obs in self.moteur.get_nearby_obstacles(hitbox):
                pygame.draw.rect(self.screen, "red", self.camera.apply(obs), 2)

        # Affichage du chemin jusqu'a l'ennemie
        for path in self.paths:
            if path != None:
                for i in range(len(path) - 1):
                    # print(self.path[i], self.path[i + 1])
                    pygame.draw.line(
                        self.screen,
                        (255, 0, 128),
                        (
                            path[i][0] * 32
                            + 16
                            + self.camera.camera.x
                            + self.camera.offset_x,
                            path[i][1] * 32
                            + 16
                            + self.camera.camera.y
                            + self.camera.offset_y,
                        ),
                        (
                            path[i + 1][0] * 32
                            + 16
                            + self.camera.camera.x
                            + self.camera.offset_x,
                            path[i + 1][1] * 32
                            + 16
                            + self.camera.camera.y
                            + self.camera.offset_y,
                        ),
                    )

    # Sauvegarde et reset

    def reset(self):
        self.playing_mode = None
        self.player_controller = None
        self.game_name = "tt"

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

        # -- HUD --
        self.hud = HUD(self.screen, self.camera)

        # -- Particules --
        self.particles = pygame.sprite.Group()

        # -- F2 --
        self.show_hitbox = False

        # -- Map --
        self.map: Map = None
        self.nb_chunks = (8, 8)
        self.chunk_size = (32, 32)
        self.octaves = (8, 8)
        self.seed = 0

        # -- Moteur --
        self.moteur: Moteur = None

        # -- Ennemis --
        self.paths = [[]]
        self.ennemis: Dict[int, Ennemi] = {}
        self.ennemis_id: List[int] = []

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
            image_path=os.path.join(INVENTORY_ASSET_DIRECTORY, "chest.png"),
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

    def save(self, file: str | None = "save.json"):

        if isinstance(self.player_controller, SoloPlayerController):
            data = {
                "last_save": str(datetime.datetime.today()),
                "game_name": self.game_name,
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
                    "nb_chunks": self.map.nb_chunks.tolist(),
                    "chunk_size": self.map.chunk_size_tile.tolist(),
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

            f.write(json.dumps(data, indent="\t"))

    def load_save(self, file: str):

        with open(file, "r") as f:

            data = json.loads(f.read())

        self.game_name = data["game_name"]
        self.nb_chunks = data["map"]["nb_chunks"]
        self.chunk_size = data["map"]["chunk_size"]
        self.octaves = data["map"]["octaves"]
        self.seed = data["map"]["seed"]
        self.playing_mode = data["playing_mode"]
