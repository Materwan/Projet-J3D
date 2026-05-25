"""Module pour la gestion du jeu."""

import time
import datetime
import json
from random import randint
from typing import Dict, List, Any, Tuple, TYPE_CHECKING
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
from map import MapManager, STR_TYPE, Hub
from camera_system import Camera
from hud import HUD
from inventory import Item, Inventaire, InventaireUI, InventaireManager
from ennemis import Ennemi
from particule import spawn_local_particle
from pnj import PNJManager
from sound import EFFECT

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
            "up": pygame.K_z,
            "down": pygame.K_s,
            "left": pygame.K_q,
            "right": pygame.K_d,
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
        self.seed = randint(0, 999999999)

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
        self.inv_joueur.add_item(Item.create("Potion Rouge", 2))

        # PNJ :
        self.pnj_manager = PNJManager(self.screen, self.camera)
        self.money: int = 500

        # Stats de run
        self.run_stats = RunStats()
        self.permanent_xp = 0
        self.font_xp = pygame.font.SysFont("segoeui", 18, bold=True)
        self.permanent_max_pv_bonus = 0
        self._guest_permanent_xp = 0
        self._guest_permanent_max_pv_bonus = 0

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
            if item.effect > 0:
                if self.player_controller.pv < self.player_controller.max_pv:
                    ui.inv.remove_item(slot[0], slot[1], 1)
                    self.player_controller.pv += 1
            else:
                ui.inv.remove_item(slot[0], slot[1], 1)
                self.player_controller.update_pv(-1)

    def is_in_hub(self) -> bool:
        """True uniquement si la carte active est le Hub."""
        return self.map is not None and isinstance(self.map.map, Hub)

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
            self.permanent_xp = initial.get("guest", {}).get("permanent_xp", 0)
            self.permanent_max_pv_bonus = initial.get("guest", {}).get(
                "permanent_max_pv_bonus", 0
            )

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

                self.player_controller.guest.max_pv += (
                    self._guest_permanent_max_pv_bonus
                )
                self.player_controller.guest.pv = self.player_controller.guest.max_pv

                # Réseau : construction de l'état initial avec la map
                initial_state = self.get_to_send_data_host(include_map=True)
                self.network = HostNetwork(self.port)
                self.network.start(initial_state)

            # -- Ennemis --
            self._spawn_enemies(
                self.map["principal_map"], nb=20, speed=1.0, chase_range=15
            )
            nb_dungeons = self.map["principal_map"].nb_dungeons
            for i in range(nb_dungeons):
                self._spawn_enemies(
                    self.map[f"dungeon{i}"], nb=8, speed=1.2, chase_range=10
                )

            self.pnj_manager = self.map.get_pnjs()

        # -- Keybinds --
        self.player_controller.keybinds = self.keybinds

        # -- Taille camera --
        self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
        self.camera.map_height = self.map.size[1] * self.map.tile_size[1]

        # Applique le bonus permanent de PV Max
        self.player_controller.max_pv += self.permanent_max_pv_bonus
        self.player_controller.pv = self.player_controller.max_pv
        # Synchronise le pnj_manager avec les valeurs courantes
        self.pnj_manager.permanent_xp = self.permanent_xp
        self.pnj_manager.permanent_max_pv_bonus = self.permanent_max_pv_bonus

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
        # Si déjà sur RECAP, ne pas re-déclencher !
        if self.manager.state == self.manager.states["RECAP"]:
            return

        pc = self.player_controller

        # -- Solo --
        if isinstance(pc, SoloPlayerController):
            if pc.is_dead:
                self.manager.states["RECAP"].start(self.run_stats)
                self.manager.change_state("RECAP")

        # -- Host --
        elif isinstance(pc, HostController):

            # Les deux sont morts → nouvelle map, retour au hub
            if pc.is_dead and pc.guest.is_dead:
                self.spectate_start = None
                self.manager.states["RECAP"].start(self.run_stats)
                self.manager.change_state("RECAP")

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
                self.manager.states["RECAP"].start(self.run_stats)
                self.manager.change_state("RECAP")

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

    def get_to_send_data_host(
        self, include_map: bool = False, reset: bool = False
    ) -> Dict[str, Any]:
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
            "reset": reset,
        }

        if include_map:
            dic["map"] = self.map._get_to_send_data()
            # Données permanentes du guest renvoyées au guest lors de la connexion
            dic["guest"]["permanent_xp"] = self._guest_permanent_xp
            dic["guest"]["permanent_max_pv_bonus"] = self._guest_permanent_max_pv_bonus

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
                "permanent_xp": self.permanent_xp,
                "permanent_max_pv_bonus": self.permanent_max_pv_bonus,
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

            # Mise à jour des données permanentes du guest (pour sauvegarde)
            old_bonus = self._guest_permanent_max_pv_bonus
            self._guest_permanent_xp = data["guest"]["permanent_xp"]
            self._guest_permanent_max_pv_bonus = data["guest"]["permanent_max_pv_bonus"]

            delta = self._guest_permanent_max_pv_bonus - old_bonus
            if delta > 0:
                hc.guest.max_pv += delta
                hc.guest.pv = hc.guest.max_pv

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
        if data.get("reset"):
            # Le host a régénéré le monde : on stocke la nouvelle map et on reset
            self.network._map_data = data["map"]
            self.reset()
            self.manager.change_state("GAME")
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

    def on_chest_opened(self):
        """Appeler depuis le système de coffres lors de l'ouverture."""
        self.run_stats.chests_opened += 1

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
                    EFFECT["slash"].play()
                    self.player_controller.attaque = True
                elif event.key == pygame.K_F2:  # Debug F2
                    self.show_hitbox = not self.show_hitbox
                elif event.key == pygame.K_F3:  # Debug F2
                    self.print_send_data = not self.print_send_data
                elif event.key == pygame.K_BACKSPACE:
                    # pour revenir au HUB
                    if not isinstance(self.map.map, Hub):
                        self.player_controller.update_pv(-999)
                elif event.key == pygame.K_TAB:  # Ouvre inventaire
                    if self.ui_joueur.is_visible == False:
                        EFFECT["open_inv"].play()
                        self.ui_joueur.is_visible = True
                    else:
                        self.ui_joueur.is_visible = False

            if not self.pnj_manager.handle_event(event, mouse_pos):
                self.drag_mgr.handle_event(event, mouse_pos, on_use=self._on_use)

        self.player_controller.velocity.update(0, 0)
        if self.pnj_manager.mode is None:
            self.player_controller.event(pygame.key.get_pressed())

    def reseau(self):
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
                if self.playing_mode != "guest":
                    self.reset()
                self.manager.change_state("MENU_P")
                return

    def update(self):
        """Met à jour le jeu."""

        # -- Réseau --
        self.reseau()

        # -- Map --
        self.map.update(self.get_position_target())

        # -- Joueur --
        self.player_controller.update(self.ennemis)
        self.camera.update(self.get_camera_target())

        # -- Ennemis --
        self.paths = self.map.update_ennemis()

        # PNJ
        old_max_pv_bonus = self.permanent_max_pv_bonus
        self.pnj_manager.set_inventaire(self.inv_joueur, self.money)
        self.pnj_manager.update(
            (
                int(self.player_controller.position.x),
                int(self.player_controller.position.y),
            ),
            self.manager.clock.get_time(),
        )
        self.money = self.pnj_manager.money
        self.permanent_xp = self.pnj_manager.permanent_xp
        self.permanent_max_pv_bonus = self.pnj_manager.permanent_max_pv_bonus

        # Mise à jour des permanent_max_pv_bonus
        delta = self.permanent_max_pv_bonus - old_max_pv_bonus
        if delta > 0:
            self.player_controller.max_pv += delta
            self.player_controller.pv = self.player_controller.max_pv
            self.hud.max_pv = self.player_controller.max_pv

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
            self.pnj_manager.permanent_xp = self.permanent_xp
            self.pnj_manager.permanent_max_pv_bonus = self.permanent_max_pv_bonus
            self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
            self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
        elif isinstance(self.player_controller, HostController):
            pass  # L'hôte garde self.ennemis de sa propre map, rien à faire.
        if move_camera:
            self.camera.set_position(player_controller.current_map.start_position)

    def _boss_fight_start(self):
        print("start boss fight")
        self.manager.states["CARD"].start(
            playing_mode=self.playing_mode,
            on_victory=self._on_card_victory,
            on_defeat=self._on_card_defeat,
        )
        self.manager.change_state("CARD")

    def _on_card_victory(self):
        self.run_stats.boss_killed += 1
        self.manager.states["RECAP"].start(self.run_stats)
        self.manager.change_state("RECAP")

    def _on_card_defeat(self):
        self.manager.states["RECAP"].start(self.run_stats)
        self.manager.change_state("RECAP")

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

    def _draw_decor(self, args: Tuple[pygame.Surface, Tuple[int, int]]):
        self.screen.blit(args[0], args[1])

    def display(self):
        """Affiche tout les éléments."""
        # -- Reset --
        self.screen.fill((32, 35, 32))

        # -- Map -- affiche uniquement le sol !
        self.map.display(self.camera)

        # -- Entités triées par Painter's Algorithm --
        drawables = []

        # -- Objets de décor --
        for (
            world_bottom_y,
            surface,
            (world_x, world_y),
        ) in self.map.get_visible_objects():
            screen_x = world_x + self.camera.camera.x + self.camera.offset_x
            screen_y = world_y + self.camera.camera.y + self.camera.offset_y
            drawables.append(
                (world_bottom_y, self._draw_decor, (surface, (screen_x, screen_y)))
            )

        # -- Players --
        pc = self.player_controller
        if not pc.is_dead:
            drawables.append((pc.hitbox.bottom, PlayerControllerBase.display, pc))
        partner = None
        if (
            isinstance(pc, HostController)
            and not pc.guest.is_dead
            and pc.current_map == pc.guest.current_map
        ):
            partner = pc.guest
        elif (
            isinstance(pc, GuestController)
            and not pc.host.is_dead
            and pc.current_map == pc.host.current_map
        ):
            partner = pc.host
        if partner:
            drawables.append(
                (partner.hitbox.bottom, PlayerControllerBase.display, partner)
            )

        # -- Ennemis --
        for ennemi in self.map.ennemis.values():
            if ennemi.hitbox:
                drawables.append((ennemi.hitbox.bottom, Ennemi.display, ennemi))

        # -- PNJ --
        screen_rect = pygame.Rect(
            0, 0, self.screen.get_width(), self.screen.get_height()
        )
        for pnj in self.pnj_manager.pnjs:
            screen_hitbox = self.camera.apply(pnj.hitbox)
            if screen_rect.colliderect(screen_hitbox):
                drawables.append((pnj.hitbox.bottom, self.pnj_manager.draw_pnj, pnj))

        # Tri et rendu
        for _, fn, entity in sorted(drawables, key=lambda x: x[0]):
            fn(entity)

        # Puis on affiche par dessus toute les entitées ceci :

        # -- Bulle [E] PNJ (toujours au-dessus) --
        self.pnj_manager.draw_pnj_bubble()

        # -- F2 : TOUTES les hitboxes --
        if self.show_hitbox:
            self.draw_debug_hitboxes()

        # -- Particules --
        for sprite in self.particles:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

        # -- Inventaire -- seulement si pas d'UI PNJ
        if self.pnj_manager.mode is None:
            self.drag_mgr.draw(pygame.mouse.get_pos())

        # -- PNJ UI --
        self.pnj_manager.draw_ui(pygame.mouse.get_pos())

        # -- XP Hub --
        self.draw_xp_hub()

        # -- HUD --
        if self.pnj_manager.mode == "amelioration":
            bonus = (
                self.pnj_manager.upgrade_ui.max_pv_bonus - self.permanent_max_pv_bonus
            )
            self.hud.draw(
                pv=self.player_controller.pv + bonus,
                max_pv=self.player_controller.max_pv + bonus,
            )
        else:
            self.hud.draw()

    def draw_xp_hub(self):
        """Affiche l'XP permanente en bas à droite — Hub uniquement."""
        if not isinstance(self.map.map, Hub):
            return

        # Lecture en temps réel si l'UI d'amélioration est ouverte
        if self.pnj_manager.mode == "amelioration":
            xp = self.pnj_manager.upgrade_ui.xp
            bonus = self.pnj_manager.upgrade_ui.max_pv_bonus
        else:
            xp = self.permanent_xp
            bonus = self.permanent_max_pv_bonus

        lines = [
            (f"XP  {xp}", (255, 215, 0)),
            (f"PV Max  +{bonus}", (100, 220, 100)),
        ]
        margin, pad_x, pad_y, gap = 12, 10, 6, 4
        rendered = [self.font_xp.render(t, True, c) for t, c in lines]
        w = max(s.get_width() for s in rendered) + pad_x * 2
        h = sum(s.get_height() for s in rendered) + pad_y * 2 + gap
        x = self.screen.get_width() - w - margin
        y = self.screen.get_height() - h - margin
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (14, 14, 26, 210), (0, 0, w, h), border_radius=7)
        pygame.draw.rect(bg, (180, 150, 0, 200), (0, 0, w, h), width=1, border_radius=7)
        self.screen.blit(bg, (x, y))
        cy = y + pad_y
        for surf in rendered:
            self.screen.blit(surf, (x + pad_x, cy))
            cy += surf.get_height() + gap

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

        # ajoute l'exp gagner et reset les stats pour la prochaine partie
        self.permanent_xp += self.run_stats.xp_gained
        self.run_stats.reset()

        # -- Controlleur --
        if self.playing_mode == "solo":
            self.seed = randint(0, 999999)
            self.map.reset(
                self.camera, 7, self.nb_chunks, self.chunk_size, self.octaves, self.seed
            )

            # Mise à jour de la caméra avec les nouvelles dimensions
            sizes = [m.size for m in self.map.maps.values()]
            self.camera.map_width = max(s[0] for s in sizes) * self.map.tile_size[0]
            self.camera.map_height = max(s[1] for s in sizes) * self.map.tile_size[1]
            self.camera.set_position(self.map.start_position)

            # Respawn le joueur dans le hub
            self.player_controller = SoloPlayerController(
                self.screen, self.camera, self.moteur, self.map.start_position
            )
            self.player_controller.current_map = self.map.map

            # HUD
            self.hud.player_controller = self.player_controller
            self.player_controller.max_pv += self.permanent_max_pv_bonus
            self.player_controller.pv = self.player_controller.max_pv
            self.hud.max_pv = self.player_controller.max_pv
            self.hud.pv = self.player_controller.pv

            # PNJ
            self.pnj_manager = self.map.get_pnjs()
            self.pnj_manager.permanent_xp = self.permanent_xp
            self.pnj_manager.permanent_max_pv_bonus = self.permanent_max_pv_bonus

        elif self.playing_mode == "host":
            self.seed = randint(0, 999999)
            self.map.reset(
                self.camera, 7, self.nb_chunks, self.chunk_size, self.octaves, self.seed
            )

            # Mise à jour de la caméra avec les nouvelles dimensions
            sizes = [m.size for m in self.map.maps.values()]
            self.camera.map_width = max(s[0] for s in sizes) * self.map.tile_size[0]
            self.camera.map_height = max(s[1] for s in sizes) * self.map.tile_size[1]
            self.camera.set_position(self.map.start_position)

            # Respawn des deux joueurs dans le hub (première map = hub)
            hub_start = self.map.start_position
            self.player_controller = HostController(
                self.screen, self.camera, self.moteur, hub_start
            )
            self.player_controller.guest.position.update(
                hub_start[0] + RESPAWN_OFFSET, hub_start[1]
            )
            self.player_controller.guest.hitbox.center = (
                self.player_controller.guest.position
            )
            self.player_controller.guest.hitbox_damage.midbottom = (
                self.player_controller.guest.position
            )
            self.player_controller.current_map = self.map.map

            self.player_controller.guest.max_pv += self._guest_permanent_max_pv_bonus
            self.player_controller.guest.pv = self.player_controller.guest.max_pv

            # HUD
            self.hud.player_controller = self.player_controller
            self.player_controller.max_pv += self.permanent_max_pv_bonus
            self.player_controller.pv = self.player_controller.max_pv
            self.hud.max_pv = self.player_controller.max_pv
            self.hud.pv = self.player_controller.pv

            # PNJ
            self.pnj_manager = self.map.get_pnjs()
            self.pnj_manager.permanent_xp = self.permanent_xp
            self.pnj_manager.permanent_max_pv_bonus = self.permanent_max_pv_bonus

            # Envoie la nouvelle map au guest via le slot prioritaire :
            # send_reset() garantit que ce paquet sera transmis exactement une
            # fois par le thread TCP, sans risque d'être écrasé par un frame
            # de jeu normal avant d'avoir été lu.
            if self.network is not None:
                self.network.send_reset(
                    self.get_to_send_data_host(include_map=True, reset=True)
                )
            self.player_controller.guest.position.x += 20

        elif self.playing_mode == "guest":

            # Récupération de la nouvelle map envoyée par l'hôte
            map_data = self.network.get_map_data()
            self.map.close_map()
            self.map = MapManager.create_map(self.screen, self, self.camera, map_data)
            self.moteur.map = self.map

            # Mise à jour de la caméra avec les nouvelles dimensions
            sizes = [m.size for m in self.map.maps.values()]
            self.camera.map_width = max(s[0] for s in sizes) * self.map.tile_size[0]
            self.camera.map_height = max(s[1] for s in sizes) * self.map.tile_size[1]
            self.camera.set_position(self.map.start_position)

            # Respawn dans le hub
            hub_start = self.map.start_position
            guest_start = (hub_start[0] + RESPAWN_OFFSET, hub_start[1])

            self.player_controller = GuestController(
                self.screen, self.camera, self.moteur, guest_start
            )
            self.player_controller.host.position.update(hub_start)
            self.player_controller.host.hitbox.center = hub_start
            self.player_controller.host.hitbox_damage.midbottom = hub_start
            self.player_controller.current_map = self.map.map

            # HUD
            self.hud.player_controller = self.player_controller
            self.player_controller.max_pv += self.permanent_max_pv_bonus  # ← ajoute
            self.player_controller.pv = self.player_controller.max_pv  # ← ajoute
            self.hud.max_pv = self.player_controller.max_pv
            self.hud.pv = self.player_controller.pv

            # PNJ
            self.pnj_manager = self.map.get_pnjs()
            self.pnj_manager.permanent_xp = self.permanent_xp
            self.pnj_manager.permanent_max_pv_bonus = self.permanent_max_pv_bonus

        # Dans reset(), après les blocs solo/host (avant # -- Keybinds --)
        if self.playing_mode in ("solo", "host"):
            self._spawn_enemies(
                self.map["principal_map"], nb=20, speed=1.0, chase_range=15
            )
            nb_dungeons = self.map["principal_map"].nb_dungeons
            for i in range(nb_dungeons):
                self._spawn_enemies(
                    self.map[f"dungeon{i}"], nb=8, speed=1.2, chase_range=10
                )

        # -- Keybinds --
        self.player_controller.keybinds = self.keybinds

        # -- Ennemis -- (vider les références à l'ancienne map)
        self.ennemis = {}
        self.paths = [[]]

        # -- Particules --
        self.particles = pygame.sprite.Group()

        # -- F2 --
        self.show_hitbox = False

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

    def save(self, file: str | None = "save.json"):
        if not self.is_in_hub():
            return

        base = {
            "last_save": str(datetime.datetime.today()),
            "game_name": self.game_name,
            "playing_mode": (
                "solo"
                if isinstance(self.player_controller, SoloPlayerController)
                else "multi"
            ),
            "permanent_xp": self.permanent_xp,
            "permanent_max_pv_bonus": self.permanent_max_pv_bonus,
        }

        if not isinstance(self.player_controller, SoloPlayerController):
            base["guest_permanent_xp"] = self._guest_permanent_xp
            base["guest_permanent_max_pv_bonus"] = self._guest_permanent_max_pv_bonus

        with open(file, "w") as f:
            f.write(json.dumps(base, indent="\t"))

    def load_save(self, file: str):
        with open(file, "r") as f:
            data = json.loads(f.read())

        self.game_name = data["game_name"]
        self.permanent_xp = data.get("permanent_xp", 0)
        self.permanent_max_pv_bonus = data.get("permanent_max_pv_bonus", 0)
        self._guest_permanent_xp = data.get("guest_permanent_xp", 0)
        self._guest_permanent_max_pv_bonus = data.get("guest_permanent_max_pv_bonus", 0)

    def _spawn_enemies(
        self,
        map_obj,
        nb: int,
        speed: float = 1.0,
        chase_range: int = 32,
    ) -> None:
        """Spawn nb ennemis sur des tuiles praticables. O(W·H) pour le sampling."""
        positions = map_obj.get_random_walkable_positions(nb)
        next_id = (max(map_obj.ennemis) + 1) if map_obj.ennemis else 0
        for i, pos in enumerate(positions):
            map_obj.ennemis[next_id + i] = Ennemi(
                self.screen,
                list(pos),
                speed,
                chase_range,
                map_obj,
                self.camera,
                self.moteur,
            )


"""
Code sur les Stats de la partie et le RecapScreen quand on meurt
"""

XP_PER_KILL = 10
XP_PER_CHEST = 25
XP_PER_BOSS = 100
GUEST_TIMEOUT_S = 60


class RunStats:
    """Statistiques collectées pendant une run. Remise à zéro à chaque nouvelle partie."""

    def __init__(self):
        self.reset()

    def update_xp_gained(self):
        self.xp_gained = (
            self.enemies_killed * XP_PER_KILL
            + self.boss_killed * XP_PER_BOSS
            + self.chests_opened * XP_PER_CHEST
        )

    def reset(self):
        self.enemies_killed = 0
        self.boss_killed = 0
        self.chests_opened = 0
        self.xp_gained = 0


class RecapScreen:
    """
    Écran récapitulatif de fin de run.

    Interface identique à DefaultManager (event / update / display / set_screen)
    sans héritage pour éviter la dépendance circulaire avec main.py.
    """

    def __init__(self, screen: pygame.Surface, manager: "Manager"):
        self.screen = screen
        self.larg, self.haut = self.screen.get_size()
        self.manager = manager

        self.stats = RunStats()
        self.guest_btn_clicked = False  # seulement pour le guest pour l'affichage
        self.time = 0.0
        self.btn_close_hovered = False

        # si True alors on est GAME_OVER sinon on est au RECAP
        self.phase = True

        self.f_death = pygame.font.SysFont("segoeui", 90, bold=True)
        self.f_title = pygame.font.SysFont("segoeui", 34, bold=True)
        self.f_stat = pygame.font.SysFont("segoeui", 22)
        self.f_xp = pygame.font.SysFont("segoeui", 28, bold=True)
        self.f_btn = pygame.font.SysFont("segoeui", 20, bold=True)

        self.btn_rect = pygame.Rect(
            self.larg // 2 - 155,
            self.haut // 2 + 168,
            310,
            48,
        )

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen
        self.larg, self.haut = self.screen.get_size()
        self.btn_rect = pygame.Rect(
            self.larg // 2 - 155,
            self.haut // 2 + 168,
            310,
            48,
        )

    def start(self, run_stats: RunStats):
        run_stats.update_xp_gained()
        self.stats = run_stats
        self.guest_btn_clicked = False
        self.time = 0.0
        self.phase = True
        EFFECT["game_over"].play()

    def return_HUB(self):

        if self.manager.states["GAME"].playing_mode == "guest":
            self.guest_btn_clicked = True
        else:
            self.manager.states["GAME"].reset()
            self.manager.change_state("GAME")

    def event(self, events: list[pygame.event.Event]):
        mouse = pygame.mouse.get_pos()
        self.btn_close_hovered = self.phase == False and self.btn_rect.collidepoint(
            mouse
        )

        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False

            if self.phase == False:
                pressed_key = event.type == pygame.KEYDOWN and (
                    event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE
                )
                pressed_btn = (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.btn_close_hovered
                )
                if pressed_key or pressed_btn:
                    self.return_HUB()

    def update(self):
        self.time += self.manager.clock.get_time() / 1000.0
        game = self.manager.states["GAME"]

        if self.phase == True:
            game.update()
            if self.time >= 3:
                if self.time >= 4:  # on attend 1s de plus
                    self.phase = False
                    self.time = 0.0
        else:
            if game.playing_mode in ("host", "guest") and game.network is not None:
                game.reseau()

    def display(self):
        self.manager.states["GAME"].display()

        if self.phase == True:
            # PHASE DE GAME_OVER

            progress = min(self.time / 3, 1.0)
            overlay_alpha = int(200 * progress)
            overlay = pygame.Surface((self.larg, self.haut))
            overlay.fill((8, 8, 18))
            overlay.set_alpha(overlay_alpha)
            self.screen.blit(overlay, (0, 0))

            text_progress = max(0.0, (progress - 0.1) / 0.9)
            if text_progress > 0:
                text_alpha = int(255 * text_progress)
                surf = self.f_death.render("GAME OVER", True, (220, 60, 60))
                surf.set_alpha(text_alpha)
                self.screen.blit(
                    surf,
                    (
                        self.larg // 2 - surf.get_width() // 2,
                        self.haut // 2 - surf.get_height() // 2,
                    ),
                )
        else:
            # PHASE DE RECAP
            overlay = pygame.Surface((self.larg, self.haut), pygame.SRCALPHA)
            overlay.fill((8, 8, 18, 200))
            self.screen.blit(overlay, (0, 0))

            # Affiche le Panel
            pw, ph = 440, 310
            px = self.larg // 2 - pw // 2
            py = self.haut // 2 - ph // 2 - 44

            surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pygame.draw.rect(surf, (14, 14, 26, 245), (0, 0, pw, ph), border_radius=12)
            pygame.draw.rect(
                surf, (70, 70, 115, 255), (0, 0, pw, ph), width=2, border_radius=12
            )
            self.screen.blit(surf, (px, py))

            cx = self.larg // 2
            y = py + 22

            title = self.f_title.render("Run terminée !", True, (230, 210, 160))
            self.screen.blit(title, (cx - title.get_width() // 2, y))
            y += title.get_height() + 18

            pygame.draw.line(self.screen, (55, 55, 95), (px + 20, y), (px + pw - 20, y))
            y += 16

            rows = (
                ("Ennemis éliminés", self.stats.enemies_killed),
                ("Boss éliminés", self.stats.boss_killed),
                ("Coffres ouverts", self.stats.chests_opened),
            )
            for label, value in rows:
                lbl = self.f_stat.render(label, True, (200, 200, 215))
                val = self.f_stat.render(str(value), True, (85, 195, 215))
                self.screen.blit(lbl, (px + 24, y))
                self.screen.blit(val, (px + pw - val.get_width() - 24, y))
                y += lbl.get_height() + 12

            y += 4
            pygame.draw.line(self.screen, (55, 55, 95), (px + 20, y), (px + pw - 20, y))
            y += 14

            xp_l = self.f_xp.render("XP Gagnée", True, (255, 210, 60))
            xp_v = self.f_xp.render(f"+{self.stats.xp_gained}", True, (255, 230, 100))
            self.screen.blit(xp_l, (px + 24, y))
            self.screen.blit(xp_v, (px + pw - xp_v.get_width() - 24, y))

            # Affiche le bouton "Continuer"
            mode = self.manager.states["GAME"].playing_mode
            waiting_for_host = mode == "guest" and self.guest_btn_clicked

            label = (
                f"En attente de l'hôte{'.' * (int(self.time * 2) % 4)}"
                if waiting_for_host
                else "Continuer  →"
            )
            enabled = not waiting_for_host
            btn = self.btn_rect
            hovered = self.btn_close_hovered and enabled

            s = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
            pygame.draw.rect(
                s,
                (55, 85, 155, 220) if hovered else (22, 22, 44, 200),
                (0, 0, btn.width, btn.height),
                border_radius=8,
            )
            pygame.draw.rect(
                s,
                (120, 150, 225, 255) if hovered else (50, 50, 95, 255),
                (0, 0, btn.width, btn.height),
                width=2,
                border_radius=8,
            )
            self.screen.blit(s, btn.topleft)

            col = (240, 240, 255) if enabled else (100, 100, 140)
            ts = self.f_btn.render(label, True, col)
            self.screen.blit(
                ts,
                (
                    btn.x + (btn.width - ts.get_width()) // 2,
                    btn.y + (btn.height - ts.get_height()) // 2,
                ),
            )
