import pygame as p
import animations as a
import os

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


class Bouton:

    def __init__(
        self, screen, left, top, width, height, color, text=Text("", 0, "", (0, 0, 0))
    ):
        self.screen = screen
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = p.Color(color)
        self.rec = p.Rect(left, top, width, height)
        self.rec2 = p.Rect(left + 15, top + 15, width - 30, height - 30)
        self.text = text
        self.text.screen = screen

    def draw(self):
        """draw the button with text"""
        p.draw.rect(self.screen, self.color, self.rec)
        p.draw.rect(self.screen, (0, 0, 0), self.rec2)
        self.text.draw_text(
            (
                (self.width - self.text.l[0]) // 2 + self.left,
                (self.height - self.text.l[1]) // 2 + self.top,
            )
        )


class Menu:

    def __init__(self, screen):
        self.WINDOWS = screen.get_size()
        self.screen = screen
        self.clock = p.time.Clock()
        self.running = True
        self.pagemenu = True
        self.keybinds = {
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
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 200),
            (400, 200),
        )
        self.settings = a.Button(
            "Ressources/Animations/UI/SETTINGS.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2),
            (400, 200),
        )
        self.quit = a.Button(
            "Ressources/Animations/UI/EXIT.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 200),
            (400, 200),
        )
        self.retour = a.Button(
            r"Ressources\Animations\UI\EMPTY.png",
            self.screen,
            (175, 40),
            (400, 200),
        )
        self.changeup = a.Button(
            r"Ressources\Animations\UI\EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 275),
            (400, 200),
        )
        self.changedown = a.Button(
            r"Ressources\Animations\UI\EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 150),
            (400, 200),
        )
        self.changeleft = a.Button(
            r"Ressources\Animations\UI\EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 - 25),
            (400, 200),
        )
        self.changeright = a.Button(
            r"Ressources\Animations\UI\EMPTY.png",
            self.screen,
            (self.WINDOWS[0] // 2, self.WINDOWS[1] // 2 + 100),
            (400, 200),
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

    def event(self, events: list[p.event.Event]) -> tuple[bool, bool]:
        rungame = False
        for event in events:
            coord = p.mouse.get_pos()
            if self.pagemenu:  # menu page
                if event.type == p.MOUSEBUTTONDOWN:
                    if self.quit.rec.collidepoint(coord):
                        self.quit.clicked, self.running = True, False
                    elif self.start.rec.collidepoint(coord):
                        self.start.clicked, rungame = True, True
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
            else:  # settings page
                if event.type == p.KEYDOWN:
                    if event.key == p.K_ESCAPE and self.checkchangekey():
                        self.pagemenu = True
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
                    checkevent = event.type == p.MOUSEBUTTONDOWN
                    if self.retour.rec.collidepoint(coord):
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (True, False, False, False, False)
                        if checkevent:
                            self.pagemenu = True
                    elif self.changeup.rec.collidepoint(coord):
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (False, True, False, False, False)
                        if checkevent:
                            self.interchange(
                                self.up_t, self.changeup, "up", "...", True
                            )
                    elif self.changedown.rec.collidepoint(coord):
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (False, False, True, False, False)
                        if checkevent:
                            self.interchange(
                                self.down_t, self.changedown, "down", "...", True
                            )
                    elif self.changeleft.rec.collidepoint(coord):
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (False, False, False, True, False)
                        if checkevent:
                            self.interchange(
                                self.left_t, self.changeleft, "left", "...", True
                            )
                    elif self.changeright.rec.collidepoint(coord):
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (False, False, False, False, True)
                        if checkevent:
                            self.interchange(
                                self.right_t, self.changeright, "right", "...", True
                            )
                    else:
                        (
                            self.retour.hover,
                            self.changeup.hover,
                            self.changedown.hover,
                            self.changeleft.hover,
                            self.changeright.hover,
                        ) = (False, False, False, False, False)
        return rungame, self.running

    def update(self) -> dict[str, int]:
        p.display.flip()
        return self.keybinds

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())  # background
        if self.pagemenu:
            self.textdisplay([self.titre])
            self.start.display()
            self.settings.display()
            self.quit.display()
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
            )

    def __run__(self):
        while self.running:
            self.event()
            self.update()
            self.display()

            self.clock.tick(60)
