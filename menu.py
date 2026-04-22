from typing import List, Dict, Tuple, Callable, TYPE_CHECKING
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

MENU_ASSET_DIRECTORY = "Ressources/UI_&_élements_graphiques/"
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


class Menu:

    def __init__(self, screen: p.Surface, manager: "Manager"):
        self.eltpages = []
        self.list_file = []
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
        def retour(mode: str):
            self.manager.change_state(mode)

        def reprendre(mode: str):
            self.manager.states["GAME"].playing_mode = mode
            self.manager.states["GAME"].game.load(self.list_file)
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        def no_function():
            pass

        self.reprendre = reprendre
        self.no_function = no_function
        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.retour = a.Button(EMPTY_BUTTON, self.screen, (170, 67), retour, text="<--")
        # =======================Button End=======================

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

    def create_list_save_and_button(self, mode: str):
        list_button = []
        list_save = []
        count = 0
        saves, files = get_all_saves(mode)
        for serveur in saves:
            button = a.Button(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150),
                self.reprendre,
                text=serveur["game_name"],
            )
            list_save.append(serveur)
            list_button.append(button)
            count += 1
        return list_button, files

    def pagedisplay(self):
        for elt in self.eltpages:
            elt.display()

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

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.retour.clicked_function = retour
        self.changeup = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 - 70),
            changeup,
            text="UP: " + p.key.name(self.keybinds["up"]),
        )
        self.changedown = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 400, self.WINDOWS[1] // 2 + 70),
            changedown,
            text="DOWN: " + p.key.name(self.keybinds["down"]),
        )
        self.changeleft = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70),
            changeleft,
            text="LEFT: " + p.key.name(self.keybinds["left"]),
        )
        self.changeright = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            changeright,
            text="RIGHT: " + p.key.name(self.keybinds["right"]),
        )
        self.changeattack = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 + 200),
            changeattack,
            text="ATTACK: " + p.key.name(self.keybinds["attack"]),
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
        self.volume = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 400, self.WINDOWS[1] // 2 - 180),
            self.no_function,
            text="Sounds volume",
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
            self.volume,
            self.retour,
        ]

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
                        "UP: " + p.key.name(self.keybinds["up"]),
                        self.changeup,
                        "up",
                        False,
                    )
                    self.interchange(
                        "DOWN: " + p.key.name(self.keybinds["down"]),
                        self.changedown,
                        "down",
                        False,
                    )
                    self.interchange(
                        "LEFT: " + p.key.name(self.keybinds["left"]),
                        self.changeleft,
                        "left",
                        False,
                    )
                    self.interchange(
                        "RIGHT: " + p.key.name(self.keybinds["right"]),
                        self.changeright,
                        "right",
                        False,
                    )
                    self.interchange(
                        "ATTACK: " + p.key.name(self.keybinds["attack"]),
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
            text="MULTIPLAYER",
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
            text="JOIN MULTIPLAYER",
        )
        # =======================Button End=======================

        self.eltpages = [self.retour, self.solo, self.multiplayer, self.joinmultiplayer]

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
            self.manager.change_state(mode)

        def rejoindre(address: str):
            self.udp_event.clear()
            self.manager.states["GAME"].playing_mode = "guest"
            self.manager.states["GAME"].address = address
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        self.rejoindre = rejoindre
        self.retour.clicked_function = retour
        # =======================Function Button End=======================

        self.eltpages = [self.retour]

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
                        sock.settimeout(0.5)
                        sock.bind(("", UDP_PORT))
                        print("UDP recieve protocol start")

                    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                    data = data.decode().strip()
                    data = json.loads(data)
                    if addr[0] not in self.serveurs:
                        self.serveurs[addr[0]] = data
                else:
                    if sock_set:
                        sock_set = False
                        sock.close()
                        print("UDP recieve protocol stopped")
                    time.sleep(0.5)
            except socket.timeout:
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
                text=serveur.keys(),
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
            elt.event(events, coord, elt.text)

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        if len(self.serveurs) != self.serveurs_save:
            self.serveurs_save = len(self.serveurs)
            self.create_list_button()
            self.eltpages = self.list_button
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
        self.manager.running = True

        # =======================Function Button Start=======================
        def resume():
            self.manager.change_state("GAME")

        def save():
            if self.manager.states["GAME"].playing_mode == "solo":
                self.manager.states["GAME"].save(
                    SAVE_SOLO + "/save_" + str(self.nbr_file_solo)
                )
            else:
                self.manager.states["GAME"].save(
                    SAVE_MULTI + "/save_" + str(self.nbr_file_multi)
                )

        def settings():
            self.manager.states["MENU_SETTING_PAUSE"].keybinds = self.manager.states[
                "GAME"
            ].keybinds
            self.manager.change_state("MENU_SETTING_PAUSE")

        def quit():
            self.manager.states["GAME"].player_controller.close = True
            self.manager.change_state("MENU_P")

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.resume = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 220),
            resume,
            text="RESUME",
        )
        self.save = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 70),
            save,
            text="SAVE",
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

    def update(self):
        if self.manager.states["GAME"].playing_mode != "solo":
            self.manager.states["GAME"].update()

    def display(self):
        self.manager.states["GAME"].display()
        self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()
        self.declicked_all()


class Solo_Menu(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        def create():
            self.nbr_file_solo += 1
            self.manager.states["GAME"].playing_mode = "solo"
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.solo = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            self.no_function,
            text="SOLO",
            text_size=100,
        )
        self.create = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            create,
            text="CREATE",
        )
        self.list_button, self.list_file = self.create_list_save_and_button("solo")
        # =======================Button End=======================

        self.eltpages = [self.retour, self.solo, self.create]
        for elt in self.list_button:
            self.eltpages.append(elt)

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.manager.change_state("MENU_PLAY")
        self.retour.event(events, coord, "MENU_PLAY")
        self.create.event(events, coord)
        for elt in self.list_button:
            elt.event(events, coord, "solo")

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
            self.nbr_file_multi += 1
            self.manager.states["GAME"].playing_mode = "host"
            self.manager.change_state("GAME")
            self.manager.state.initialize()

        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.multiplayer = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 10),
            self.no_function,
            text="MULTIPLAYER",
            text_size=100,
        )
        self.create = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            create,
            text="CREATE",
        )
        self.list_button, self.list_file = self.create_list_save_and_button(
            "multiplayer"
        )
        # =======================Button End=======================

        self.eltpages = [self.retour, self.multiplayer, self.create]
        for elt in self.list_button:
            self.eltpages.append(elt)

    def event(self, events: list[p.event.Event]):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.manager.change_state("MENU_PLAY")
        self.retour.event(events, coord, "MENU_PLAY")
        self.create.event(events, coord)
        for elt in self.list_button:
            elt.event(events, coord, "multiplayer")

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.declicked_all()


class Death_Screen(Menu):

    def __init__(self, screen: p.Surface, manager: "Manager"):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Function Button Start=======================
        # =======================Function Button End=======================

        # =======================Button Start=======================
        self.death = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            self.no_function,
            text="Game Over",
            text_size=150,
        )
        self.death2 = a.Button(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 200),
            self.no_function,
            text="Press any keybind to continu",
            text_size=50,
        )
        # =======================Button End=======================

        self.eltpages = [self.death, self.death2]

    def event(self, events: list[p.event.Event]):
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN or event.type == p.MOUSEBUTTONDOWN:
                self.manager.change_state("MENU_P")

    def update(self):
        pass

    def display(self):
        self.manager.states["GAME"].display()
        self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()


def get_all_saves(mode: str) -> List[Dict[str, str]] | List[str]:

    L = []
    list_file = []
    folder = r"save" + r"\solo" if mode == "solo" else r"save" + r"\multiplayer"

    for file in os.listdir(folder):
        list_file.append(file)
        with open(os.path.join(folder, file), "r", encoding="utf-8") as reader:
            data = json.loads(reader.read())
            L.append({"game_name": data["game_name"], "last_save": data["last_save"]})
    return L, list_file
