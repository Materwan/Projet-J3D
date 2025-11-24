import pygame as p
from game import Game

p.init()

p.font.init()

WINDOWS = p.display.get_desktop_sizes()[0]  # fullscreen

screen = p.display.set_mode(WINDOWS)


class Text:

    def __init__(self, name, size, text, t_color, antialias=False):
        self.font = p.font.SysFont(name, size)
        self.text = self.font.render(text, antialias, t_color)
        self.l = self.text.get_size()

    def draw_text(self, coordonninate):
        """draw a text"""
        screen.blit(self.text, coordonninate)


class Bouton:

    def __init__(
        self, left, top, width, height, color, text=Text("", 0, "", (0, 0, 0))
    ):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = p.Color(color)
        self.rec = p.Rect(left, top, width, height)
        self.rec2 = p.Rect(left + 15, top + 15, width - 30, height - 30)
        self.text = text

    def draw(self):
        """draw the button with text"""
        p.draw.rect(screen, self.color, self.rec)
        p.draw.rect(screen, (0, 0, 0), self.rec2)
        self.text.draw_text(
            (
                (self.width - self.text.l[0]) // 2 + self.left,
                (self.height - self.text.l[1]) // 2 + self.top,
            )
        )


class Menu:

    def __init__(self):
        self.screen = screen
        self.clock = p.time.Clock()
        self.running = True
        self.start = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 - 150,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "Start", (255, 0, 0)),
        )
        self.settings = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 - 25,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "Settings", (255, 0, 0)),
        )
        self.quitter = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 + 100,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "Quitter", (255, 0, 0)),
        )
        self.pagemenu = True
        self.settingstext = Text(
            "Impact", 50, "Page pour changer les touches", (255, 0, 0)
        )
        self.retour = Bouton(
            0, 0, 200, 100, (61, 239, 73), Text("Impact", 30, "<--", (255, 0, 0))
        )
        self.keybinds = {
            "up": p.K_UP,
            "down": p.K_DOWN,
            "left": p.K_LEFT,
            "right": p.K_RIGHT,
        }
        self.changeup = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 - 275,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "UP", (255, 0, 0)),
        )
        self.changedown = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 - 150,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "DOWN", (255, 0, 0)),
        )
        self.changeleft = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 - 25,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "LEFT", (255, 0, 0)),
        )
        self.changeright = Bouton(
            WINDOWS[0] // 2 - 100,
            WINDOWS[1] // 2 + 100,
            200,
            100,
            (61, 239, 73),
            Text("Impact", 30, "RIGHT", (255, 0, 0)),
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

    def event(self):
        events = p.event.get()
        for event in events:
            if self.pagemenu:  # menu page
                if event.type == p.MOUSEBUTTONDOWN:
                    coord = p.mouse.get_pos()
                    if self.quitter.rec.collidepoint(coord):
                        self.running = False
                    elif self.start.rec.collidepoint(coord):
                        Game().run()
                    elif self.settings.rec.collidepoint(coord):
                        self.pagemenu = False
            else:  # settings page
                if event.type == p.KEYDOWN:
                    self.changekey(event)  # try to change the keybind
                    if event.key == p.K_ESCAPE:
                        self.pagemenu = True
                if event.type == p.MOUSEBUTTONDOWN and self.checkchangekey():
                    """if a keybind is changing dont look for collidepoint"""
                    coord = p.mouse.get_pos()
                    if self.retour.rec.collidepoint(coord):
                        self.pagemenu = True
                    elif self.changeup.rec.collidepoint(coord):
                        self.key["up"] = True
                    elif self.changedown.rec.collidepoint(coord):
                        self.key["down"] = True
                    elif self.changeleft.rec.collidepoint(coord):
                        self.key["left"] = True
                    elif self.changeright.rec.collidepoint(coord):
                        self.key["right"] = True

    def update(self):
        p.display.flip()

    def display(self):
        self.screen.fill((0, 0, 0))  # background
        if self.pagemenu:
            self.start.draw()
            self.settings.draw()
            self.quitter.draw()
        else:
            self.retour.draw()
            self.changeup.draw()
            self.changedown.draw()
            self.changeleft.draw()
            self.changeright.draw()

    def run(self):
        while self.running:
            self.event()
            self.update()
            self.display()

            self.clock.tick(60)
