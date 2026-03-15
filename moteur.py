import pygame
from map import Map


class Moteur:
    def __init__(self, screen, camera):
        self.screen = screen
        self.camera = camera
        self.map = None
        self.map: Map
        self.nearby_obstacles = []

        # Configuration : { "direction": (decalage_x, decalage_y, largeur, hauteur) }
        self.attaque_config = {
            "right": (0, -55, 70, 60),
            "left": (-70, -55, 70, 60),
            # "up": (-25, -70, 80, 70),
            # "down": (-25, 0, 80, 70),
        }

    def get_nearby_obstacles(self, hitbox: pygame.Rect):
        """
        Récupère la matrice de la map du jeu.
        Analyse une zone de 3x3 tuiles autour de la position
        centrale du joueur pour optimiser les tests de collision.

        Args:
            hitbox (pygame.Rect): La hitbox du joueur pour calculer sa position sur la grille.
        Returns:
            list[pygame.Rect]: Liste des obstacles à proximité immédiate.
        """
        nearby_obstacles = []

        # Trouver la position du joueur dans la grille
        grid_x = hitbox.centerx // 32
        grid_y = hitbox.centery // 32

        # Vérifier un carré de 3x3 tuiles autour du joueur
        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):
                # Si la valeur est de l'eau (< 0.5)
                if self.map.map[x][y] < 0.5:
                    # On crée le rectangle de collision pour cette tuile
                    nearby_obstacles.append(pygame.Rect(x * 32, y * 32, 32, 32))

        return nearby_obstacles

    def collision(
        self,
        hitbox: pygame.Rect,
        velocity: pygame.Vector2,
        other_hitbox: pygame.Rect | None,
    ):
        """
        Anticipe et résout les collisions avec les obstacles environnants.

        Sépare les axes X et Y pour permettre de glisser contre un mur.
        Si un obstacle est détecté dans la trajectoire future (vitesse * 2),
        la vélocité sur cet axe est annulée.

        Args:
            hitbox (pygame.Rect): La boîte de collision actuelle du joueur.
            velocity (pygame.Vector2): Vecteur de déplacement souhaité (modifié sur place).
            other_hitbox (pygame.Rect|None): La boîte de collision actuelle de l'autre joueur.
        """
        self.nearby_obstacles = self.get_nearby_obstacles(hitbox)
        if other_hitbox != None:
            self.nearby_obstacles.append(other_hitbox)

        if velocity.x != 0:
            future_hitbox = hitbox.move(velocity.x * 3, 0)
            if any(
                future_hitbox.colliderect(obstacle)
                for obstacle in self.nearby_obstacles
            ):
                velocity.x = 0

        if velocity.y != 0:
            future_hitbox = hitbox.move(0, velocity.y * 3)
            if any(
                future_hitbox.colliderect(obstacle)
                for obstacle in self.nearby_obstacles
            ):
                velocity.y = 0

    def verif_velocity(self, velocity: list) -> pygame.Vector2:
        """
        Convertit et valide la vélocité reçue du réseau.
        Bride les valeurs entre -1 et 1 pour éviter qu'un client
        malveillant ou bugué n'envoie des valeurs aberrantes.
        """
        vel = pygame.Vector2(velocity)
        vel.x = max(-1.0, min(1.0, vel.x))
        vel.y = max(-1.0, min(1.0, vel.y))
        return vel

    def create_rect_attaque(self, position, direction):
        dec_x, dec_y, wide, high = self.attaque_config[direction]

        return pygame.Rect(position.x + dec_x, position.y + dec_y, wide, high)
