import pygame

class Moteur:
    def __init__(self, screen):
        self.screen = screen


    def analyse(self): # doit donner la liste des obstacle proche du joueur selon ça position sur la carte
        pass


    def collision(self, velocity, hitbox, list_surface): # list_surface devra être remplacer par la methode analyse
        """
        S'il y a un déplacement sur l'axe x et/ou y alors on regarde s'il y a une collision 
        entre la liste de toutes les surface et notre future "hitbox" en x et/ou y pour ensuite
        s'il y a collision empecher le déplacement (en mettant la vélocité sur 0 pour x et/ou y)
        """
        if velocity[0] != 0:
            future_hitbox = hitbox.move(velocity[0] * 3, 0)
            if any(future_hitbox.colliderect(surface) for surface in list_surface):
                velocity[0] = 0

        if velocity[1] != 0: # pareil pour l'axe y
            future_hitbox = hitbox.move(0, velocity[1] * 3)
            if any(future_hitbox.colliderect(surface) for surface in list_surface):
                velocity[1] = 0
        return velocity
