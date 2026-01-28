import pygame
from typing import List


class Moteur:
    def __init__(self, screen):
        self.screen = screen
        self.map = None


    def get_nearby_obstacles(self, hitbox):
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


    def collision(self, hitbox: pygame.Rect, velocity: pygame.Vector2):
        """
        Anticipe et résout les collisions avec les obstacles environnants.
        
        Sépare les axes X et Y pour permettre de glisser contre un mur. 
        Si un obstacle est détecté dans la trajectoire future (vitesse * 2), 
        la vélocité sur cet axe est annulée.

        Args:
            hitbox (pygame.Rect): La boîte de collision actuelle de l'entité.
            velocity (pygame.Vector2): Vecteur de déplacement souhaité (modifié sur place).
        """
        nearby_obstacles = self.map # temporaire
        if velocity.x != 0:
            future_hitbox = hitbox.move(velocity.x * 2, 0)
            if any(future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles):
                velocity.x = 0

        if velocity.y != 0:
            future_hitbox = hitbox.move(0, velocity.y * 2)
            if any(future_hitbox.colliderect(obstacle) for obstacle in nearby_obstacles):
                velocity.y = 0


    def new_player(self, name, x, y):
        """
        Enregistre un nouveau joueur dans le dictionnaire player_data.
        Args:
            name (str): Identifiant unique (Nom ou IP).
            x, y (int): Coordonnées de départ.
        """
        self.player_data[name] = {
            "position" : pygame.Vector2(x, y),
            "hitbox" : pygame.Rect(x, y, 32, 15),
            "direction" : "right"
        }


    def del_player(self, name):
        """
        Supprime un joueur du dictionnaire player_data.
        Args:
            name (str): Identifiant unique (Nom ou IP).
        """
        self.player_data.pop(name, None)


    def verif_velocity(self, velocity):
        """
        Convertit la vélocité reçue (sous forme de liste : [x, y]) en vecteur.
        Puis assure que les entrées sont comprises entre -1 et 1. 
        Si le joueur se déplace en diagonale, la vélocité est normalisée.
        Returns:
            vel (pygame.Vector2): Vecteur de déplacement
            moving_intent (bool): Un bolléen qui est vrai si vel != [0, 0]
        """
        vel = pygame.Vector2(velocity)

        vel.x = max(-1.0, min(1.0, vel.x))
        vel.y = max(-1.0, min(1.0, vel.y))

        length = vel.length_squared()
        if length > 1.0:
            vel.normalize_ip()
        
        return vel, length > 0


    def get_player_hitbox(name):
        """
        Donne la hitbox de tous les joueurs,
        sauf la hitbox qui a comme clé le nom donner en argument
        """
        pass


    def handle_data(self, dico):
        """
        Prend un dico de cette forme (pour l'instant) : 
        self.dico = {"player1" : {"velocity": [1, 0]}, ...}
        Et return :
        dico_sortant = {"player1" : {"position" : [595, 1474], "moving_intent" : True, "direction" : "right"}, ...}
        """
        dico_sortant = {}
        for name, data in dico.items():
            direction = self.player_data[name]["direction"]

            # gestion de la velocité et des déplacements en diagonales
            velocity, moving_intent = self.verif_velocity(data["velocity"])
            if moving_intent: # si le joueur veut se deplacer alors :

                # gestion collision
                self.collision(self.player_data[name]["hitbox"], velocity)

                if velocity.x != 0 or velocity.y != 0: # si on se deplace toujours alors :

                    # gestion du vecteur position
                    self.player_data[name]["position"] += velocity * 2
                    # la position de la hitbox se cale sur le vecteur position
                    self.player_data[name]["hitbox"].topleft = self.player_data[name]["position"]

                    # gestion de la direction /// en attente de animation up et down
                    if velocity.x < 0:
                        direction = "left"
                    elif velocity.x > 0:
                        direction = "right"

                    self.player_data[name]["direction"] = direction
            
            dico_sortant[name] = {
                "position": list(self.player_data[name]["position"]),
                "moving_intent": moving_intent,
                "direction": direction
            }
        return dico_sortant