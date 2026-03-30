import pygame as p
import animations as a
from typing import List, Dict
import threading
import socket
import json
import asyncio
import time

MENU_ASSET_DIRECTORY = "Ressources/UI_&_élements_graphiques/"
BACKGROUND = MENU_ASSET_DIRECTORY + "fond ecran menu.png"
PLAY_BUTTON = MENU_ASSET_DIRECTORY + "PLAY.png"
SETTING_BUTTON = MENU_ASSET_DIRECTORY + "SETTINGS.png"
EXIT_BUTTON = MENU_ASSET_DIRECTORY + "EXIT.png"
EMPTY_BUTTON = MENU_ASSET_DIRECTORY + "EMPTY.png"
TITLE = MENU_ASSET_DIRECTORY + "logo.png"

UDP_IP = "0.0.0.0"
UDP_PORT = 9999

p.font.init()
p.mixer.init()

p.mixer.music.load("Ressources/Musics/placeholder.mp3")
p.mixer.music.play(-1)


def create_button_with_text(image, screen, pos, text_str="", scale=1):
    button = a.Button(image, screen, pos, scale=scale)
    text = Text("Impact", 30, text_str, (0, 0, 0), screen)
    coord = (
        (button.rec.width - text.lenth[0]) // 2 + button.rec.left,
        (button.rec.height - text.lenth[1]) // 2 + button.rec.top,
    )
    return button, [text, coord]


class Text:

    def __init__(self, name, size, text, t_color, screen=None, antialias=False):
        self.screen = screen
        self.caractere = text
        self.font = p.font.SysFont(name, size)
        self.text = self.font.render(text, antialias, t_color)
        self.lenth = self.text.get_size()

    def draw_text(self, coordonninate):
        """draw a text"""
        self.screen.blit(self.text, coordonninate)


class Menu:

    def __init__(self, screen: p.Surface, manager):
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

        # =======================Button Start=======================
        self.retour, self.retour_t = create_button_with_text(
            EMPTY_BUTTON, self.screen, (170, 67), "<--"
        )
        # =======================Button End=======================

    def recalculcoord(self, text, button):
        """recalcul the coordonnee"""
        return (
            (button.rec.width - text[0].lenth[0]) // 2 + button.rec.left,
            (button.rec.height - text[0].lenth[1]) // 2 + button.rec.top,
        )

    def pagedisplay(self):
        """draw the page"""
        for elt in self.eltpages:
            elt.display()

    def textdisplay(self):
        """draw the text"""
        for elt in self.elttexts:
            elt[0].draw_text(elt[1])


class Principal_Menu(Menu):

    def __init__(self, screen: p.Surface, manager):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Button Start=======================
        self.start = a.Button(
            PLAY_BUTTON,
            self.screen,
            (self.half[0], self.half[1] - 100),
        )
        self.settings, _ = create_button_with_text(
            SETTING_BUTTON, self.screen, (self.half[0], self.half[1] + 50), "", 0.8
        )
        self.quit, _ = create_button_with_text(
            EXIT_BUTTON, self.screen, (self.half[0], self.half[1] + 200)
        )
        self.titre, _ = create_button_with_text(
            TITLE, self.screen, (self.half[0], self.half[1] - 250), "", 0.6
        )
        # =======================Button End=======================

        self.elttexts = []
        self.eltpages = [self.titre, self.start, self.settings, self.quit]

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
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
                self.quit.hover, self.start.hover, self.settings.hover = (
                    False,
                    False,
                    False,
                )
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover = True
                elif self.start.rec.collidepoint(coord):
                    self.start.hover = True
                elif self.settings.rec.collidepoint(coord):
                    self.settings.hover = True

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.textdisplay()
        self.pagedisplay()
        self.start.clicked = False
        self.settings.clicked = False
        self.quit.clicked = False


class Setting_Menu(Menu):

    def __init__(self, screen, manager, menu_appel="MENU_P"):
        super().__init__(screen, manager)
        self.manager.running = True
        self.surface_copie = None
        self.menu_appel = menu_appel

        # =======================Button Start=======================
        self.changeup, self.up_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 - 70),
            "UP: " + p.key.name(self.keybinds["up"]),
        )
        self.changedown, self.down_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 - 200, self.WINDOWS[1] // 2 + 70),
            "DOWN: " + p.key.name(self.keybinds["down"]),
        )
        self.changeleft, self.left_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 200, self.WINDOWS[1] // 2 - 70),
            "LEFT: " + p.key.name(self.keybinds["left"]),
        )
        self.changeright, self.right_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2 + 200, self.WINDOWS[1] // 2 + 70),
            "RIGHT: " + p.key.name(self.keybinds["right"]),
        )
        self.changeattack, self.attack_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 200),
            "ATTACK: " + p.key.name(self.keybinds["attack"]),
        )
        # =======================Button End=======================

        self.elttexts = [
            self.up_t,
            self.down_t,
            self.left_t,
            self.right_t,
            self.attack_t,
            self.retour_t,
        ]
        self.eltpages = [
            self.retour,
            self.changeup,
            self.changedown,
            self.changeleft,
            self.changeright,
            self.changeattack,
        ]

    def changekey(self, event):
        """take the last keybind to replace the old one"""
        for elt in self.key.keys():
            if self.key[elt]:
                if event.type == p.KEYDOWN:
                    if event.key != p.K_ESCAPE:
                        self.keybinds[elt] = event.key
                else:
                    self.keybinds[elt] = event.button
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
        changetext[0].lenth = changetext[0].text.get_size()
        changetext[1] = super().recalculcoord(changetext, button)
        self.key[direction] = bool

    def event(self, events):
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
                (
                    self.retour.hover,
                    self.changeup.hover,
                    self.changedown.hover,
                    self.changeleft.hover,
                    self.changeright.hover,
                    self.changeattack.hover,
                ) = (False, False, False, False, False, False)
                checkevent = (
                    event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT
                )
                # Les fonctions ca existe !!!!
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
                elif self.changeattack.rec.collidepoint(coord):
                    self.changeattack.hover = True
                    if checkevent:
                        self.interchange(
                            self.attack_t, self.changeattack, "attack", "...", True
                        )

    def update(self):
        pass
        if (
            self.menu_appel != "MENU_P"
            and self.manager.states["GAME"].playing_mode != "solo"
        ):
            self.manager.states["GAME"].update()

    def display(self):
        if self.menu_appel == "MENU_P":
            # Euhhhhh Non
            self.screen.blit(self.bg_img, self.bg_img_coord)
        else:
            self.manager.states["GAME"].display()
            self.screen.blit(self.blackscreen, (0, 0))
            # self.screen.blit(self.surface_copie, (0, 0))
        self.pagedisplay()
        self.textdisplay()


class Play_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.manager.running = True

        # =======================Button Start=======================
        self.solo, self.solo_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            "SOLO",
        )
        self.multiplayer, self.multiplayer_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            self.half,
            "MULTIPLAYER",
        )
        self.joinmultiplayer, self.joinmultiplayer_t = create_button_with_text(
            EMPTY_BUTTON,
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
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

    def event(self, events):
        # Stp aére ton code
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
                    self.manager.state.initialize()
                elif self.multiplayer.rec.collidepoint(coord):
                    self.multiplayer.clicked = True
                    p.mixer.music.stop()
                    self.multiplayer.hover = False
                    self.manager.states["GAME"].playing_mode = "host"
                    self.manager.change_state("GAME")
                    self.manager.state.initialize()
                elif self.joinmultiplayer.rec.collidepoint(coord):
                    self.joinmultiplayer.clicked = True
                    self.joinmultiplayer.hover = False
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
        self.screen.blit(self.bg_img, self.bg_img_coord)
        self.pagedisplay()
        self.textdisplay()
        (
            self.retour.clicked,
            self.solo.clicked,
            self.multiplayer.clicked,
            self.joinmultiplayer.clicked,
        ) = (False, False, False, False)


class Join_Multi_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.serveurs_save = None
        self.list_button = []
        self.manager.running = True
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
        self.upd_prot = threading.Thread(target=self.recieve_udp)
        self.udp_event = threading.Event()
        self.upd_prot.start()
        self.elttexts = [self.retour_t]
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

    def create_list_button(self, serveurs):
        # Ca non
        self.list_button = []
        count = 0
        for serveur in serveurs.keys():
            button, button_t = create_button_with_text(
                EMPTY_BUTTON,
                self.screen,
                (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200 + count * 150),
                serveur,
            )
            self.list_button.append((button, button_t))
            count += 1

    def event(self, events):
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
                    self.retour.clicked = True
                    self.retour.hover = False
                    self.udp_event.clear()
                    self.manager.change_state("MENU_PLAY")
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
                            p.mixer.music.stop()
                            break
            else:
                self.retour.hover = False
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True

    def update(self):
        pass

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img_coord)
        if self.serveurs != self.serveurs_save:
            self.serveurs_save = self.serveurs
            self.eltpages = [self.retour]
            self.elttexts = [self.retour_t]
            self.create_list_button(self.serveurs)
            for elt in self.list_button:
                self.eltpages.append(elt[0])
                self.elttexts.append(elt[1])
        self.pagedisplay()
        self.textdisplay()
        self.retour.clicked = False


class Pause_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.surface_copie = None
        self.blackscreen = p.Surface(self.WINDOWS, p.SRCALPHA)
        p.draw.rect(
            self.blackscreen,
            (10, 10, 22, 100),
            (0, 0, self.WINDOWS[0], self.WINDOWS[1]),
        )
        self.manager.running = True

        # =======================Button Start=======================
        self.resume, self.resume_t = create_button_with_text(
            EMPTY_BUTTON, self.screen, (self.half[0], self.half[1] - 150), "RESUME"
        )
        self.settings, _ = create_button_with_text(
            SETTING_BUTTON, self.screen, self.half, "", 0.8
        )
        self.quit, _ = create_button_with_text(
            EXIT_BUTTON, self.screen, (self.half[0], self.half[1] + 150)
        )
        # =======================Button End=======================

        self.eltpages = [self.resume, self.settings, self.quit]
        self.elttexts = [self.resume_t]

    def event(self, events):
        coord = p.mouse.get_pos()
        for event in events:
            if event.type == p.QUIT:
                self.manager.running = False
            if event.type == p.MOUSEBUTTONDOWN and event.button == p.BUTTON_LEFT:
                if self.quit.rec.collidepoint(coord):
                    self.quit.clicked = True
                    self.manager.states["GAME"].player_controller.close = True
                    self.manager.change_state("MENU_P")
                elif self.resume.rec.collidepoint(coord):
                    self.resume.clicked = True
                    self.manager.change_state("GAME")
                elif self.settings.rec.collidepoint(coord):
                    self.settings.clicked = True
                    self.manager.states["MENU_SETTING_PAUSE"].keybinds = (
                        self.manager.states["GAME"].keybinds
                    )
                    self.manager.states["MENU_SETTING_PAUSE"].surface_copie = (
                        self.surface_copie
                    )
                    self.manager.change_state("MENU_SETTING_PAUSE")

            elif event.type == p.KEYDOWN and event.key == p.K_ESCAPE:
                self.resume.clicked = True
                self.manager.change_state("GAME")
            else:
                if self.quit.rec.collidepoint(coord):
                    self.quit.hover, self.resume.hover, self.settings.hover = (
                        True,
                        False,
                        False,
                    )
                elif self.resume.rec.collidepoint(coord):
                    self.resume.hover, self.quit.hover = True, False
                elif self.settings.rec.collidepoint(coord):
                    self.quit.hover, self.resume.hover, self.settings.hover = (
                        False,
                        False,
                        True,
                    )
                else:
                    self.quit.hover, self.resume.hover, self.settings.hover = (
                        False,
                        False,
                        False,
                    )

    def update(self):
        if self.manager.states["GAME"].playing_mode != "solo":
            self.manager.states["GAME"].update()

    def display(self):
        self.manager.states["GAME"].display()
        self.screen.blit(self.blackscreen, (0, 0))
        self.pagedisplay()
        self.textdisplay()
        self.resume.clicked = False
        self.settings.clicked = False
        self.quit.clicked = False
