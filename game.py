import pygame
from player import Player


class Game:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        largeur, hauteur = self.screen.get_size()
        self.player = Player(self.screen, largeur // 2 - 30, hauteur // 2 - 20)

        # ceci est temporaire (remplace la carte)
        self.map = [
            pygame.Rect(0, 0, largeur, 5),
            pygame.Rect(0, hauteur - 5, largeur, 5),
            pygame.Rect(0, 0, 5, hauteur),
            pygame.Rect(largeur - 5, 0, 5, hauteur),
            pygame.Rect(largeur // 2 + 200, hauteur // 2 - 300, 300, 150),
            pygame.Rect(400, 200, 30, 400),
        ]
        self.player.moteur.map = self.map

    def event(self, events: list[pygame.event.Event]) -> bool:
        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.play(-1)
                    self.manager.change_state("MENU_P")

        self.player.event(pygame.key.get_pressed())
        return False

    def update(self):
        self.player.update()

    def display(self):
        self.screen.fill((100, 100, 100))

        # ceci est temporaire (remplace la carte)
        for i in range(4):
            pygame.draw.rect(self.screen, "gold", self.map[i])
        pygame.draw.rect(self.screen, (0, 119, 190), self.map[4])
        pygame.draw.rect(self.screen, "black", self.map[5])
        # fin du temporaire

        self.player.display()
