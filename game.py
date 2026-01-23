import pygame
from player import Player


class Game:
    def __init__(self, screen):
        self.running = True
        self.screen = screen
        largeur, hauteur = self.screen.get_size()

        # ceci est temporaire (remplace la carte)
        self.list_surface = [pygame.Rect(0,0,largeur,5), pygame.Rect(0,hauteur-5,largeur,5),
                             pygame.Rect(0,0,5,hauteur), pygame.Rect(largeur-5,0,5,hauteur),
                             pygame.Rect(largeur//2 + 200, hauteur//2 -300, 300, 150),
                             pygame.Rect(400, 200, 30, 400)]
        # fin du temporaire

        self.player = Player(
            self.screen, largeur // 2 - 30, hauteur // 2 - 20, self.list_surface
        )
        self.clock = pygame.time.Clock()

    def event(self, events: list[pygame.event.Event]) -> bool:
        run_menu = False
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run_menu = True

        self.player.event(pygame.key.get_pressed())

        return run_menu, self.running

    def update(self):
        self.player.update()
        
    def display(self):
        self.screen.fill((100, 100, 100))

        # ceci est temporaire (remplace la carte)
        for i in range(4):
            pygame.draw.rect(self.screen, "gold", self.list_surface[i])
        pygame.draw.rect(self.screen, (0, 119, 190), self.list_surface[4])
        pygame.draw.rect(self.screen, "black", self.list_surface[5])
        # fin du temporaire

        self.player.display()
        pygame.display.flip()  # ne pas utiliser .update()