import pygame as p
import animations as a
from typing import List, Dict
import threading
import socket
import json
import asyncio

EMPTY_BUTTON = "Ressources/UI_&_élements_graphiques/"
UDP_IP = "0.0.0.0"
UDP_PORT = 9999

p.font.init()
p.mixer.init()

p.mixer.music.load("Ressources/Musics/placeholder.mp3")
p.mixer.music.play(-1)


class Text:

    def __init__(self, name, size, text, t_color, screen=None, antialias=False):
        self.screen = screen
        self.font = p.font.SysFont(name, size)
        self.text = self.font.render(text, antialias, t_color)
        self.l = self.text.get_size()

    def draw_text(self, coordonninate):
        """draw a text"""
        self.screen.blit(self.text, coordonninate)


class Menu:

    def __init__(self, screen, manager):
        self.WINDOWS = screen.get_size()
        self.screen = screen
        self.bg_img = p.image.load(EMPTY_BUTTON + "fond ecran menu.png")
        self.manager = manager
        self.keybinds = {
            "up": p.K_UP,
            "down": p.K_DOWN,
            "left": p.K_LEFT,
            "right": p.K_RIGHT,
        }
        self.key = {"up": False, "down": False, "left": False, "right": False}
        self.manager.running = False

    def changekey(self, event):
        """take the last keybind to replace the old one"""
        for elt in self.key.keys():
            if self.key[elt]:
                if event.key != p.K_ESCAPE:
                    self.keybinds[elt] = event.key
                self.key[elt] = False

    def checkchangekey(self):
        """look if there is no other keybind that is being change"""
        for elt in self.key.keys():
            if self.key[elt]:
                return False
        return True

    def recalculcoord(self, text, button):
        """recalcul the coordonnee"""
        return (
            (button.rec.width - text[0].l[0]) // 2 + button.rec.left,
            (button.rec.height - text[0].l[1]) // 2 + button.rec.top,
        )

    def interchange(self, changetext, button, direction, caractere, bool):
        """change the texte of the button that you want to change the keybind"""
        changetext[0].text = changetext[0].font.render(caractere, False, (0, 0, 0))
        changetext[0].l = changetext[0].text.get_size()
        changetext[1] = self.recalculcoord(changetext, button)
        self.key[direction] = bool

    def pagedisplay(self, eltpages):
        """draw the page"""
        for elt in eltpages:
            elt.display()

    def textdisplay(self, elttexts):
        """draw the text"""
        for elt in elttexts:
            elt[0].draw_text(elt[1])


class Principal_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.manager.running = True
        self.start = a.Button(
            EMPTY_BUTTON + "PLAY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            (301, 95),
        )
        self.settings = a.Button(
            EMPTY_BUTTON + "SETTINGS.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            (497 * 0.80, 184 * 0.80),
        )
        self.quit = a.Button(
            EMPTY_BUTTON + "EXIT.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            (322 * 0.97, 82 * 0.97),
        )
        self.titre = [Text("Impact", 150, "Mole Tale", (255, 255, 255), self.screen)]
        self.titre.append(((self.WINDOWS[0] - self.titre[0].l[0]) // 2, 0))

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN:
                if self.quit.rec.collidepoint(coord):
                    self.quit.clicked = True
                    self.manager.running = False
                elif self.start.rec.collidepoint(coord):
                    self.start.clicked = True
                    self.manager.change_state("MENU_PLAY")
                elif self.settings.rec.collidepoint(coord):
                    self.settings.clicked = True
                    self.manager.change_state("MENU_SETTING")
            else:
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        True,
                        False,
                        False,
                    )
                elif self.start.rec.collidepoint(coord):
                    self.start.hover, self.quit.hover = True, False
                elif self.settings.rec.collidepoint(coord):
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        False,
                        False,
                        True,
                    )
                else:
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        False,
                        False,
                        False,
                    )

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())
        super().textdisplay([self.titre])
        super().pagedisplay([self.start, self.settings, self.quit])
        self.start.clicked = False
        self.settings.clicked = False
        self.quit.clicked = False


class Setting_Menu(Menu):

    def __init__(self, screen, manager, menu_appel="MENU_P"):
        super().__init__(screen, manager)
        self.manager.running = True
        self.surface_copie = None
        self.menu_appel = menu_appel
        self.retour = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (170, 67),
            (301, 95),
        )
        self.changeup = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 210),
            (301, 95),
        )
        self.changedown = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70),
            (301, 95),
        )
        self.changeleft = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            (301, 95),
        )
        self.changeright = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 210),
            (301, 95),
        )
        self.up_t = [
            Text(
                "Impact",
                30,
                "UP: " + p.key.name(self.keybinds["up"]),
                (0, 0, 0),
                self.screen,
            )
        ]
        self.up_t.append(
            (
                (self.changeup.rec.width - self.up_t[0].l[0]) // 2
                + self.changeup.rec.left,
                (self.changeup.rec.height - self.up_t[0].l[1]) // 2
                + self.changeup.rec.top,
            )
        )
        self.down_t = [
            Text(
                "Impact",
                30,
                "DOWN: " + p.key.name(self.keybinds["down"]),
                (0, 0, 0),
                self.screen,
            )
        ]
        self.down_t.append(
            (
                (self.changedown.rec.width - self.down_t[0].l[0]) // 2
                + self.changedown.rec.left,
                (self.changedown.rec.height - self.down_t[0].l[1]) // 2
                + self.changedown.rec.top,
            )
        )
        self.left_t = [
            Text(
                "Impact",
                30,
                "LEFT: " + p.key.name(self.keybinds["left"]),
                (0, 0, 0),
                self.screen,
            )
        ]
        self.left_t.append(
            (
                (self.changeleft.rec.width - self.left_t[0].l[0]) // 2
                + self.changeleft.rec.left,
                (self.changeleft.rec.height - self.left_t[0].l[1]) // 2
                + self.changeleft.rec.top,
            )
        )
        self.right_t = [
            Text(
                "Impact",
                30,
                "RIGHT: " + p.key.name(self.keybinds["right"]),
                (0, 0, 0),
                self.screen,
            )
        ]
        self.right_t.append(
            (
                (self.changeright.rec.width - self.right_t[0].l[0]) // 2
                + self.changeright.rec.left,
                (self.changeright.rec.height - self.right_t[0].l[1]) // 2
                + self.changeright.rec.top,
            )
        )
        self.retour_t = [Text("Impact", 30, "<--", (0, 0, 0), self.screen)]
        self.retour_t.append(
            (
                (self.retour.rec.width - self.retour_t[0].l[0]) // 2
                + self.retour.rec.left,
                (self.retour.rec.height - self.retour_t[0].l[1]) // 2
                + self.retour.rec.top,
            )
        )

    def changekey(self, event):
        """take the last keybind to replace the old one"""
        for elt in self.key.keys():
            if self.key[elt]:
                if event.key != p.K_ESCAPE:
                    self.keybinds[elt] = event.key
                self.key[elt] = False

    def checkchangekey(self):
        """look if there is no other keybind that is being change"""
        for elt in self.key.keys():
            if self.key[elt]:
                return False
        return True

    def interchange(self, changetext, button, direction, caractere, bool):
        """change the texte of the button that you want to change the keybind"""
        changetext[0].text = changetext[0].font.render(caractere, False, (0, 0, 0))
        changetext[0].l = changetext[0].text.get_size()
        changetext[1] = super().recalculcoord(changetext, button)
        self.key[direction] = bool

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE and self.checkchangekey():
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
            if self.checkchangekey():
                """if a keybind is changing dont look for collidepoint"""
                (
                    self.retour.hover,
                    self.changeup.hover,
                    self.changedown.hover,
                    self.changeleft.hover,
                    self.changeright.hover,
                ) = (False, False, False, False, False)
                checkevent = event.type == p.MOUSEBUTTONDOWN
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True
                    if checkevent:
                        self.retour.hover = False
                        self.manager.states["GAME"].keybinds = self.keybinds
                        self.manager.change_state(self.menu_appel)
                elif self.changeup.rec.collidepoint(coord):
                    self.changeup.hover = True
                    if checkevent:
                        self.interchange(self.up_t, self.changeup, "up", "...", True)
                elif self.changedown.rec.collidepoint(coord):
                    self.changedown.hover = True
                    if checkevent:
                        self.interchange(
                            self.down_t, self.changedown, "down", "...", True
                        )
                elif self.changeleft.rec.collidepoint(coord):
                    self.changeleft.hover = True
                    if checkevent:
                        self.interchange(
                            self.left_t, self.changeleft, "left", "...", True
                        )
                elif self.changeright.rec.collidepoint(coord):
                    self.changeright.hover = True
                    if checkevent:
                        self.interchange(
                            self.right_t, self.changeright, "right", "...", True
                        )

    def update(self):
        pass

    def display(self):
        if self.menu_appel == "MENU_P":
            self.screen.blit(self.bg_img, self.bg_img.get_rect())
        else:
            self.screen.blit(self.surface_copie, (0, 0))
        super().pagedisplay(
            [
                self.retour,
                self.changeup,
                self.changedown,
                self.changeleft,
                self.changeright,
            ]
        )
        super().textdisplay(
            [self.up_t, self.down_t, self.left_t, self.right_t, self.retour_t]
        )


class Play_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.manager.running = True
        self.retour = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (170, 67),
            (301, 95),
        )
        self.solo = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            (301, 95),
        )
        self.multiplayer = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            (301, 95),
        )
        self.joinmultiplayer = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            (301, 95),
        )
        self.solo_t = [
            Text(
                "Impact",
                30,
                "SOLO",
                (0, 0, 0),
                self.screen,
            )
        ]
        self.solo_t.append(
            (
                (self.solo.rec.width - self.solo_t[0].l[0]) // 2 + self.solo.rec.left,
                (self.solo.rec.height - self.solo_t[0].l[1]) // 2 + self.solo.rec.top,
            )
        )
        self.multiplayer_t = [
            Text(
                "Impact",
                30,
                "MULTIPLAYER",
                (0, 0, 0),
                self.screen,
            )
        ]
        self.multiplayer_t.append(
            (
                (self.multiplayer.rec.width - self.multiplayer_t[0].l[0]) // 2
                + self.multiplayer.rec.left,
                (self.multiplayer.rec.height - self.multiplayer_t[0].l[1]) // 2
                + self.multiplayer.rec.top,
            )
        )
        self.joinmultiplayer_t = [
            Text(
                "Impact",
                30,
                "JOIN MULTIPLAYER",
                (0, 0, 0),
                self.screen,
            )
        ]
        self.joinmultiplayer_t.append(
            (
                (self.joinmultiplayer.rec.width - self.joinmultiplayer_t[0].l[0]) // 2
                + self.joinmultiplayer.rec.left,
                (self.joinmultiplayer.rec.height - self.joinmultiplayer_t[0].l[1]) // 2
                + self.joinmultiplayer.rec.top,
            )
        )
        self.retour_t = [Text("Impact", 30, "<--", (0, 0, 0), self.screen)]
        self.retour_t.append(
            (
                (self.retour.rec.width - self.retour_t[0].l[0]) // 2
                + self.retour.rec.left,
                (self.retour.rec.height - self.retour_t[0].l[1]) // 2
                + self.retour.rec.top,
            )
        )

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.manager.change_state("MENU_P")
            if event.type == p.MOUSEBUTTONDOWN:
                if self.solo.rec.collidepoint(coord):
                    self.solo.clicked = True
                    p.mixer.music.stop()
                    self.solo.hover = False
                    self.manager.states["GAME"].playing_mode = "solo"
                    self.manager.change_state("GAME")
                elif self.multiplayer.rec.collidepoint(coord):
                    self.multiplayer.clicked = True
                    p.mixer.music.stop()
                    self.multiplayer.hover = False
                    self.manager.states["GAME"].playing_mode = "host"
                    self.manager.change_state("GAME")
                elif self.joinmultiplayer.rec.collidepoint(coord):
                    self.joinmultiplayer.clicked = True
                    self.joinmultiplayer.hover = False
                    # self.manager.states["GAME"].playing_mode = "guest"
                    # self.manager.change_state("GAME")
                    self.manager.states["MENU_MULTI"].udp_event.set()
                    self.manager.change_state("MENU_MULTI")
                elif self.retour.rec.collidepoint(coord):
                    self.retour.clicked = True
                    self.retour.hover = False
                    self.manager.change_state("MENU_P")
            else:
                (
                    self.solo.hover,
                    self.multiplayer.hover,
                    self.joinmultiplayer.hover,
                    self.retour.hover,
                ) = (False, False, False, False)
                if self.solo.rec.collidepoint(coord):
                    self.solo.hover = True
                elif self.multiplayer.rec.collidepoint(coord):
                    self.multiplayer.hover = True
                elif self.joinmultiplayer.rec.collidepoint(coord):
                    self.joinmultiplayer.hover = True
                elif self.retour.rec.collidepoint(coord):
                    self.retour.hover = True

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())
        super().pagedisplay(
            [self.retour, self.solo, self.multiplayer, self.joinmultiplayer]
        )
        super().textdisplay(
            [self.solo_t, self.multiplayer_t, self.joinmultiplayer_t, self.retour_t]
        )
        (
            self.retour.clicked,
            self.solo.clicked,
            self.multiplayer.clicked,
            self.joinmultiplayer.clicked,
        ) = (False, False, False, False)


class Join_Multi_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.list_button = []
        self.manager.running = True
        self.retour = a.Button(
            EMPTY_BUTTON + "EMPTY.png",
            self.screen,
            (170, 67),
            (301, 95),
        )
        """
        Un dictionnaire ou les clé sont les addresses ip et les valeurs sont un dictionnaire contennant le nom de la partie et l'addresses :
        <une ip>: {
            "Game name": <le nom de la partie>,
            "Port": <port pour se connecter>
        }
        <une autre ip>: {
            "Game name": <le nom de la partie>,
            "Port": <port pour se connecter>
        }
        .
        .
        .
        """
        self.serveurs = {}
        self.serveurs: Dict[Dict]
        self.retour_t = [Text("Impact", 30, "<--", (0, 0, 0), self.screen)]
        self.retour_t.append(
            (
                (self.retour.rec.width - self.retour_t[0].l[0]) // 2
                + self.retour.rec.left,
                (self.retour.rec.height - self.retour_t[0].l[1]) // 2
                + self.retour.rec.top,
            )
        )

        self.upd_prot = threading.Thread(target=self.recieve_udp)
        self.udp_event = threading.Event()
        self.upd_prot.start()

    def initialize_udp(self):

        self.upd_func = asyncio.run(self.recieve_udp())

    def recieve_udp(self):

        sock_set = False
        sock = None

        while self.manager.running:

            try:
                if self.udp_event.is_set():
                    if not sock_set:
                        sock = socket.socket(
                            socket.AF_INET, socket.SOCK_DGRAM
                        )  # Internet  # UDP
                        sock.bind((UDP_IP, UDP_PORT))
                        sock.settimeout(0.5)
                        sock_set = True
                        print("UDP recieve protocol start")

                    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                    data = data.decode().strip()
                    data = json.loads(data)
                    if addr[0] not in self.serveurs:
                        self.serveurs[addr[0]] = data
                        print(self.serveurs)
            except socket.timeout:
                continue

        print("UDP recieve protocol stopped")
        if sock:
            sock.close()

    def create_list_button(self, serveurs):
        self.list_button = []
        count = 0
        for serveur in serveurs.keys():
            button = a.Button(
                EMPTY_BUTTON + "EMPTY.png",
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 100),
                (301, 95),
            )
            button_t = [
                Text(
                    "Impact",
                    30,
                    serveur,
                    (0, 0, 0),
                    self.screen,
                )
            ]
            button_t.append(
                (
                    (button.rec.width - button_t[0].l[0]) // 2 + button.rec.left,
                    (button.rec.height - button_t[0].l[1]) // 2 + button.rec.top,
                )
            )
            self.list_button.append((button, button_t))

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    self.udp_event.clear()
                    self.manager.change_state("MENU_PLAY")
            if event.type == p.MOUSEBUTTONDOWN:
                if self.retour.rec.collidepoint(coord):
                    self.retour.clicked = True
                    self.retour.hover = False
                    self.udp_event.clear()
                    self.manager.change_state("MENU_PLAY")
            else:
                self.retour.hover = False
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())
        super().pagedisplay([self.retour])
        super().textdisplay([self.retour_t])
        self.create_list_button(self.serveurs)
        for elt in self.list_button:
            super().pagedisplay([elt[0]])
            super().textdisplay([elt[1]])
        self.retour.clicked = False


class Pause_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.surface_copie = None
        self.manager.running = True
        self.start = a.Button(
            EMPTY_BUTTON + "PLAY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            (301, 95),
        )
        self.settings = a.Button(
            EMPTY_BUTTON + "SETTINGS.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            (497 * 0.80, 184 * 0.80),
        )
        self.quit = a.Button(
            EMPTY_BUTTON + "EXIT.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            (322 * 0.97, 82 * 0.97),
        )

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN:
                if self.quit.rec.collidepoint(coord):
                    self.quit.clicked = True
                    self.manager.change_state("MENU_P")
                elif self.start.rec.collidepoint(coord):
                    self.start.clicked = True
                    self.manager.change_state("GAME")
                elif self.settings.rec.collidepoint(coord):
                    self.settings.clicked = True
                    self.manager.states["MENU_SETTING_PAUSE"].surface_copie = (
                        self.surface_copie
                    )
                    self.manager.change_state("MENU_SETTING_PAUSE")
            else:
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        True,
                        False,
                        False,
                    )
                elif self.start.rec.collidepoint(coord):
                    self.start.hover, self.quit.hover = True, False
                elif self.settings.rec.collidepoint(coord):
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        False,
                        False,
                        True,
                    )
                else:
                    self.quit.hover, self.start.hover, self.settings.hover = (
                        False,
                        False,
                        False,
                    )

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.surface_copie, (0, 0))
        super().pagedisplay([self.start, self.settings, self.quit])
        self.start.clicked = False
        self.settings.clicked = False
        self.quit.clicked = False
