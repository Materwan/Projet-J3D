import pygame
from typing import List


class Moteur:
    def __init__(self, screen):
        self.screen = screen
        self.map = None

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
        grid_x = hitbox.centerx // 16
        grid_y = (hitbox.y - 10) // 16

        # Vérifier un carré de 3x3 tuiles autour du joueur
        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):
                # Si la valeur est de l'eau (< 0.5)
                if self.map[x][y] < 0.5:
                    # On crée le rectangle de collision pour cette tuile
                    nearby_obstacles.append(pygame.Rect(x * 16, y * 16, 16, 16))

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
        nearby_obstacles = self.map  # temporaire /// get_nearby_obstacles(hitbox)
        if other_hitbox != None:
            nearby_obstacles.append(other_hitbox)
        if velocity.x != 0:
            future_hitbox = hitbox.move(velocity.x * 2, 0)
            if any(
                future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles
            ):
                velocity.x = 0

        if velocity.y != 0:
            future_hitbox = hitbox.move(0, velocity.y * 2)
            if any(
                future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles
            ):
                velocity.y = 0

        if other_hitbox != None:
            nearby_obstacles.pop(-1)

    def verif_velocity(self, velocity: List[int]):
        """
        Convertit la vélocité reçue (sous forme de liste : [x, y]) en vecteur.
        Puis assure que les entrées sont comprises entre -1 et 1.
        Si le joueur se déplace en diagonale, la vélocité est normalisée.

        Returns:
            tuple[pygame.Vector2, bool]:
                - vel : Le vecteur de déplacement normalisé (longueur max = 1).
                - moving_intent : True si le joueur essaie de se déplacer, False sinon.
        """
        vel = pygame.Vector2(velocity)

        vel.x = max(-1.0, min(1.0, vel.x))
        vel.y = max(-1.0, min(1.0, vel.y))

        length = vel.length_squared()
        if length > 1.0:
            vel.normalize_ip()

        return vel, length > 0
