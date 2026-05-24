from typing import List, Dict, Tuple, Callable, TYPE_CHECKING
from player import GuestController
import threading
import socket
import json
import asyncio
import time
import os

import pygame as p
import animations as a
from utils import resource_path, DefaultManager

if TYPE_CHECKING:
    from main import Manager

MENU_ASSET_DIRECTORY = resource_path(r"Ressources\UIAsset")
BACKGROUND = os.path.join(MENU_ASSET_DIRECTORY, "fond ecran menu.png")
PLAY_BUTTON = os.path.join(MENU_ASSET_DIRECTORY, "PLAY.png")
SETTING_BUTTON = os.path.join(MENU_ASSET_DIRECTORY, "SETTINGS.png")
EXIT_BUTTON = os.path.join(MENU_ASSET_DIRECTORY, "EXIT.png")
EMPTY_BUTTON = os.path.join(MENU_ASSET_DIRECTORY, "EMPTY.png")
TITLE = os.path.join(MENU_ASSET_DIRECTORY, "logo.png")

SAVE_FILE = resource_path(r"save")
SAVE_MULTI = os.path.join(SAVE_FILE, "multiplayer")
SAVE_SOLO = os.path.join(SAVE_FILE, "solo")

UDP_IP = "0.0.0.0"
UDP_PORT = 9999

FULLSCREEN_SIZE = p.display.Info().current_w, p.display.Info().current_h


class Menu(DefaultManager):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        self.eltpages = []
        self.textpages = []
        self.list_file = []
        self.WINDOWS = screen.get_size()
        self.half = (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2)
        self.screen = screen
        self.bg_img = p.image.load(BACKGROUND).convert()
        self.bg_img_coord = self.bg_img.get_rect()
        self.manager = manager
        self.keybinds = {
            "up": p.K_z,
            "down": p.K_s,
            "left": p.K_q,
            "right": p.K_d,
            "attack": p.K_SPACE,
        }
        self.key = {"up": False, "down": False, "left": False, "right": False}
        self.manager.running = False
        self.blackscreen = p.Surface(self.WINDOWS, p.SRCALPHA)
        p.draw.rect(
            self.blackscreen,
            (10, 10, 22, 100),
            (0, 0, self.WINDOWS[0], self.WINDOWS[1]),
        )
        self.nbr_file_solo = len(os.listdir(SAVE_SOLO))
        self.nbr_file_multi = len(os.listdir(SAVE_MULTI))

        # =======================Function Button Start=======================
        def retour(mode: str):
            self.manager.change_state(mode)

        def reprendre(mode: str, partie: int):
            playing_mode = "solo" if mode == "solo" else "host"
            self.manager.states["GAME"].playing_mode = playing_mode
            current_save = SAVE_FILE + "/" + mode + "/" + self.list_file[partie]
            self.manager.states["MENU_PAUSE"].current_save = current_save
            self.manager.states["GAME"].load_save(current_save)
            self.manager.change_state("LOADING")
            self.manager.states["LOADING"].start(playing_mode)

        def destroy_save(mode: str, save: str):
            os.remove(SAVE_FILE + "/" + mode + "/" + save)
            if mode == "solo":
                self.nbr_file_solo -= 1
                self.manager.states["MENU_SOLO"].reset_solo()
            else:
                self.nbr_file_multi -= 1
                self.manager.states["MENU_MULTIPLAYER"].reset_multi()

        # =======================Function Button End=======================

        # =======================Button End=======================
        def no_function():
            pass

        self.destroy_save = destroy_save
        self.reprendre = reprendre
        self.no_function = no_function
        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.retour = a.Button(EMPTY_BUTTON, self.screen, (170, 67), retour, text="<--")
        # =======================Button End=======================

    def set_screen(self, screen: p.Surface):
        self.screen = screen
        self.WINDOWS = screen.get_size()
        self.half = (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2)
        self.blackscreen = p.Surface(self.WINDOWS, p.SRCALPHA)
        p.draw.rect(
            self.blackscreen,
            (10, 10, 22, 100),
            (0, 0, self.WINDOWS[0], self.WINDOWS[1]),
        )
        self.retour.set_screen(screen, (170, 67))

    def change_button_text(
        self,
        changetext: str,
        button: a.Button,
    ):
        """change the text in a button"""
        button.text.update(changetext)

    def interchange(
        self,
        changetext: str,
        button: a.Button,
        direction: str,
        bool: bool,
    ):
        """change the texte of the button that you want to change the keybind"""
        self.change_button_text(changetext, button)
        self.key[direction] = bool

    def create_list_save_and_button(
        self, mode: str
    ) -> Tuple[List[a.Button], List[a.Button], Dict]:
        list_button = []
        list_button_suppr = []
        list_save = []
        count = 0
        saves, files = get_all_saves(mode)
        for serveur in saves:
            button = a.Button(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 - 200 + count * 150),
                self.reprendre,
                text=serveur["game_name"],
            )
            button_suppr = a.Button(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2 + 200, self.WINDOWS[1] // 2 - 200 + count * 150),
                self.destroy_save,
                text="SUPPRIMER",
            )
            list_save.append(serveur)
            list_button.append(button)
            list_button_suppr.append(button_suppr)
            count += 1
        return list_button, list_button_suppr, files

    def pagedisplay(self):
        for elt in self.eltpages:
            elt.display()
        for elt in self.textpages:
            elt.draw_text()

    def dehover_all(self):
        for button in self.eltpages:
            button.hover = False

    def declicked_all(self):
        for button in self.eltpages:
            button.clicked = False


class Principal_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def start():
            self.manager.change_state("MENU_PLAY")

        def settings():
            self.manager.change_state("MENU_SETTING")

        def quit():
            self.manager.running = False

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.start = a.Button(
            PLAY_BUTTON, self.screen, (self.half[0], self.half[1] - 100), start
        )
        self.settings = a.Button(
            SETTING_BUTTON,
            self.screen,
            (self.half[0], self.half[1] + 50),
            settings,
            button_scale=0.8,
        )
        self.quit = a.Button(
            EXIT_BUTTON,
            self.screen,
            (self.half[0], self.half[1] + 200),
            quit,
        )
        self.titre = a.Button(
            TITLE,
            self.screen,
            (self.half[0], self.half[1] // 3),
            self.no_function,
            button_scale=0.6,
        )
        # =======================Button End=======================

        self.eltpages = [self.titre, self.start, self.settings, self.quit]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.start.set_screen(screen, (self.half[0], self.half[1] - 100))
        self.settings.set_screen(screen, (self.half[0], self.half[1] + 50))
        self.quit.set_screen(screen, (self.half[0], self.half[1] + 200))
        self.titre.set_screen(screen, (self.half[0], self.half[1] // 3))

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
        self.quit.event(events, coord)
        self.start.event(events, coord)
        self.settings.event(events, coord)

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()


class Setting_Menu(Menu):

    def __init__(
        self, screen: p.Surface, manager: "Manager", menu_appel: str | None = "MENU_P"
    ):
        super().__init__(screen, manager)
        self.manager.running = True
        self.surface_copie = None
        self.menu_appel = menu_appel

        # =======================Function Button Start=======================
        def retour(mode: str):
            self.manager.states["GAME"].keybinds = self.keybinds
            self.manager.change_state(mode)

        def changeup():
            self.interchange("...", self.changeup, "up", True)

        def changedown():
            self.interchange("...", self.changedown, "down", True)

        def changeleft():
            self.interchange("...", self.changeleft, "left", True)

        def changeright():
            self.interchange("...", self.changeright, "right", True)

        def changeattack():
            self.interchange("...", self.changeattack, "attack", True)

        def volume(choise: bool):
            self.manager.change_volume(choise)

        def window():
            current = self.changewindow.text.to_display_text
            if current == "PLEIN ÉCRAN":
                # Borderless fullscreen : fenêtre sans bordure à la taille du bureau
                manager.resize(FULLSCREEN_SIZE, menu_appel)
                self.change_button_text("FENÊTRÉ", self.changewindow)
            else:
                # Retour en mode fenêtré
                manager.resize((1080, 780), menu_appel)
                self.change_button_text("PLEIN ÉCRAN", self.changewindow)

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.retour.clicked_function = retour
        self.changeup = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 - 70),
            changeup,
            text="HAUT: " + p.key.name(self.keybinds["up"]),
        )
        self.changedown = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 + 70),
            changedown,
            text="BAS: " + p.key.name(self.keybinds["down"]),
        )
        self.changeleft = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70),
            changeleft,
            text="GAUCHE: " + p.key.name(self.keybinds["left"]),
        )
        self.changeright = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            changeright,
            text="DROITE: " + p.key.name(self.keybinds["right"]),
        )
        self.changeattack = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 + 200),
            changeattack,
            text="ATTAQUE: " + p.key.name(self.keybinds["attack"]),
        )
        self.volume_up = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 70),
            volume,
            text="+",
        )
        self.volume_down = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 + 70),
            volume,
            text="-",
        )
        self.volume = a.Text(
            "Volume du son",
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 180),
        )
        self.changewindow = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] - 170, 67),
            window,
            text=("FENÊTRÉ" if self.manager.fullscreen else "PLEIN ÉCRAN"),
        )
        # =======================Button End=======================

        self.eltpages = [
            self.changeup,
            self.changedown,
            self.changeleft,
            self.changeright,
            self.changeattack,
            self.volume_up,
            self.volume_down,
            self.retour,
            self.changewindow,
        ]
        self.textpages = [self.volume]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.changeup.set_screen(
            screen, (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 - 70)
        )
        self.changedown.set_screen(
            screen, (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 + 70)
        )
        self.changeleft.set_screen(
            screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70)
        )
        self.changeright.set_screen(
            screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70)
        )
        self.changeattack.set_screen(
            screen, (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 + 200)
        )
        self.volume_up.set_screen(
            screen, (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 70)
        )
        self.volume_down.set_screen(
            screen, (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 + 70)
        )
        self.volume.set_screen(
            self.screen, (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 180)
        )
        self.changewindow.set_screen(screen, (self.WINDOWS[0] - 170, 67))

    def changekey(self, event: p.event.Event):
        """take the last keybind to replace the old one"""
        for elt in self.key.keys():
            if self.key[elt]:
                if event.type == p.KEYDOWN and event.key != p.K_ESCAPE:
                    self.keybinds[elt] = event.key
                self.key[elt] = False

    def checkchangekey(self) -> bool:
        """look if there is no other keybind that is being change"""
        for elt in self.key.keys():
            if self.key[elt]:
                return False
        return True

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE and self.checkchangekey():
                    self.manager.states["GAME"].keybinds = self.keybinds
                    self.manager.change_state(self.menu_appel)
                else:
                    self.changekey(event)  # try to change the keybind
                    self.interchange(
                        "HAUT: " + p.key.name(self.keybinds["up"]),
                        self.changeup,
                        "up",
                        False,
                    )
                    self.interchange(
                        "BAS: " + p.key.name(self.keybinds["down"]),
                        self.changedown,
                        "down",
                        False,
                    )
                    self.interchange(
                        "GAUCHE: " + p.key.name(self.keybinds["left"]),
                        self.changeleft,
                        "left",
                        False,
                    )
                    self.interchange(
                        "DROITE: " + p.key.name(self.keybinds["right"]),
                        self.changeright,
                        "right",
                        False,
                    )
                    self.interchange(
                        "ATTAQUE: " + p.key.name(self.keybinds["attack"]),
                        self.changeattack,
                        "attack",
                        False,
                    )
        if self.checkchangekey():
            """if a keybind is changing dont look for collidepoint"""
            self.retour.event(events, coord, self.menu_appel)
            self.changeup.event(events, coord)
            self.changedown.event(events, coord)
            self.changeleft.event(events, coord)
            self.changeright.event(events, coord)
            self.changeattack.event(events, coord)
            self.volume_up.event(events, coord, True)
            self.volume_down.event(events, coord, False)
            self.changewindow.event(events, coord)
            if self.manager.states["GAME"].keybinds != self.keybinds:
                self.manager.states["GAME"].keybinds = self.keybinds

    def update(self):
        if (
            self.menu_appel != "MENU_P"
            and self.manager.states["GAME"].playing_mode != "solo"
        ):
            self.manager.states["GAME"].update()

    def display(self):
        if self.menu_appel == "MENU_P":
            self.screen.blit(self.bg_img, self.bg_img_coord)
        else:
            self.manager.states["GAME"].display()
            self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()
        self.declicked_all()


class Play_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def multiplayer():
            self.manager.change_state("MENU_MULTIPLAYER")

        def solo():
            self.manager.change_state("MENU_SOLO")

        def joinmultiplayer():
            self.manager.states["MENU_MULTI"].udp_event.set()
            self.manager.change_state("MENU_MULTI")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.multiplayer = a.Button(
            EMPTY_BUTTON,
            self.screen,
            self.half,
            multiplayer,
            text="MULTIJOUEUR",
        )
        self.solo = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            solo,
            text="SOLO",
        )
        self.joinmultiplayer = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            joinmultiplayer,
            text="REJOINDRE MULTIJOUEUR",
        )
        # =======================Button End=======================

        self.eltpages = [self.retour, self.solo, self.multiplayer, self.joinmultiplayer]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.multiplayer.set_screen(screen, self.half)
        self.solo.set_screen(screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150))
        self.joinmultiplayer.set_screen(
            screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150)
        )

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.manager.change_state("MENU_P")
                elif event.key == p.K_0:
                    self.manager.states["GAME"].load_save("save.json")
        self.solo.event(events, coord)
        self.multiplayer.event(events, coord)
        self.joinmultiplayer.event(events, coord)
        self.retour.event(events, coord, "MENU_P")

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.declicked_all()


class Join_Multi_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.serveurs_save = 0
        self.list_button: List[a.Button] = []
        self.manager.running = True
        self.serveurs = {}
        self.serveurs: Dict[Dict]
        self.upd_prot = threading.Thread(target=self.recieve_udp, daemon=True)
        self.udp_event = threading.Event()
        self.upd_prot.start()

        # =======================Function Button Start=======================
        def retour(mode: str):
            self.udp_event.clear()
            self.manager.change_state(mode)

        def rejoindre(address: str):
            self.udp_event.clear()
            self.manager.states["GAME"].playing_mode = "guest"
            self.manager.states["GAME"].address = address

            # pour l'écran de chargement !
            self.manager.change_state("LOADING")
            self.manager.states["LOADING"].start("guest")

        self.rejoindre = rejoindre
        self.retour.clicked_function = retour
        # =======================Function Button End=======================

        self.eltpages = [self.retour]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        for count, button in enumerate(self.list_button):
            button.set_screen(
                screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150)
            )

    def initialize_udp(self):

        self.upd_func = asyncio.run(self.recieve_udp())

    def recieve_udp(self):

        sock_set = False
        sock = None

        while self.manager.running:

            try:
                if self.udp_event.is_set():
                    if not sock_set:
                        sock_set = True
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.settimeout(0.5)
                        sock.bind(("", UDP_PORT))
                        print("[Guest] Écoute UDP démarrée")

                    try:
                        data, addr = sock.recvfrom(1024)
                        data = json.loads(data.decode("utf-8").strip())
                        if addr[0] not in self.serveurs:
                            self.serveurs[addr[0]] = data
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        pass
                else:
                    if sock_set:
                        sock_set = False
                        sock.close()
                        print("[Guest] Écoute UDP arrêtée")
                    time.sleep(0.5)
            except socket.timeout:
                # Enleve les serveurs expirés
                now = time.time()
                expired = [
                    ip
                    for ip, info in self.serveurs.items()
                    if now - info.get("last", 0) > 2.0
                ]
                for ip in expired:
                    del self.serveurs[ip]
                continue
        if sock:
            if sock_set:
                sock_set = False
                sock.close()
                print("UDP recieve protocol stopped")

    def create_list_button(self):
        self.list_button = []
        count = 0
        for serveur in self.serveurs.keys():
            button = a.Button(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150),
                self.rejoindre,
                text=serveur,
            )
            self.list_button.append(button)
            count += 1

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.udp_event.clear()
                self.manager.change_state("MENU_PLAY")
        self.retour.event(events, coord, "MENU_PLAY")
        for elt in self.list_button:
            elt.event(events, coord, elt.text.to_display_text)

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        if len(self.serveurs) != self.serveurs_save:
            self.serveurs_save = len(self.serveurs)
            self.create_list_button()
            self.eltpages = self.list_button[:]
            self.eltpages.append(self.retour)
        self.pagedisplay()
        self.declicked_all()


class Pause_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.surface_copie = None
        self.blackscreen = p.Surface(self.WINDOWS, p.SRCALPHA)
        p.draw.rect(
            self.blackscreen,
            (10, 10, 22, 100),
            (0, 0, self.WINDOWS[0], self.WINDOWS[1]),
        )
        self.current_save = None
        self.manager.running = True

        # =======================Function Button Start=======================
        def resume():
            self.manager.change_state("GAME")

        def save():
            self.manager.states["GAME"].save(self.current_save)
            if self.manager.states["GAME"].playing_mode == "solo":
                self.manager.states["MENU_SOLO"].reset_solo()
            else:
                self.manager.states["MENU_MULTIPLAYER"].reset_multi()

        def settings():
            self.manager.states["MENU_SETTING_PAUSE"].keybinds = self.manager.states[
                "GAME"
            ].keybinds
            self.manager.change_state("MENU_SETTING_PAUSE")

        def quit():
            game = self.manager.states["GAME"]
            if isinstance(game.player_controller, GuestController):
                game._send_close_and_disconnect()
            game.close_game()
            self.manager.change_state("MENU_P")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.resume = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 220),
            resume,
            text="REPRENDRE",
        )
        self.save = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 70),
            save,
            text="SAUVEGARDE",
        )
        self.settings = a.Button(
            SETTING_BUTTON,
            self.screen,
            (self.half[0], self.half[1] + 70),
            settings,
            button_scale=0.8,
        )
        self.quit = a.Button(
            EXIT_BUTTON, self.screen, (self.half[0], self.half[1] + 220), quit, text=""
        )
        # =======================Button End=======================

        self.eltpages = [self.resume, self.save, self.settings, self.quit]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.resume.set_screen(self.screen, (self.half[0], self.half[1] - 220))
        self.save.set_screen(self.screen, (self.half[0], self.half[1] - 70))
        self.settings.set_screen(self.screen, (self.half[0], self.half[1] + 70))
        self.quit.set_screen(self.screen, (self.half[0], self.half[1] + 220))

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.resume.clicked_function()
        self.quit.event(events, coord)
        self.resume.event(events, coord)
        self.settings.event(events, coord)
        self.save.event(events, coord)

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.resume.clicked_function()
        self.quit.event(events, coord)
        self.resume.event(events, coord)
        self.settings.event(events, coord)

        game = self.manager.states["GAME"]
        if game.is_in_hub() and not isinstance(game.player_controller, GuestController):
            self.save.event(events, coord)

    def update(self):
        if self.manager.states["GAME"].playing_mode != "solo":
            self.manager.states["GAME"].update()

    def display(self):
        game = self.manager.states["GAME"]

        game.display()
        self.screen.blit(self.blackscreen, (0, 0))
        for elt in self.eltpages:
            if elt is self.save:
                if (
                    isinstance(game.player_controller, GuestController)
                    or not game.is_in_hub()
                ):
                    continue
            if elt is self.save and not game.is_in_hub():
                continue
            elt.display()
        self.declicked_all()


class Solo_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def create():
            if self.nbr_file_solo < 3:
                self.manager.states["INPUTBOX"].playing_mode = "solo"
                self.manager.change_state("INPUTBOX")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.solo = a.Text(
            "SOLO",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            font_size=100,
        )
        self.create = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + self.WINDOWS[1] // 3),
            create,
            text="CRÉER" if self.nbr_file_solo < 3 else "SAUVEGARDE MAXIMUM",
        )
        self.list_button, self.list_button_suppr, self.list_file = (
            self.create_list_save_and_button("solo")
        )
        # =======================Button End=======================

        self.eltpages = [self.retour, self.create]
        self.textpages = [self.solo]
        for elt in self.list_button:
            self.eltpages.append(elt)
        for elt in self.list_button_suppr:
            self.eltpages.append(elt)

    def reset_solo(self):
        self.list_button, self.list_button_suppr, self.list_file = (
            self.create_list_save_and_button("solo")
        )
        self.change_button_text(
            "CRÉER" if self.nbr_file_solo < 3 else "SAUVEGARDE MAXIMUM", self.create
        )
        self.eltpages = [self.retour, self.create]
        for elt in self.list_button:
            self.eltpages.append(elt)
        for elt in self.list_button_suppr:
            self.eltpages.append(elt)

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.solo.set_screen(self.screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10))
        self.create.set_screen(
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + self.WINDOWS[1] // 3),
        )
        for count, button in enumerate(self.list_button):
            button.set_screen(
                self.screen,
                (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 - 200 + count * 150),
            )
        for count, button in enumerate(self.list_button_suppr):
            button.set_screen(
                self.screen,
                (self.WINDOWS[0] // 2 + 200, self.WINDOWS[1] // 2 - 200 + count * 150),
            )

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.manager.change_state("MENU_PLAY")
        self.retour.event(events, coord, "MENU_PLAY")
        self.create.event(events, coord)
        ind = 0
        while ind < len(self.list_button):
            self.list_button[ind].event(events, coord, "solo", ind)
            self.list_button_suppr[ind].event(
                events, coord, "solo", self.list_file[ind]
            )
            ind += 1

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.declicked_all()


class Multiplayer_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def create():
            if self.nbr_file_multi < 3:
                self.manager.states["INPUTBOX"].playing_mode = "host"
                self.manager.change_state("INPUTBOX")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.multiplayer = a.Text(
            "MULTIJOUEUR",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            font_size=100,
        )
        self.create = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + self.WINDOWS[1] // 3),
            create,
            text="CRÉER" if self.nbr_file_multi < 3 else "SAUVEGARDE MAXIMUM",
        )
        self.list_button, self.list_button_suppr, self.list_file = (
            self.create_list_save_and_button("multiplayer")
        )
        # =======================Button End=======================

        self.eltpages = [self.retour, self.create]
        self.textpages = [self.multiplayer]
        for elt in self.list_button:
            self.eltpages.append(elt)
        for elt in self.list_button_suppr:
            self.eltpages.append(elt)

    def reset_multi(self):
        self.list_button, self.list_button_suppr, self.list_file = (
            self.create_list_save_and_button("multiplayer")
        )
        self.eltpages = [self.retour, self.create]
        self.change_button_text(
            "CRÉER" if self.nbr_file_multi < 3 else "SAUVEGARDE MAXIMUM", self.create
        )
        for elt in self.list_button:
            self.eltpages.append(elt)
        for elt in self.list_button_suppr:
            self.eltpages.append(elt)

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.multiplayer.set_screen(
            self.screen, (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10)
        )
        self.create.set_screen(
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + self.WINDOWS[1] // 3),
        )
        for count, button in enumerate(self.list_button):
            button.set_screen(
                self.screen,
                (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 - 200 + count * 150),
            )
        for count, button in enumerate(self.list_button_suppr):
            button.set_screen(
                self.screen,
                (self.WINDOWS[0] // 2 + 200, self.WINDOWS[1] // 2 - 200 + count * 150),
            )

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.manager.change_state("MENU_PLAY")
        self.retour.event(events, coord, "MENU_PLAY")
        self.create.event(events, coord)
        ind = 0
        while ind < len(self.list_button):
            self.list_button[ind].event(events, coord, "multiplayer", ind)
            self.list_button_suppr[ind].event(
                events, coord, "multiplayer", self.list_file[ind]
            )
            ind += 1

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.declicked_all()


class InputBox(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True
        self.rect = p.Rect(
            self.WINDOWS[0] // 2 - 150,
            self.WINDOWS[1] // 2 - 25,
            300,
            50,
        )
        self.color = (255, 255, 255)
        self.text = ""
        self.screen = screen
        self.font = p.font.Font(None, 40)
        self.font_hint = p.font.Font(None, 30)
        self.active = False
        self.playing_mode = "solo"

        self.error_msg = ""
        self.error_timer = 0.0
        self.ERROR_DURATION = 2500.0

        self.btn_rect = p.Rect(
            self.WINDOWS[0] // 2 - 80,
            self.WINDOWS[1] // 2 + 45,
            160,
            44,
        )
        self.btn_hovered = False

        def retour_action(mode: str):
            self.text = ""
            self.error_msg = ""
            self.manager.change_state(mode)

        self.retour.clicked_function = retour_action
        self.eltpages = [self.retour]

    def set_screen(self, screen: p.Surface):
        super().set_screen(screen)
        self.rect.topleft = (self.WINDOWS[0] // 2 - 150, self.WINDOWS[1] // 2 - 25)
        self.btn_rect = p.Rect(
            self.WINDOWS[0] // 2 - 80,
            self.WINDOWS[1] // 2 + 45,
            160,
            44,
        )

    def _show_error(self, msg: str):
        self.error_msg = msg
        self.error_timer = self.ERROR_DURATION

    def _confirm(self):
        name = self.text.strip()
        if not name:
            self.error_msg = (
                "Attention : le nom de la sauvegarde ne peut pas être vide."
            )
            self.error_timer = self.ERROR_DURATION
        else:
            if self.playing_mode == "solo":
                self.lancer_solo()
            else:
                self.lancer_multi()

    def event(self, events: list[p.event.Event]):
        mouse_pos = p.mouse.get_pos()
        self.btn_hovered = self.btn_rect.collidepoint(mouse_pos)

        target = "MENU_SOLO" if self.playing_mode == "solo" else "MENU_MULTIPLAYER"

        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False

            elif event.type == p.MOUSEBUTTONDOWN and event.button == 1:
                self.active = self.rect.collidepoint(event.pos)
                if self.btn_hovered:
                    self._confirm()

            elif event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.text = ""
                    self.error_msg = ""
                    self.manager.change_state(target)
                elif self.active:
                    if event.key == p.K_BACKSPACE:
                        self.text = self.text[:-1]
                    elif event.key == p.K_RETURN:
                        self._confirm()
                    elif len(self.text) < 20:
                        self.text += event.unicode

        self.retour.event(events, mouse_pos, target)

    def lancer_solo(self):
        save_name = self.text.strip()
        if "save_0" not in self.manager.states["MENU_SOLO"].list_file:
            current_save = SAVE_SOLO + "/save_0"
        elif "save_1" not in self.manager.states["MENU_SOLO"].list_file:
            current_save = SAVE_SOLO + "/save_1"
        else:
            current_save = SAVE_SOLO + "/save_2"
        self.manager.states["MENU_SOLO"].nbr_file_solo += 1
        self.manager.states["MENU_PAUSE"].current_save = current_save
        self.manager.states["GAME"].playing_mode = "solo"
        self.manager.states["GAME"].game_name = save_name
        self.text = ""
        self.manager.change_state("LOADING")
        self.manager.states["LOADING"].start("solo")

    def lancer_multi(self):
        save_name = self.text.strip()
        if "save_0" not in self.manager.states["MENU_MULTIPLAYER"].list_file:
            current_save = SAVE_MULTI + "/save_0"
        elif "save_1" not in self.manager.states["MENU_MULTIPLAYER"].list_file:
            current_save = SAVE_MULTI + "/save_1"
        else:
            current_save = SAVE_MULTI + "/save_2"
        self.manager.states["MENU_MULTIPLAYER"].nbr_file_multi += 1
        self.manager.states["MENU_PAUSE"].current_save = current_save
        self.manager.states["GAME"].playing_mode = "host"
        self.manager.states["GAME"].game_name = save_name
        self.text = ""
        self.manager.change_state("LOADING")
        self.manager.states["LOADING"].start("host")

    def update(self):
        self.error_timer = max(0.0, self.error_timer - self.manager.clock.get_time())

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.screen.blit(self.blackscreen, (0, 0))

        instruction = self.font_hint.render(
            "Veuillez donner un nom à la partie :",
            True,
            (200, 200, 200),
        )
        self.screen.blit(
            instruction,
            (
                self.WINDOWS[0] // 2 - instruction.get_width() // 2,
                self.WINDOWS[1] // 2 - 75,
            ),
        )

        # Champ de saisie
        txt_surface = self.font.render(self.text, True, (255, 255, 255))
        p.draw.rect(self.screen, (30, 30, 30), self.rect)
        p.draw.rect(
            self.screen, self.color if self.active else (120, 120, 120), self.rect, 2
        )
        self.screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + 10))

        # Bouton Confirmer
        col_bg = (55, 85, 155, 220) if self.btn_hovered else (28, 28, 50, 200)
        col_brd = (120, 150, 225, 255) if self.btn_hovered else (55, 55, 100, 255)
        btn_surf = p.Surface((self.btn_rect.width, self.btn_rect.height), p.SRCALPHA)
        p.draw.rect(
            btn_surf,
            col_bg,
            (0, 0, self.btn_rect.width, self.btn_rect.height),
            border_radius=8,
        )
        p.draw.rect(
            btn_surf,
            col_brd,
            (0, 0, self.btn_rect.width, self.btn_rect.height),
            width=2,
            border_radius=8,
        )
        self.screen.blit(btn_surf, self.btn_rect.topleft)

        label = self.font_hint.render("Confirmer", True, (240, 240, 255))
        self.screen.blit(
            label,
            (
                self.btn_rect.x + (self.btn_rect.width - label.get_width()) // 2,
                self.btn_rect.y + (self.btn_rect.height - label.get_height()) // 2,
            ),
        )

        # Pop-up erreur
        if self.error_timer > 0:
            alpha = int(255 * min(1.0, self.error_timer / (self.ERROR_DURATION * 0.3)))
            err_surf = self.font_hint.render(self.error_msg, True, (220, 80, 80))
            err_surf.set_alpha(alpha)
            self.screen.blit(
                err_surf,
                (
                    self.WINDOWS[0] // 2 - err_surf.get_width() // 2,
                    self.btn_rect.bottom + 14,
                ),
            )

        self.pagedisplay()
        self.declicked_all()


def get_all_saves(mode: str) -> List[Dict[str, str]] | List[str]:

    L = []
    list_file = []
    folder = (
        os.path.join(resource_path(r"save"), r"solo")
        if mode == "solo"
        else os.path.join(resource_path(r"save"), r"multiplayer")
    )

    for file in os.listdir(folder):
        list_file.append(file)
        with open(os.path.join(folder, file), "r", encoding="utf-8") as reader:
            data = json.loads(reader.read())
            L.append({"game_name": data["game_name"], "last_save": data["last_save"]})
    return L, list_file
