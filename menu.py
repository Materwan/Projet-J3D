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

if TYPE_CHECKING:
    from main import Manager

MENU_ASSET_DIRECTORY = "Ressources/UIAsset/"
BACKGROUND = MENU_ASSET_DIRECTORY + "fond ecran menu.png"
PLAY_BUTTON = MENU_ASSET_DIRECTORY + "PLAY.png"
SETTING_BUTTON = MENU_ASSET_DIRECTORY + "SETTINGS.png"
EXIT_BUTTON = MENU_ASSET_DIRECTORY + "EXIT.png"
EMPTY_BUTTON = MENU_ASSET_DIRECTORY + "EMPTY.png"
TITLE = MENU_ASSET_DIRECTORY + "logo.png"

SAVE_FILE = "save/"
SAVE_MULTI = SAVE_FILE + "multiplayer"
SAVE_SOLO = SAVE_FILE + "solo"

UDP_IP = "0.0.0.0"
UDP_PORT = 9999

p.font.init()


class Text:

    def __init__(
        self,
        name: str,
        size: int,
        text: str,
        t_color: Tuple[int, int, int],
        screen: p.Surface = None,
        antialias: bool = False,
    ):
        self.screen = screen
        self.caractere = text
        self.font = p.font.SysFont(name, size)
        self.text = self.font.render(text, antialias, t_color)
        self.lenth = self.text.get_size()

    def draw_text(self, coordonninate: Tuple[int, int]) -> None:
        """draw a text"""
        self.screen.blit(self.text, coordonninate)


class Menu:

    def __init__(self, screen: p.Surface, manager: "Manager"):
        self.elttexts = []
        self.eltpages = []
        self.WINDOWS = screen.get_size()
        self.half = (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2)
        self.screen = screen
        self.bg_img = p.image.load(BACKGROUND).convert()
        self.bg_img_coord = self.bg_img.get_rect()
        self.manager = manager
        self.keybinds = {
            "up": p.K_UP,
            "down": p.K_DOWN,
            "left": p.K_LEFT,
            "right": p.K_RIGHT,
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
        def retour(menu: str):
            self.retour.clicked = True
            self.retour.hover = False
            self.manager.change_state(menu)

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.retour, self.retour_t = create_button_with_text(
            EMPTY_BUTTON, self.screen, (170, 67), retour, "<--"
        )
        # =======================Button End=======================

    def recalculcoord(
        self, text: List | Text | Tuple[int, int], button: a.Button
    ) -> Tuple[int, int]:
        """recalcul the coordonnee"""
        return (
            (button.rec.width - text[0].lenth[0]) // 2 + button.rec.left,
            (button.rec.height - text[0].lenth[1]) // 2 + button.rec.top,
        )

    def change_button_text(
        self,
        changetext: List | Text | Tuple[int, int],
        button: a.Button,
        caractere: str,
    ) -> None:
        """change the text in a button"""
        changetext[0].text = changetext[0].font.render(caractere, False, (0, 0, 0))
        changetext[0].lenth = changetext[0].text.get_size()
        changetext[0].caractere = caractere
        changetext[1] = self.recalculcoord(changetext, button)

    def interchange(
        self,
        changetext: List | Text | Tuple[int, int],
        button: a.Button,
        direction: str,
        caractere: str,
        bool: bool,
    ) -> None:
        """change the texte of the button that you want to change the keybind"""
        self.change_button_text(changetext, button, caractere)
        self.key[direction] = bool

    def create_list_save_and_button(
        self, mode: str
    ) -> List | Tuple[a.Button, List | Text | Tuple[int, int]] | List[str]:
        list_button = []
        list_save = []

        def no_function():
            pass

        count = 0
        saves, files = get_all_saves(mode)
        for serveur in saves:
            button, button_t = create_button_with_text(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150),
                no_function,
                serveur.key(),
            )
            list_save.append(serveur)
            list_button.append((button, button_t))
            count += 1
        return list_button, files

    def pagedisplay(self) -> None:
        """draw the page"""
        for elt in self.eltpages:
            elt.display()

    def textdisplay(self) -> None:
        """draw the text"""
        for elt in self.elttexts:
            elt[0].draw_text(elt[1])

    def dehover_all(self) -> None:
        for button in self.eltpages:
            button.hover = False

    def declicked_all(self) -> None:
        for button in self.eltpages:
            button.clicked = False


class Principal_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def start():
            self.start.clicked = True
            self.manager.change_state("MENU_PLAY")

        def settings():
            self.settings.clicked = True
            self.manager.change_state("MENU_SETTING")

        def quit():
            self.quit.clicked = True
            self.manager.running = False

        def no_function():
            pass

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.start, _ = create_button_with_text(
            PLAY_BUTTON, self.screen, (self.half[0], self.half[1] - 100), start
        )
        self.settings, _ = create_button_with_text(
            SETTING_BUTTON,
            self.screen,
            (self.half[0], self.half[1] + 50),
            settings,
            "",
            0.8,
        )
        self.quit, _ = create_button_with_text(
            EXIT_BUTTON, self.screen, (self.half[0], self.half[1] + 200), quit
        )
        self.titre, _ = create_button_with_text(
            TITLE, self.screen, (self.half[0], self.half[1] // 3), no_function, "", 0.6
        )
        # =======================Button End=======================

        self.elttexts = []
        self.eltpages = [self.titre, self.start, self.settings, self.quit]

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                if self.quit.rec.collidepoint(coord):
                    self.quit.clicked_function()
                elif self.start.rec.collidepoint(coord):
                    self.start.clicked_function()
                elif self.settings.rec.collidepoint(coord):
                    self.settings.clicked_function()
            else:
                self.dehover_all()
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover = True
                elif self.start.rec.collidepoint(coord):
                    self.start.hover = True
                elif self.settings.rec.collidepoint(coord):
                    self.settings.hover = True

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.textdisplay()
        self.pagedisplay()
        self.declicked_all()


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
            self.retour.clicked_function(mode)

        def changeup():
            self.interchange(self.up_t, self.changeup, "up", "...", True)

        def changedown():
            self.interchange(self.down_t, self.changedown, "down", "...", True)

        def changeleft():
            self.interchange(self.left_t, self.changeleft, "left", "...", True)

        def changeright():
            self.interchange(self.right_t, self.changeright, "right", "...", True)

        def changeattack():
            self.interchange(self.attack_t, self.changeattack, "attack", "...", True)

        def volume(choise: bool):
            self.manager.change_volume(choise)

        def no_function():
            pass

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.changeup, self.up_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 - 70),
            changeup,
            "UP: " + p.key.name(self.keybinds["up"]),
        )
        self.changedown, self.down_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 + 70),
            changedown,
            "DOWN: " + p.key.name(self.keybinds["down"]),
        )
        self.changeleft, self.left_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70),
            changeleft,
            "LEFT: " + p.key.name(self.keybinds["left"]),
        )
        self.changeright, self.right_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            changeright,
            "RIGHT: " + p.key.name(self.keybinds["right"]),
        )
        self.changeattack, self.attack_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 + 200),
            changeattack,
            "ATTACK: " + p.key.name(self.keybinds["attack"]),
        )
        self.volume_up, self.volume_up_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 70),
            volume,
            "+",
        )
        self.volume_down, self.volume_down_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 + 70),
            volume,
            "-",
        )
        _, self.volume_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 180),
            no_function,
            "Sounds volume",
        )
        # =======================Button End=======================

        self.elttexts = [
            self.up_t,
            self.down_t,
            self.left_t,
            self.right_t,
            self.attack_t,
            self.volume_up_t,
            self.volume_down_t,
            self.volume_t,
            self.retour_t,
        ]
        self.eltpages = [
            self.changeup,
            self.changedown,
            self.changeleft,
            self.changeright,
            self.changeattack,
            self.volume_up,
            self.volume_down,
            self.retour,
        ]

    def changekey(self, event: p.event.Event) -> None:
        """take the last keybind to replace the old one"""
        for elt in self.key.keys():
            if self.key[elt]:
                if event.type == p.KEYDOWN:
                    if event.key != p.K_ESCAPE:
                        self.keybinds[elt] = event.key
                else:
                    self.keybinds[elt] = event.button
                self.key[elt] = False

    def checkchangekey(self) -> bool:
        """look if there is no other keybind that is being change"""
        for elt in self.key.keys():
            if self.key[elt]:
                return False
        return True

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN or event.type == p.MOUSEBUTTONDOWN:
                if (
                    event.type == p.KEYDOWN
                    and event.key == p.K_ESCAPE
                    and self.checkchangekey()
                ):
                    self.manager.states["GAME"].keybinds = self.keybinds
                    self.manager.change_state(self.menu_appel)
                self.changekey(event)  # try to change the keybind
                self.interchange(
                    self.up_t,
                    self.changeup,
                    "up",
                    "UP: " + p.key.name(self.keybinds["up"]),
                    False,
                )
                self.interchange(
                    self.down_t,
                    self.changedown,
                    "down",
                    "DOWN: " + p.key.name(self.keybinds["down"]),
                    False,
                )
                self.interchange(
                    self.left_t,
                    self.changeleft,
                    "left",
                    "LEFT: " + p.key.name(self.keybinds["left"]),
                    False,
                )
                self.interchange(
                    self.right_t,
                    self.changeright,
                    "right",
                    "RIGHT: " + p.key.name(self.keybinds["right"]),
                    False,
                )
                self.interchange(
                    self.attack_t,
                    self.changeattack,
                    "attack",
                    "ATTACK: " + p.key.name(self.keybinds["attack"]),
                    False,
                )
            if self.checkchangekey():
                """if a keybind is changing dont look for collidepoint"""
                if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                    if self.retour.rec.collidepoint(coord):
                        self.manager.states["GAME"].keybinds = self.keybinds
                        self.retour.clicked_function(self.menu_appel)
                    elif self.changeup.rec.collidepoint(coord):
                        self.changeup.clicked_function()
                    elif self.changedown.rec.collidepoint(coord):
                        self.changedown.clicked_function()
                    elif self.changeleft.rec.collidepoint(coord):
                        self.changeleft.clicked_function()
                    elif self.changeright.rec.collidepoint(coord):
                        self.changeright.clicked_function()
                    elif self.changeattack.rec.collidepoint(coord):
                        self.changeattack.clicked_function()
                    elif self.volume_up.rec.collidepoint(coord):
                        self.volume_up.clicked_function(True)
                    elif self.volume_down.rec.collidepoint(coord):
                        self.volume_up.clicked_function(False)
                else:
                    self.dehover_all()
                    if self.retour.rec.collidepoint(coord):
                        self.retour.hover = True
                    elif self.changeup.rec.collidepoint(coord):
                        self.changeup.hover = True
                    elif self.changedown.rec.collidepoint(coord):
                        self.changedown.hover = True
                    elif self.changeleft.rec.collidepoint(coord):
                        self.changeleft.hover = True
                    elif self.changeright.rec.collidepoint(coord):
                        self.changeright.hover = True
                    elif self.changeattack.rec.collidepoint(coord):
                        self.changeattack.hover = True
                    elif self.volume_up.rec.collidepoint(coord):
                        self.volume_up.hover = True
                    elif self.volume_down.rec.collidepoint(coord):
                        self.volume_down.hover = True

    def update(self) -> None:
        if (
            self.menu_appel != "MENU_P"
            and self.manager.states["GAME"].playing_mode != "solo"
        ):
            self.manager.states["GAME"].update()

    def display(self) -> None:
        if self.menu_appel == "MENU_P":
            self.screen.blit(self.bg_img, self.bg_img_coord)
        else:
            self.manager.states["GAME"].display()
            self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()
        self.textdisplay()
        self.declicked_all()


class Play_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def multiplayer():
            self.multiplayer.clicked = True
            self.multiplayer.hover = False
            self.manager.change_state("MENU_MULTIPLAYER")

        def solo():
            self.solo.clicked = True
            self.solo.hover = False
            self.manager.change_state("MENU_SOLO")

        def joinmultiplayer():
            self.joinmultiplayer.clicked = True
            self.joinmultiplayer.hover = False
            self.manager.states["MENU_MULTI"].udp_event.set()
            self.manager.change_state("MENU_MULTI")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.multiplayer, self.multiplayer_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            self.half,
            multiplayer,
            "MULTIPLAYER",
        )
        self.solo, self.solo_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            solo,
            "SOLO",
        )
        self.joinmultiplayer, self.joinmultiplayer_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            joinmultiplayer,
            "JOIN MULTIPLAYER",
        )
        # =======================Button End=======================

        self.elttexts = [
            self.solo_t,
            self.multiplayer_t,
            self.joinmultiplayer_t,
            self.retour_t,
        ]
        self.eltpages = [self.retour, self.solo, self.multiplayer, self.joinmultiplayer]

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.manager.change_state("MENU_P")
                if event.key == p.K_0:
                    self.manager.states["GAME"].load_save("save.json")
            if event.type == p.MOUSEBUTTONDOWN:
                if self.solo.rec.collidepoint(coord):
                    self.solo.clicked_function()
                elif self.multiplayer.rec.collidepoint(coord):
                    self.multiplayer.clicked_function()
                elif self.joinmultiplayer.rec.collidepoint(coord):
                    self.joinmultiplayer.clicked_function()
                elif self.retour.rec.collidepoint(coord):
                    self.retour.clicked_function("MENU_P")
            else:
                self.dehover_all()
                if self.solo.rec.collidepoint(coord):
                    self.solo.hover = True
                elif self.multiplayer.rec.collidepoint(coord):
                    self.multiplayer.hover = True
                elif self.joinmultiplayer.rec.collidepoint(coord):
                    self.joinmultiplayer.hover = True
                elif self.retour.rec.collidepoint(coord):
                    self.retour.hover = True

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.textdisplay()
        self.declicked_all()


class Join_Multi_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.serveurs_save = 0
        self.list_button = []
        self.manager.running = True
        self.serveurs = {}
        self.serveurs: Dict[Dict]
        self.upd_prot = threading.Thread(target=self.recieve_udp)
        self.udp_event = threading.Event()
        self.upd_prot.start()

        # =======================Function Button Start=======================
        def retour(mode: str):
            self.udp_event.clear()
            self.retour.clicked_function(mode)

        # =======================Function Button End=======================

        self.elttexts = [self.retour_t]
        self.eltpages = [self.retour]

    def initialize_udp(self) -> None:

        self.upd_func = asyncio.run(self.recieve_udp())

    def recieve_udp(self) -> None:

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

                    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                    data = json.loads(data.decode().strip())
                    if addr[0] not in self.serveurs:
                        self.serveurs[addr[0]] = data
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

    def create_list_button(self) -> None:
        self.list_button = []

        def no_function():
            pass

        count = 0
        for serveur in self.serveurs.keys():
            button, button_t = create_button_with_text(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150),
                no_function,
                serveur,
            )
            self.list_button.append((button, button_t))
            count += 1

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.udp_event.clear()
                    self.manager.change_state("MENU_PLAY")
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                if self.retour.rec.collidepoint(coord):
                    self.udp_event.clear()
                    self.retour.clicked_function("MENU_PLAY")
                else:
                    for elt in self.list_button:
                        if elt[0].rec.collidepoint(coord):
                            elt[0].clicked = True
                            elt[0].hover = False
                            self.udp_event.clear()
                            self.manager.states["GAME"].playing_mode = "guest"
                            self.manager.states["GAME"].address = elt[1][0].caractere
                            self.manager.change_state("GAME")
                            self.manager.state.initialize()
                            break
            else:
                self.dehover_all()
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True
                else:
                    for elt in self.list_button:
                        if elt[0].rec.collidepoint(coord):
                            elt[0].hover = True
                            break

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.screen.blit(self.bg_img, self.bg_img_coord)
        if len(self.serveurs) != self.serveurs_save:
            self.serveurs_save = len(self.serveurs)
            self.eltpages = [self.retour]
            self.elttexts = [self.retour_t]
            self.create_list_button()
            for elt in self.list_button:
                self.eltpages.append(elt[0])
                self.elttexts.append(elt[1])
        self.pagedisplay()
        self.textdisplay()
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
        self.manager.running = True

        # =======================Function Button Start=======================
        def resume():
            self.resume.clicked = True
            self.resume.hover = False
            self.manager.change_state("GAME")

        def save():
            self.save.clicked = True
            self.save.hover = False
            if self.manager.states["GAME"].playing_mode == "solo":
                self.manager.states["GAME"].save(
                    SAVE_SOLO + "/save_" + str(self.nbr_file_solo)
                )
            else:
                self.manager.states["GAME"].save(
                    SAVE_MULTI + "/save_" + str(self.nbr_file_multi)
                )

        def settings():
            self.settings.clicked = True
            self.settings.hover = False
            self.manager.states["MENU_SETTING_PAUSE"].keybinds = self.manager.states[
                "GAME"
            ].keybinds
            self.manager.change_state("MENU_SETTING_PAUSE")

        def quit():
            self.quit.clicked = True
            self.quit.hover = False
            game = self.manager.states["GAME"]
            if isinstance(game.player_controller, GuestController):
                game._send_close_and_disconnect()
            game.close_network()
            game.reset()
            self.manager.change_state("MENU_P")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.resume, self.resume_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 220),
            resume,
            "RESUME",
        )
        self.save, self.save_t = create_button_with_text(
            EMPTY_BUTTON, self.screen, (self.half[0], self.half[1] - 70), save, "SAVE"
        )
        self.settings, _ = create_button_with_text(
            SETTING_BUTTON,
            self.screen,
            (self.half[0], self.half[1] + 70),
            settings,
            "",
            0.8,
        )
        self.quit, _ = create_button_with_text(
            EXIT_BUTTON, self.screen, (self.half[0], self.half[1] + 220), quit
        )
        # =======================Button End=======================

        self.eltpages = [self.resume, self.save, self.settings, self.quit]
        self.elttexts = [self.resume_t, self.save_t]

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                if self.quit.rec.collidepoint(coord):
                    self.quit.clicked_function()
                elif self.resume.rec.collidepoint(coord):
                    self.resume.clicked_function()
                elif self.settings.rec.collidepoint(coord):
                    self.settings.clicked_function()
                elif self.save.rec.collidepoint(coord):
                    self.save.clicked_function()
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.resume.clicked_function()
            else:
                self.dehover_all()
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover = True
                elif self.resume.rec.collidepoint(coord):
                    self.resume.hover = True
                elif self.settings.rec.collidepoint(coord):
                    self.settings.hover = True
                elif self.save.rec.collidepoint(coord):
                    self.save.hover = True

    def update(self) -> None:
        if self.manager.states["GAME"].playing_mode != "solo":
            self.manager.states["GAME"].update()

    def display(self) -> None:
        self.manager.states["GAME"].display()
        self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()
        self.textdisplay()
        self.declicked_all()


class Solo_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def create():
            self.create.clicked = True
            self.create.hover = False
            self.nbr_file_solo += 1
            self.manager.states["GAME"].playing_mode = "solo"
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        def no_function():
            pass

        # =======================Function Button End=======================

        # =======================Button Start=======================
        _, self.solo_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            no_function,
            "SOLO",
            1,
            100,
        )
        self.create, self.create_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            create,
            "CREATE",
        )
        self.list_button, self.list_file = self.create_list_save_and_button("solo")
        self.len_list = len(self.list_button)
        # =======================Button End=======================

        self.eltpages = [self.retour, self.create]
        self.elttexts = [self.retour_t, self.solo_t, self.create_t]
        for elt in self.list_button:
            self.eltpages.append(elt[0])
            self.elttexts.append(elt[1])

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.manager.change_state("MENU_PLAY")
            if event.type == p.MOUSEBUTTONDOWN:
                if self.retour.rec.collidepoint(coord):
                    self.retour.clicked_function("MENU_PLAY")
                    """if self.solo.rec.collidepoint(coord):
                    self.solo.clicked = True
                    self.solo.hover = False
                    self.manager.states["GAME"].playing_mode = "solo"
                    self.manager.change_state("GAME")
                    self.manager.state.initialize()"""
                elif self.create.rec.collidepoint(coord):
                    self.create.clicked_function()
                    """self.multiplayer.clicked = True
                    self.multiplayer.hover = False
                    self.manager.states["GAME"].playing_mode = "host"
                    self.manager.change_state("GAME")
                    self.manager.state.initialize()"""
                else:
                    for ind in range(self.len_list):
                        if self.list_button[ind][0].rec.collidepoint(coord):
                            self.list_button[ind][0].clicked = True
                            self.list_button[ind][0].hover = False
                            self.manager.states["GAME"].playing_mode = "solo"
                            self.manager.states["GAME"].game.load(self.list_file)
                            self.manager.change_state("GAME")
                            self.manager.state.initialize()
                            break
            else:
                self.dehover_all()
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True
                elif self.create.rec.collidepoint(coord):
                    self.create.hover = True
                else:
                    for elt in self.list_button:
                        if elt[0].rec.collidepoint(coord):
                            elt[0].hover = True
                            break

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.textdisplay()
        self.declicked_all()


class Multiplayer_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def create():
            self.create.clicked = True
            self.create.hover = False
            self.nbr_file_multi += 1
            self.manager.states["GAME"].playing_mode = "host"
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        def no_function():
            pass

        # =======================Function Button End=======================

        # =======================Button Start=======================
        _, self.multiplayer_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            no_function,
            "MULTIPLAYER",
            1,
            100,
        )
        self.create, self.create_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            create,
            "CREATE",
        )
        self.list_button, self.list_file = self.create_list_save_and_button(
            "multiplayer"
        )
        self.len_list = len(self.list_button)
        # =======================Button End=======================

        self.eltpages = [self.retour, self.create]
        self.elttexts = [self.retour_t, self.multiplayer_t, self.create_t]
        for elt in self.list_button:
            self.eltpages.append(elt[0])
            self.elttexts.append(elt[1])

    def event(self, events: list[p.event.Event]) -> None:
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.manager.change_state("MENU_PLAY")
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                if self.retour.rec.collidepoint(coord):
                    self.retour.clicked_function("MENU_PLAY")
                elif self.create.rec.collidepoint(coord):
                    self.create.clicked_function()
                    """elif self.mode_jeu.rec.collidepoint(coord):
                    self.mode_jeu.clicked = True
                    self.mode_jeu.hover = False
                    if self.mode_jeu_t[0].caractere == "SOLO":
                        self.change_button_text(
                            self.mode_jeu_t, self.mode_jeu, "MULTIPLAYER"
                        )
                    else:
                        self.change_button_text(
                            self.mode_jeu_t, self.mode_jeu, "SOLO"
                        )"""
                else:
                    for ind in range(self.len_list):
                        if self.list_button[ind][0].rec.collidepoint(coord):
                            self.list_button[ind][0].clicked = True
                            self.list_button[ind][0].hover = False
                            self.manager.states["GAME"].playing_mode = "multiplayer"
                            self.manager.states["GAME"].game.load(self.list_file)
                            self.manager.change_state("GAME")
                            self.manager.state.initialize()
                            break
            else:
                self.dehover_all()
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True
                elif self.create.rec.collidepoint(coord):
                    self.create.hover = True
                else:
                    for elt in self.list_button:
                        if elt[0].rec.collidepoint(coord):
                            elt[0].hover = True
                            break

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.textdisplay()
        self.declicked_all()


class Death_Screen(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def no_function():
            pass

        # =======================Function Button End=======================

        # =======================Button Start=======================
        _, self.death_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            no_function,
            "Game Over",
            1,
            150,
        )
        _, self.death2_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 200),
            no_function,
            "Press any keybind to continu",
            1,
            50,
        )
        # =======================Button End=======================

        self.elttexts = [self.death_t, self.death2_t]
        self.eltpages = []

    def event(self, events: list[p.event.Event]) -> None:
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN or event.type == p.MOUSEBUTTONDOWN:
                self.manager.change_state("MENU_P")

    def update(self) -> None:
        pass

    def display(self) -> None:
        self.manager.states["GAME"].display()
        self.screen.blit(self.blackscreen, (0, 0))
        self.textdisplay()


def create_button_with_text(
    image: str,
    screen: p.Surface,
    pos: Tuple | List,
    function_event,
    text_str: str | None = "",
    scale: int | None = 1,
    text_size: int | None = 30,
) -> Tuple[a.Button, List | Text | Tuple[int, int]]:
    button = a.Button(image, screen, pos, function_event, scale=scale)
    text = Text("Impact", text_size, text_str, (0, 0, 0), screen)
    coord = (
        (button.rec.width - text.lenth[0]) // 2 + button.rec.left,
        (button.rec.height - text.lenth[1]) // 2 + button.rec.top,
    )
    return button, [text, coord]


def get_all_saves(mode: str) -> List[Dict[str, str]] | List[str]:

    L = []
    list_file = []
    folder = r"save" + r"\solo" if mode == "solo" else r"save" + r"\multiplayer"

    for file in os.listdir(folder):
        list_file.append(file)
        with open(file, "r") as reader:
            data = json.loads(reader.read())
            L.append({"game_name": data["game_name"], "last_save": data["last_save"]})
    return L, list_file
