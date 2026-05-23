import pygame
from map import MapManager, BaseMap
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ennemis import Ennemi
    from player import PlayerControllerBase


class Moteur:
    def __init__(self):
        self.map: MapManager = None

        # Configuration : { "direction": (decalage_x, decalage_y, largeur, hauteur) }
        self.attaque_config = {
            "right": (0, -55, 70, 80),
            "left": (-70, -55, 70, 80),
        }

    def collision(
        self,
        hitbox: pygame.Rect,
        velocity: pygame.Vector2,
        other_hitbox: list[pygame.Rect],
        map: BaseMap | None = None,
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
        map = self.map.map if map is None else map
        nearby_obstacles = map.get_nearby_obstacles(hitbox)

        for elt in other_hitbox:
            nearby_obstacles.append(elt)

        if velocity[0] != 0:
            future_hitbox = hitbox.move(float(velocity[0]) * 3, 0)
            if any(
                future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles
            ):
                velocity[0] = 0

        if velocity[1] != 0:
            future_hitbox = hitbox.move(0, float(velocity[1]) * 3)
            if any(
                future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles
            ):
                velocity[1] = 0

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

    def create_rect_attaque(
        self, position: pygame.Vector2 | pygame.Rect, direction: str
    ):
        dec_x, dec_y, wide, high = self.attaque_config[direction]

        return pygame.Rect(position.x + dec_x, position.y + dec_y, wide, high)

    def apply_attack(
        self, attaque_rect: pygame.Rect, ennemi: "Ennemi | PlayerControllerBase"
    ):
        if ennemi.hitbox_damage and attaque_rect.colliderect(ennemi.hitbox_damage):
            ennemi.update_pv(-1)
