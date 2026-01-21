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
        self.bg_img = p.image.load('Ressources/Animations/UI/fond ecran menu.png')
        self.start = a.Button(
            "Ressources/Animations/UI/PLAY.png",
            self.screen,
            (self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 - 150),
            (200,
             100))
        self.settings = a.Button(
            "Ressources/Animations/UI/SETTINGS.png",
            self.screen,
            (self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 - 25),
            (200,
            100)
        )
        self.quit = a.Button(
            "Ressources/Animations/UI/EXIT.png",
            self.screen,
            (self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 + 100),
            (200,
            100)
        )
        self.pagemenu = True
        self.retour = Bouton(
            self.screen,
            0,
            0,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "<--", (255, 0, 0)),
        )
        self.keybinds = {
            "up": p.K_UP,
            "down": p.K_DOWN,
            "left": p.K_LEFT,
            "right": p.K_RIGHT,
        }
        self.changeup = Bouton(
            self.screen,
            self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 - 275,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "UP: up", (255, 0, 0)),
        )
        self.changedown = Bouton(
            self.screen,
            self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 - 150,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "DOWN: down", (255, 0, 0)),
        )
        self.changeleft = Bouton(
            self.screen,
            self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 - 25,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "LEFT: left", (255, 0, 0)),
        )
        self.changeright = Bouton(
            self.screen,
            self.WINDOWS[0] // 2 - 100,
            self.WINDOWS[1] // 2 + 100,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "RIGHT: right", (255, 0, 0)),
        )
        self.key = {"up": False, "down": False, "left": False, "right": False}

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

    def interchange(self, bouton, direction, caractere, bool):
        """change the texte of the bouton that you want to change the keybind"""
        bouton.text.text = bouton.text.font.render(caractere, False, (255, 0, 0))
        bouton.text.l = bouton.text.text.get_size()
        self.key[direction] = bool

    def pagedisplay(self, eltpages):
        """draw the page"""
        for elt in eltpages:
            elt.draw()

    def event(self, events: list[p.event.Event]) -> tuple[bool, bool]:
        rungame = False
        for event in events:
            if self.pagemenu:  # menu page
                if event.type == p.MOUSEBUTTONDOWN:
                    coord = p.mouse.get_pos()
                    if self.quit.rec.collidepoint(coord):
                        self.quit.clicked = True
                        self.running = False
                    elif self.start.rec.collidepoint(coord):
                        self.start.clicked = True
                        rungame = True
                    elif self.settings.rec.collidepoint(coord):
                        self.settings.clicked = True
                        self.pagemenu = False
                else:
                    coord = p.mouse.get_pos()
                    if self.quit.rec.collidepoint(coord):
                        self.quit.hover = True
                        self.start.hover = False
                        self.settings.hover = False
                    elif self.start.rec.collidepoint(coord):
                        self.start.hover = True
                        self.quit.hover = False
                    elif self.settings.rec.collidepoint(coord):
                        self.quit.hover = False
                        self.start.hover = False
                        self.settings.hover = True
                    else:
                        self.quit.hover = False
                        self.start.hover = False
                        self.settings.hover = False
            else:  # settings page
                if event.type == p.KEYDOWN:
                    if event.key == p.K_ESCAPE and self.checkchangekey():
                        self.pagemenu = True
                    self.changekey(event)  # try to change the keybind
                    self.interchange(
                        self.changeup,
                        "up",
                        "UP: " + p.key.name(self.keybinds["up"]),
                        False,
                    )
                    self.interchange(
                        self.changedown,
                        "down",
                        "DOWN: " + p.key.name(self.keybinds["down"]),
                        False,
                    )
                    self.interchange(
                        self.changeleft,
                        "left",
                        "LEFT: " + p.key.name(self.keybinds["left"]),
                        False,
                    )
                    self.interchange(
                        self.changeright,
                        "right",
                        "RIGHT: " + p.key.name(self.keybinds["right"]),
                        False,
                    )
                if event.type == p.MOUSEBUTTONDOWN and self.checkchangekey():
                    """if a keybind is changing dont look for collidepoint"""
                    coord = p.mouse.get_pos()
                    if self.retour.rec.collidepoint(coord):
                        self.pagemenu = True
                    elif self.changeup.rec.collidepoint(coord):
                        self.interchange(self.changeup, "up", "...", True)
                    elif self.changedown.rec.collidepoint(coord):
                        self.interchange(self.changedown, "down", "...", True)
                    elif self.changeleft.rec.collidepoint(coord):
                        self.interchange(self.changeleft, "left", "...", True)
                    elif self.changeright.rec.collidepoint(coord):
                        self.interchange(self.changeright, "right", "...", True)
        return rungame, self.running

    def update(self) -> dict[str, int]:
        p.display.flip()
        return self.keybinds

    def display(self):
        self.screen.blit(self.bg_img, self.bg_img.get_rect())  # background
        if self.pagemenu:
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

    def __run__(self):
        while self.running:
            self.event()
            self.update()
            self.display()

            self.clock.tick(60)
