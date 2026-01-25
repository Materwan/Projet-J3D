import pygame

class Moteur:
    def __init__(self, screen):
        self.screen = screen
        self.map = None


    def get_nearby_obstacles(self, hitbox):
        """
        Donne la liste des obstacles proche du joueur selon ça position sur la carte
        """
        return self.map
        """
        nearby_obstacles = []
    
        # Trouver la position du joueur dans la grille
        grid_x = hitbox.centerx // 16
        grid_y = (hitbox.y - 10) // 16
        
        # Vérifier un carré de 3x3 tuiles autour du joueur
        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):
                # Si la valeur est de l'eau (< 0.5)
                if game_map[x][y] < 0.5:
                    # On crée le rectangle de collision pour cette tuile
                    nearby_obstacles.append(pygame.Rect(x * 16, y * 16, 16, 16))
                        
        return nearby_obstacles
        """


    def collision(self, hitbox, velocity, nearby_obstacles):
        """
        S'il y a un déplacement sur l'axe x et/ou y alors on regarde s'il y a une collision 
        entre la liste de toutes les surface et notre future "hitbox" en x et/ou y pour ensuite
        s'il y a collision empecher le déplacement (en mettant la vélocité sur 0 pour x et/ou y)
        """
        if velocity.x != 0:
            future_hitbox = hitbox.move(velocity.x * 2, 0)
            if any(future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles):
                velocity.x = 0

        if velocity.y != 0:
            future_hitbox = hitbox.move(0, velocity.y * 2)
            if any(future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles):
                velocity.y = 0