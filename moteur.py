import pygame

class Moteur:
    def __init__(self, screen):
        self.screen = screen
        largeur, hauteur = self.screen.get_size()
        self.list_surface = [pygame.Rect(0,0,largeur,5), pygame.Rect(0,hauteur-5,largeur,5),
                             pygame.Rect(0,0,5,hauteur), pygame.Rect(largeur-5,0,5,hauteur),
                             pygame.Rect(largeur//2 + 200, hauteur//2 -300, 300, 150),
                             pygame.Rect(400, 200, 30, 400)]


    def display(self): # ceci est temporaire
        for i in range(4):
            pygame.draw.rect(self.screen, "gold", self.list_surface[i])
        pygame.draw.rect(self.screen, (0, 119, 190), self.list_surface[4])
        pygame.draw.rect(self.screen, "black", self.list_surface[5])


    def collide(self, rect_a, rect_b): # renvoie vrai ou faux s'il y a une collision entre les deux surfaces
        return rect_a.colliderect(rect_b)
    

    def collision(self, velocity, hitbox): 
        """
        S'il y a un déplacement sur l'axe x et/ou y alors on regarde s'il y a une collision 
        entre la liste de toutes les surface et notre future "hitbox" en x et/ou y pour ensuite
        s'il y a collision empecher le déplacement (en mettant la vélocité sur 0 pour x et/ou y)
        """
        if velocity[0] != 0: # regarde si la vélocité nous indique un déplacement en x
            future_hitbox = hitbox.move(3 * velocity[0], 0)
            if any(self.collide(surface, future_hitbox) for surface in self.list_surface): # empêche le déplacement à la moindre collision
                velocity[0] = 0

        if velocity[1] != 0: # pareil pour l'axe y
            future_hitbox = hitbox.move(0, 3 * velocity[1])
            if any(self.collide(surface, future_hitbox) for surface in self.list_surface):
                velocity[1] = 0
        return velocity
