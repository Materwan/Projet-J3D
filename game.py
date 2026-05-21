"""Module pour la gestion du jeu."""

import time
import datetime
import json
from random import randint
from typing import Dict, List, Any, Tuple, TYPE_CHECKING
import os
import pprint

import pygame

from player import (
    PlayerControllerBase,
    SoloPlayerController,
    HostController,
    GuestController,
)
from utils import resource_path, DefaultManager
from network import HostNetwork, GuestNetwork
from moteur import Moteur
from map import MapManager, STR_TYPE
from camera_system import Camera
from hud import HUD
from inventory import Item, Inventaire, InventaireUI, InventaireManager
from ennemis import Ennemi
from particule import spawn_local_particle
from pnj import PNJ, PNJManager

if TYPE_CHECKING:
    from main import Manager

INVENTORY_ASSET_DIRECTORY = resource_path(r"Ressources\InventoryAsset")
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


class Game(DefaultManager):
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
        self.print_send_data: bool = False
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
        self.map: MapManager = None
        self.nb_chunks = (8, 8)
        self.chunk_size = (32, 32)
        self.octaves = (8, 8)
        self.seed = 1545

        # -- Moteur --
        self.moteur: Moteur = None

        # -- Ennemis --
        self.paths = [[]]
        self.ennemis: Dict[int, Ennemi] = {}

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
            pos=((largeur - 480) // 2, hauteur - 290),
            is_merchant=False,
            is_visible=False,
        )
        self.drag_mgr = InventaireManager(self.screen, [self.ui_joueur])

        # Items de départ :
        self.inv_joueur.add_item(Item.create("Potion Rouge", 3))

        # PNJ :
        self.pnj_manager: PNJManager = PNJManager(self.screen, self.camera)
        self.money: int = 500

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen
        if self.map:
            self.map.set_screen(screen)
        if self.player_controller:
            self.player_controller.set_screen(screen)
        self.camera.width, self.camera.height = screen.get_size()
        self.hud.screen = screen
        self.ui_joueur.screen = screen
        self.drag_mgr.screen = screen
        self.pnj_manager.set_screen(screen)

    def _on_use(self, item: Item, slot: Tuple[int, int], ui: InventaireUI):
        """Inventaire : Appelé au clic droit sur un consommable."""

        if item.item_type == "Consommable" and item.effect is not None:
            if self.player_controller.pv >= self.player_controller.max_pv:
                print("You are already full health !")
            else:
                ui.inv.remove_item(slot[0], slot[1], 1)
                print("You've suck dry your potion : +1 HP")
                self.player_controller.pv += 1

    def initialize(self):
        """Initialise le moteur, la map, le contrôleur et le réseau.
        Il est maitenant appelé dans un thread depuis GameLoadingScreen !"""

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
            self.map = MapManager.create_map(self.screen, self, self.camera, map_data)

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

            self.pnj_manager = self.map.get_pnjs()

        # ── Solo / Host ────────────────────────────────────────────────
        else:

            # -- Map --
            self.map = MapManager.generate_maps(
                self.screen,
                self,
                self.camera,
                7,
                self.nb_chunks,
                self.chunk_size,
                self.octaves,
                self.seed,
            )

            # -- Controlleur --
            if self.playing_mode == "solo":
                self.player_controller = SoloPlayerController(
                    self.screen, self.camera, self.moteur, self.map.start_position
                )

            elif self.playing_mode == "host":
                self.player_controller = HostController(
                    self.screen, self.camera, self.moteur, self.map.start_position
                )
                self.player_controller.guest.position.x += 20

                # Réseau : construction de l'état initial avec la map
                initial_state = self.get_to_send_data_host(include_map=True)
                self.network = HostNetwork(self.port)
                self.network.start(initial_state)

            # -- Ennemis (pour test) --
            ennemi = Ennemi(
                self.screen,
                (3500, 3500),
                1,
                32,
                self.map["principal_map"],
                self.camera,
                self.moteur,
            )
            self.map["principal_map"].ennemis[0] = ennemi

            self.pnj_manager = self.map.get_pnjs()

        # -- Keybinds --
        self.player_controller.keybinds = self.keybinds

        # -- Taille camera --
        self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
        self.camera.map_height = self.map.size[1] * self.map.tile_size[1]

        # -- HUD --
        self.hud.player_controller = self.player_controller
        self.hud.max_pv = self.player_controller.max_pv
        self.hud.pv = self.player_controller.pv

        # -- Map -- Ne pas oublier de passer la map au moteur !
        self.moteur.map = self.map
        self.player_controller.current_map = self.map.map

    def get_camera_target(self) -> pygame.Rect:
        """Renvoie la hitbox cible pour la caméra.

        Si le joueur local est mort, on suit le partenaire — mais seulement
        s'il est lui-même vivant et que sa hitbox est valide. Sinon on
        renvoie la dernière hitbox connue du joueur local pour éviter un crash.
        """
        pc = self.player_controller

        if pc.is_dead:
            if isinstance(pc, HostController):
                if not pc.guest.is_dead and pc.guest.hitbox:
                    return pc.guest.hitbox
            elif isinstance(pc, GuestController):
                if not pc.host.is_dead and pc.host.hitbox:
                    return pc.host.hitbox

        # Fallback : hitbox du joueur local (toujours valide, même après mort)
        return pc.hitbox

    def get_position_target(self) -> pygame.Vector2:
        """Renvoie la position cible pour la map.

        Même logique de fallback que get_camera_target.
        """
        pc = self.player_controller

        if pc.is_dead:
            if isinstance(pc, HostController):
                if not pc.guest.is_dead:
                    return pc.guest.position
            elif isinstance(pc, GuestController):
                if not pc.host.is_dead:
                    return pc.host.position

        return pc.position

    def _handle_death(self):
        """Gère la mort des joueurs : spectateur SPECTATE_DURATION s puis respawn,
        ou écran de mort si les deux sont morts simultanément."""
        pc = self.player_controller

        # -- Solo --
        if isinstance(pc, SoloPlayerController):
            if pc.is_dead:
                self.manager.change_state("DEATH_SCREEN")

        # -- Host --
        elif isinstance(pc, HostController):

            # Les deux sont morts → écran de mort
            if pc.is_dead and pc.guest.is_dead:
                self.spectate_start = None
                self.manager.change_state("DEATH_SCREEN")

            # Un seul est mort → mode spectateur puis respawn
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

            else:
                # Plus personne n'est mort : on reset le timer au cas où
                self.spectate_start = None

        # -- Guest --
        elif isinstance(pc, GuestController):

            if pc.is_dead and pc.host.is_dead:
                self.spectate_start = None
                self.manager.change_state("DEATH_SCREEN")

            elif pc.is_dead or pc.host.is_dead:
                if self.spectate_start is None:
                    if pc.is_dead and pc.host.current_map is not None:
                        if pc.host.current_map is not None:
                            self.map.change_map(pc.host.current_map)
                    self.spectate_start = time.time()

                elif time.time() - self.spectate_start >= SPECTATE_DURATION:
                    if pc.is_dead:
                        respawn_pos = (
                            pc.host.position.x + RESPAWN_OFFSET,
                            pc.host.position.y,
                        )
                        pc.respawn(respawn_pos, RESPAWN_PV)

                        if pc.host.current_map is not None:
                            if pc.host.current_map is not None:
                                self.map.change_map(pc.host.current_map)
                    else:
                        pc.host.respawn(
                            (pc.position.x + RESPAWN_OFFSET, pc.position.y), RESPAWN_PV
                        )
                    self.spectate_start = None

            else:
                self.spectate_start = None

    # Réseau

    def get_to_send_data_host(self, include_map: bool = False) -> Dict[str, Any]:
        """Construit le dictionnaire d'état envoyé par l'hôte au guest."""
        hc = self.player_controller  # hc pour HostController

        dic: Dict[str, Any] = {
            "host": {
                "map": self.map.map_name,
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
            "map": {
                "name": self.map.map_name,
            },
            "ennemis": (
                serialize_ennemis(
                    self.player_controller.guest.current_map.get_ennemis()
                )
                if self.player_controller.guest.current_map
                else {}
            ),
            "close": False,
        }

        if include_map:
            dic["map"] = self.map._get_to_send_data()

        return dic

    def get_to_send_data_guest(self) -> Dict[str, Any]:
        """Construit le dictionnaire d'état envoyé par le guest à l'hôte."""
        gc = self.player_controller  # gc pour GuestController

        return {
            "guest": {
                "map": self.map.map_name,
                "velocity": list(gc.velocity),
                "moving_intent": gc.moving_intent,
                "attaque": gc.animation.current_state == "attack",
            },
            "map": {
                "name": self.map.map_name,
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
            if hc.guest.current_map != self.map[data["map"]["name"]]:
                self._change_map(hc.guest, data["map"]["name"], move_camera=False)
                if self.player_controller.hitbox.colliderect(
                    self.player_controller.guest.hitbox
                ):
                    new_pos = self.player_controller.guest.position
                    new_pos[0] += 50
                    self.player_controller.guest.position.update(new_pos)
                    self.player_controller.guest.hitbox.center = new_pos

    def update_variables_guest(self, data: Dict[str, Any]):
        """Applique les données reçues de l'hôte sur le GuestController."""
        if not data:
            return
        gc = self.player_controller  # gc pour GuestController

        if "guest" in data:
            new_is_dead = data["guest"]["is_dead"]
            gc.pv = data["guest"]["pv"]

            if gc.is_dead and not new_is_dead:
                gc.position.update(data["guest"]["position"])
                gc.hitbox.center = gc.position
                gc.hitbox_damage.midbottom = gc.position
                gc.target_pos = None
                self.spectate_start = None  # reset du timer spectateur
            elif not new_is_dead:
                gc.target_pos = pygame.Vector2(data["guest"]["position"])

            gc.is_dead = new_is_dead

        if "host" in data:
            host_map_name = data.get("map", {}).get("name")

            gc.host.current_map = self.map.maps.get(host_map_name)

            new_host_is_dead = data["host"]["is_dead"]
            gc.host.moving_intent = data["host"]["moving_intent"]
            gc.host.direction = data["host"]["direction"]
            gc.host.attaque = data["host"]["attaque"]

            if gc.host.is_dead and not new_host_is_dead:
                gc.host.position.update(data["host"]["position"])
                gc.host.hitbox.center = gc.host.position
                gc.host.hitbox_damage.midbottom = gc.host.position
                gc.host_target_pos = None
                self.spectate_start = None  # reset du timer spectateur
            elif not new_host_is_dead:
                gc.host_target_pos = pygame.Vector2(data["host"]["position"])

            gc.host.is_dead = new_host_is_dead

        # Ennemis
        for key, ennemi_data in data.get("ennemis", {}).items():

            if key not in self.ennemis.keys():
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

            self.ennemis[key].update_variables(ennemi_data)
            self.ennemis[key].update_animation()

            self.spawn_death_particles(self.ennemis[key])

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

    def close_game(self):
        self.close_network()
        if self.map:
            self.map.close_map()

    # Game basic

    def event(self, events: List[pygame.event.Event]) -> bool:
        """Gére les entré de l'utilisateur."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:  # Si quitte
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.ui_joueur.is_visible:  # Ferme inventaire
                        self.ui_joueur.is_visible = False
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
                elif event.key == pygame.K_F3:  # Debug F2
                    self.print_send_data = not self.print_send_data
                elif event.key == pygame.K_i:  # Ouvre inventaire
                    self.ui_joueur.is_visible = not self.ui_joueur.is_visible

            if not self.pnj_manager.handle_event(event, mouse_pos):
                self.drag_mgr.handle_event(event, mouse_pos, on_use=self._on_use)

        self.player_controller.velocity.update(0, 0)
        if self.pnj_manager.mode is None:
            self.player_controller.event(pygame.key.get_pressed())

    def update(self):
        """Met à jour le jeu."""

        # -- Réseau --
        if self.network is not None:

            if isinstance(self.player_controller, HostController):

                self.update_variables_host(
                    self.network.update(self.get_to_send_data_host())
                )

                if self.print_send_data:
                    print("Sended :")
                    pprint.pp(self.get_to_send_data_host())
                    print("Last recieved :")
                    pprint.pp(self.network._incoming_back)
                    self.print_send_data = False

            elif isinstance(self.player_controller, GuestController):

                self.update_variables_guest(
                    self.network.update(self.get_to_send_data_guest())
                )
                if self.print_send_data:
                    print("Sended :")
                    pprint.pp(self.get_to_send_data_guest())
                    print("Last recieved :")
                    pprint.pp(self.network._incoming_back)
                    self.print_send_data = False

            # Host : si le guest s'est déconnecté on remet en écoute
            if (
                isinstance(self.network, HostNetwork)
                and self.network.is_guest_disconnected()
            ):
                print("[Host] Guest déconnecté — remise en écoute")
                self.network.restart_listening()

            # Si l'hôte quitte alors fermeture totale
            elif self.network.is_closed():
                self.close_game()
                self.reset()
                self.manager.change_state("MENU_P")
                return

        # -- Map --
        self.map.update(self.get_position_target())

        # -- Joueur --
        self.player_controller.update(self.ennemis)
        self.camera.update(self.get_camera_target())

        # -- Ennemis --
        self.paths = self.map.update_ennemis()
        # Guest : gerer dans update_ennemis_guest() et appeler via update_variables_guest

        # PNJ
        self.pnj_manager.set_inventaire(self.inv_joueur, self.money)
        self.pnj_manager.update(
            (
                int(self.player_controller.position.x),
                int(self.player_controller.position.y),
            ),
            self.manager.clock.get_time(),
        )
        self.money = self.pnj_manager.money

        # -- Particules --
        self.update_particles()

        # -- HUD --
        self.hud.update(self.manager.clock.get_time() / 1000)

        # -- Mort / Spectateur --
        self._handle_death()

    def _change_map(
        self,
        player_controller: PlayerControllerBase,
        new_map: str,
        move_camera: bool = True,
    ):
        player_controller.current_map = self.map[new_map]
        player_controller.position.update(player_controller.current_map.start_position)
        player_controller.hitbox.center = player_controller.current_map.start_position
        if player_controller == self.player_controller:
            self.ennemis = self.map.get_ennemis()
            self.pnj_manager = self.map.get_pnjs()
            self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
            self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
        elif isinstance(self.player_controller, HostController):
            pass  # L'hôte garde self.ennemis de sa propre map, rien à faire.
        if move_camera:
            self.camera.set_position(player_controller.current_map.start_position)

    def _boss_fight_start(self):
        print("start boss fight")
        # self.manager.change_state("CARD")

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
        self.screen.fill((32, 35, 32))

        # -- Map --
        self.map.display(self.camera)

        # -- Joueur --
        self.player_controller.display()

        # -- Ennemis --
        for ennemi in self.map.ennemis.values():
            ennemi.display()

        """ # -- Particules --
        for sprite in self.particles:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))"""

        # -- PNJ --
        self.pnj_manager.draw_pnj()

        # -- F2 : TOUTES les hitboxes --
        if self.show_hitbox:
            self.draw_debug_hitboxes()

        # -- Inventaire -- seulement si pas d'UI PNJ
        if self.pnj_manager.mode is None:
            self.drag_mgr.draw(pygame.mouse.get_pos())

        # -- PNJ UI --
        self.pnj_manager.draw_ui(pygame.mouse.get_pos())

        # -- HUD --
        self.hud.draw()

    def draw_debug_hitboxes(self):
        """
        Affiche l'hitbox des joueurs et des ennemies ainsi que leur hitbox
        d'attaque et les obstacles proches de toutes les entités vivantes.
        """
        pc = self.player_controller
        entities = [pc]

        # En multi on rajoute l'autre joueur
        if isinstance(pc, HostController) and pc.current_map == pc.guest.current_map:
            entities.append(pc.guest)
        elif isinstance(pc, GuestController) and pc.current_map == pc.host.current_map:
            entities.append(pc.host)

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

        # Affichage des obstacles du jeu et tuiles d'action
        for hitbox in all_hitboxes:
            for obs in self.map.get_nearby_obstacles(hitbox):
                pygame.draw.rect(self.screen, "red", self.camera.apply(obs), 2)

            for obs in self.map.get_nearby_action_tiles(hitbox):
                pygame.draw.rect(self.screen, "blue", self.camera.apply(obs), 2)

        # Affichage du chemin jusqu'a l'ennemie
        for path in self.paths:
            if path is None:
                path = []
            for i in range(len(path) - 1):
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

    def _debug(self, font: pygame.font.Font):
        player = self.player_controller.position
        hitbox = self.player_controller.hitbox.center
        left_data = {
            "Type": self.playing_mode,
            "FPS": int(self.manager.clock.get_fps()),
            "Map": STR_TYPE[type(self.map.map)],
            "Player": (int(player[0]), int(player[1])),
            "Hitbox": (int(hitbox[0]), int(hitbox[1])),
        }
        right_data = {}

        if self.playing_mode == "host":
            player = self.player_controller.guest.position
            hitbox = self.player_controller.guest.hitbox.center
            right_data = {
                "Type": "guest",
                "RTT": round(self.network.guest_rtt_ms, 2),
                "Map": STR_TYPE[type(self.player_controller.guest.current_map)],
                "Player": (int(player[0]), int(player[1])),
                "Hitbox": (int(hitbox[0]), int(hitbox[1])),
            }

        elif self.playing_mode == "guest":
            player = self.player_controller.host.position
            hitbox = self.player_controller.host.hitbox.center
            right_data = {
                "Type": "host",
                "RTT": round(self.network.average_rtt_ms, 2),
                "Map": STR_TYPE[type(self.player_controller.host.current_map)],
                "Player": (int(player[0]), int(player[1])),
                "Hitbox": (int(hitbox[0]), int(hitbox[1])),
            }

        for i, (key, value) in enumerate(left_data.items()):
            text = f"{key}: {value}"
            surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (10, 10 + i * 22))
        screen_size = self.screen.get_size()
        for i, (key, value) in enumerate(right_data.items()):
            text = f"{key}: {value}"
            surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (screen_size[0] - 150, 10 + i * 22))

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
        self.map: MapManager = None
        self.nb_chunks = (8, 8)
        self.chunk_size = (32, 32)
        self.octaves = (8, 8)
        self.seed = 0

        # -- Moteur --
        self.moteur: Moteur = None

        # -- Ennemis --
        self.paths = [[]]
        self.ennemis: Dict[int, Ennemi] = {}

        # -- Réseau --
        self.address = "0.0.0.0"
        self.port = 8888

        # -- Mort / Spectateur --
        self.spectate_start = None

        # -- Inventaire -- : touche I pour ouvrir et fermer l'inventaire
        largeur, hauteur = self.screen.get_size()
        self.inv_joueur = Inventaire(rows=4, cols=8)
        self.ui_joueur = InventaireUI(
            self.screen,
            name="Sac du joueur",
            inv=self.inv_joueur,
            pos=((largeur - 480) // 2, hauteur - 290),
            is_merchant=False,
            is_visible=False,
        )
        self.drag_mgr = InventaireManager(self.screen, [self.ui_joueur])

        # Items de départ :
        self.inv_joueur.add_item(Item.create("Potion Rouge", 3))

        # PNJ :
        self.pnj_manager = PNJManager(self.screen, self.camera)
        self.money: int = 500

    def save(self, file: str | None = "save.json"):

        if isinstance(self.player_controller, SoloPlayerController):
            data = {
                "last_save": str(datetime.datetime.today()),
                "game_name": self.game_name,
                "playing_mode": "solo",
                "player": {
                    "position": list(self.player_controller.position),
                },
            }
        else:
            data = {
                "last_save": str(datetime.datetime.today()),
                "game_name": self.game_name,
                "playing_mode": "multi",
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
        self.playing_mode = data["playing_mode"]
