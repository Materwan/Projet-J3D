import pygame as p
import animations as a

EMPTY_BUTTON = "Ressources/Animations/UI/"

p.font.init()
p.mixer.init()

p.mixer.music.load("Ressources/Musics/placeholder.mp3")
p.mixer.music.play(-1)

"""self.keybinds = {
            "up": p.K_UP,
            "down": p.K_DOWN,
            "left": p.K_LEFT,
            "right": p.K_RIGHT,
        }
        self.key = {"up": False, "down": False, "left": False, "right": False}
        self.bg_img = p.image.load("Ressources/Animations/UI/fond ecran menu.png")
        self.start = a.Button(
            "Ressources/Animations/UI/PLAY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            (301, 95),
        )
        self.settings = a.Button(
            "Ressources/Animations/UI/SETTINGS.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            (497 * 0.80, 184 * 0.80),
        )
        self.quit = a.Button(
            "Ressources/Animations/UI/EXIT.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 150),
            (322 * 0.97, 82 * 0.97),
        )
        self.retour = a.Button(
            "Ressources/Animations/UI/EMPTY.png",
            self.screen,
            (170, 67),
            (301, 95),
        )
        self.changeup = a.Button(
            "Ressources/Animations/UI/EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 210),
            (301, 95),
        )
        self.changedown = a.Button(
            "Ressources/Animations/UI/EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 70),
            (301, 95),
        )
        self.changeleft = a.Button(
            "Ressources/Animations/UI/EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 70),
            (301, 95),
        )
        self.changeright = a.Button(
            "Ressources/Animations/UI/EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 210),
            (301, 95),
        )
        self.up_t = [Text("Impact", 30, "UP: up", (0, 0, 0), self.screen)]
        self.up_t.append(
            (
                (self.changeup.rec.width - self.up_t[0].l[0]) // 2
                + self.changeup.rec.left,
                (self.changeup.rec.height - self.up_t[0].l[1]) // 2
                + self.changeup.rec.top,
            )
        )
        self.down_t = [Text("Impact", 30, "DOWN: down", (0, 0, 0), self.screen)]
        self.down_t.append(
            (
                (self.changedown.rec.width - self.down_t[0].l[0]) // 2
                + self.changedown.rec.left,
                (self.changedown.rec.height - self.down_t[0].l[1]) // 2
                + self.changedown.rec.top,
            )
        )
        self.left_t = [Text("Impact", 30, "LEFT: left", (0, 0, 0), self.screen)]
        self.left_t.append(
            (
                (self.changeleft.rec.width - self.left_t[0].l[0]) // 2
                + self.changeleft.rec.left,
                (self.changeleft.rec.height - self.left_t[0].l[1]) // 2
                + self.changeleft.rec.top,
            )
        )
        self.right_t = [Text("Impact", 30, "RIGHT: right", (0, 0, 0), self.screen)]
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
        self.titre = [Text("Impact", 150, "Mole Tale", (255, 255, 255), self.screen)]
        self.titre.append(((self.WINDOWS[0] - self.titre[0].l[0]) // 2, 0))
    def event(self, events: list[p.event.Event]) -> tuple[bool, bool]:
        coord = p.mouse.get_pos()
            for event in events:
                if event.type == p.QUIT:
                    self.prochaine_etat = "CLOSE"
                    return True
                if event.type == p.MOUSEBUTTONDOWN:
                    if self.quit.rec.collidepoint(coord):
                        self.quit.clicked = True
                        self.prochaine_etat = "CLOSE"
                        return True
                    elif self.start.rec.collidepoint(coord):
                        self.start.clicked = True
                        self.prochaine_etat = "GAME"
                        return True
                    elif self.settings.rec.collidepoint(coord):
                        self.settings.clicked, self.pagemenu = True, False
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

            
        return False

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())  # background
        if self.pagemenu:
            self.textdisplay([self.titre])
            self.pagedisplay([self.start, self.settings, self.quit])
            self.start.clicked = False
            self.settings.clicked = False
            self.quit.clicked = False
        else:
            self.pagedisplay(
                [
                    self.retour,
                    self.changeup,
                    self.changedown,
                    self.changeleft,
                    self.changeright,
                ]
            )
            self.textdisplay(
                [self.up_t, self.down_t, self.left_t, self.right_t, self.retour_t]
            )"""


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
        self.screen.blit(self.bg_img, self.bg_img.get_rect())
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
                    p.mixer.music.stop()
                    self.manager.change_state("GAME")
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
        super().textdisplay([self.titre])
        super().pagedisplay([self.start, self.settings, self.quit])
        self.start.clicked = False
        self.settings.clicked = False
        self.quit.clicked = False


class Setting_Menu(Menu):

    def __init__(self, screen, manager):
        super().__init__(screen, manager)
        self.manager.running = True
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
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE and self.checkchangekey():
                    self.manager.states["GAME"].player.keybinds = self.keybinds
                    self.manager.change_state("MENU_P")
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
            (
                self.retour.hover,
                self.changeup.hover,
                self.changedown.hover,
                self.changeleft.hover,
                self.changeright.hover,
            ) = (False, False, False, False, False)
            if self.checkchangekey():
                """if a keybind is changing dont look for collidepoint"""
                checkevent = event.type == p.MOUSEBUTTONDOWN
                if self.retour.rec.collidepoint(coord):
                    self.retour.hover = True
                    if checkevent:
                        self.retour.hover = False
                        self.manager.states["GAME"].player.keybinds = self.keybinds
                        self.manager.change_state("MENU_P")
                elif self.changeup.rec.collidepoint(coord):
                    self.retour.hover,
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
