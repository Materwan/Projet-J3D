import pygame

class Moteur:
    def __init__(self, screen):
        self.screen = screen
        largeur, hauteur = self.screen.get_size()
        self.list_surface = [pygame.Rect(0,0,largeur,5), pygame.Rect(0,hauteur-5,largeur,5),
                             pygame.Rect(0,0,5,hauteur), pygame.Rect(largeur-5,0,5,hauteur)]
        self.eau = pygame.Rect(largeur//2 + 200, hauteur//2 -300, 300, 150)


    def display(self): # ceci est temporaire
        for elt in self.list_surface:
            pygame.draw.rect(self.screen, "gold", elt)
        pygame.draw.rect(self.screen, (0, 119, 190), self.eau)


    def collide(self, rect_a, rect_b): # renvoie vrai ou faux s'il y a une collision entre les deux surfaces
        return rect_a.colliderect(rect_b)
    

    def collision(self, velocity, hitbox): 
        """
        S'il y a un déplacement sur l'axe x et/ou y alors on regarde s'il y a une collision 
        entre la liste de toutes les surface et notre future "hitbox" en x et/ou y pour ensuite
        s'il y a collision empecher le déplacement (en mettant la vélocité sur 0 pour x et/ou y)
        """
        self.list_surface.append(self.eau) # temporaire

        if velocity[0] != 0: # regarde si la vélocité nous indique un déplacement en x
            future_hitbox = hitbox.move(5 * velocity[0], 0)
            if any(self.collide(surface, future_hitbox) for surface in self.list_surface): # empêche le déplacement à la moindre collision
                velocity[0] = 0

        if velocity[1] != 0: # pareil pour l'axe y
            future_hitbox = hitbox.move(0, 5 * velocity[1])
            if any(self.collide(surface, future_hitbox) for surface in self.list_surface):
                velocity[1] = 0
        return velocity
