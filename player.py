import pygame
from moteur import Moteur
from animations import AnimationController, create_player_animation
from typing import Tuple, Dict


class Player:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.moteur = Moteur(self.screen)
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }
        self.position = pygame.Vector2(x, y)
        self.hitbox = pygame.Rect(x, y, 32, 15)
        self.velocity = pygame.Vector2(0, 0)  # == [0, 0]
        self.direction = "right"

    def event(self, keys: Tuple[bool]):
        # gestion de la vélocité en regardant les touches pressées
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
        )
        # vaut soit -1, 0 ou 1 pour la velocité en x et en y

    def update(self):
        moving_intent = self.velocity.length_squared() > 0
        if moving_intent: # si le joueur veut se deplacer alors :

            # gestion collision
            self.moteur.collision(self.hitbox, self.velocity, None)

            is_moving = self.velocity.length_squared()
            if is_moving > 0: # si on se deplace toujours alors :

                # gestion des déplacements en diagonales
                if is_moving > 1: # si deplacement en diagonale
                    self.velocity.normalize_ip() # [1, 1] devient [0.707107, 0.707107]

                # gestion du vecteur position
                self.position += self.velocity * 2
                # la position de la hitbox se cale sur le vecteur position
                self.hitbox.topleft = self.position

                # gestion de la direction /// en attente de animation up et down
                if self.velocity.x < 0:
                    self.direction = "left"
                elif self.velocity.x > 0:
                    self.direction = "right"

        self.animation.update(moving_intent, self.direction)

    def display(self):
        self.animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox, 2) # pour voir la hitbox du joueur (pas touche)



class Host:
    def __init__(self, screen, x, y):
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.host_animation = AnimationController(animation_images, screen)
        self.guest_animation = AnimationController(animation_images, screen)
        self.moteur = Moteur(screen)

        self.host_data = {
            "position" : pygame.Vector2(x, y),
            "hitbox" : pygame.Rect(x, y, 32, 15),
            "direction" : "right",
            "moving_intent" : True
        }
        self.guest_data = {
            "position" : pygame.Vector2(x+100, y),
            "hitbox" : pygame.Rect(x+100, y, 32, 15),
            "direction" : "right",
            "moving_intent" : True
        }
        self.connected = False # True si client connecté

        self.velocity = pygame.Vector2(0, 0)
        self.look_direction = pygame.Vector2(1, 0)
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }


    def event(self, keys: Tuple[bool]):
        """
        Détermine le vecteur de mouvement à partir des entrées clavier.
        
        Utilise une soustraction binaire pour calculer la direction :
        - (1 - 0) = 1  (Droite/Bas)
        - (0 - 1) = -1 (Gauche/Haut)
        - (1 - 1) ou (0 - 0) = 0 (Neutre)
        
        Le vecteur 'self.velocity' ainsi mis à jour contient des composantes 
        x et y allant de -1 à 1, permettant aussi la gestion des diagonales.
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )


    def update(self):
        """
        - doit recuperer : la vélocité de client
        - traite l'info : verification velocité
        - gestion collision, position et direction de tous les joueurs
        - gestion de l'animation de chaque joueur (frame)
        - doit envoyer des infos : position, vélocité 
          de hote et la position de client + (une fois la map ou seed)
        """
        self.host_data["moving_intent"] = self.velocity.length_squared() > 0
        if self.host_data["moving_intent"]:
            # gestion de look_direction pour les attaques dans le future 
            self.look_direction = self.velocity.normalize()

            # gestion collision
            if self.connected:
                self.moteur.collision(self.host_data["hitbox"], self.velocity, self.guest_data["hitbox"])
            else:
                self.moteur.collision(self.host_data["hitbox"], self.velocity, None)

            is_moving = self.velocity.length_squared()
            if is_moving > 0: # si on se deplace toujours alors :
                
                # gestion des déplacements en diagonales
                if is_moving > 1:
                    self.velocity.normalize_ip() # [1, 1] devient [0.707107, 0.707107]

                # gestion du vecteur position
                self.host_data["position"] += self.velocity * 2
                # la position de la hitbox se cale sur le vecteur position
                self.host_data["hitbox"].topleft = self.host_data["position"]

                # gestion de la direction
                if self.velocity.x > 0:
                    self.host_data["direction"] = "right"
                elif self.velocity.x < 0:
                    self.host_data["direction"] = "left"
                """ Optionnel : en attente animation up et down
                elif self.velocity.y > 0:
                    self.host_data["direction"] = "down"
                elif self.velocity.y < 0:
                    self.host_data["direction"] = "up"
                """
        
        # GESTION RESEAU

        # reçoie des infos du client
        data_to_receive = {"velocity": [0, 0]}

        # envoie des infos au client
        data_to_send = self.handle_client_data(data_to_receive)

        # FIN GESTION RESEAU

        # gestion animation frame pour hôte (et client si connecté)
        self.host_animation.update(self.host_data["moving_intent"], self.host_data["direction"])
        if self.connected:
            self.guest_animation.update(self.guest_data["moving_intent"], self.guest_data["direction"])


    def display(self):
        """
        Gère le rendu graphique des joueurs (Hôte et Client) à l'écran.
        
        Calcule les coordonnées d'affichage en appliquant un décalage
        pour centrer les sprites par rapport à leurs positions logiques.
        
        Note : Les offsets (-34, -70) permettent d'aligner le bas du sprite 
        avec la position de la hitbox.
        """
        self.host_animation.display((self.host_data["hitbox"].x - 34, self.host_data["hitbox"].y - 70))
        if self.connected:
            self.guest_animation.display((self.guest_data["hitbox"].x - 34, self.guest_data["hitbox"].y - 70))


    def handle_client_data(self, data_to_receive):
        """
        Traite les données envoyées par le client, applique la physique et 
        prépare le paquet réseau de réponse.

        Cette méthode à trois étapes principales:
        1. Validation : Vérifie et normalise la vélocité reçue pour éviter les triches.
        2. Physique : Gère les collisions entre le client, le décor et l'hôte.
        3. Mise à jour : Applique le déplacement final et met à jour l'orientation.

        Args:
            data_to_receive (dict): Contient la vélocité souhaitée par le client.

        Returns:
            dict: État synchronisé incluant les positions réelles, directions et intentions.
        """
        # verification de la velocité et des déplacements en diagonales
        velocity, self.guest_data["moving_intent"] = self.moteur.verif_velocity(data_to_receive["velocity"])
        if self.guest_data["moving_intent"]:

            # gestion collision
            self.moteur.collision(self.guest_data["hitbox"], velocity, self.host_data["hitbox"])

            if velocity.x != 0 or velocity.y != 0: # si on se deplace toujours alors :

                # gestion du vecteur position
                self.guest_data["position"] += velocity * 2
                # la position de la hitbox se cale sur le vecteur position
                self.guest_data["hitbox"].topleft = self.guest_data["position"]

                # gestion de la direction
                if velocity.x > 0:
                    self.guest_data["direction"] = "right"
                elif velocity.x < 0:
                    self.guest_data["direction"] = "left"
                """ Optionnel : en attente animation up et down
                elif velocity.y > 0:
                    self.guest_data["direction"] = "down"
                elif velocity.y < 0:
                    self.guest_data["direction"] = "up"
                """
        
        return {"host" : {"position" : list(self.host_data["position"]), 
                        "moving_intent" : self.host_data["moving_intent"], 
                        "direction" : self.host_data["direction"]}, 
                "guest" : {"position" : list(self.guest_data["position"])}}
        


class Guest:
    def __init__(self, screen):
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.host_animation = AnimationController(animation_images, screen)
        self.guest_animation = AnimationController(animation_images, screen)

        self.host_data = {
            "position" : [100, 100],
            "direction" : "right",
            "moving_intent" : False
        }
        self.guest_data = {
            "position" : [300, 300],
            "direction" : "right",
            "moving_intent" : False
        }
        
        self.velocity = pygame.Vector2(0, 0)
        self.look_direction = pygame.Vector2(1, 0)
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }


    def event(self, keys: Tuple[bool]):
        """
        Détermine le vecteur de mouvement à partir des entrées clavier.
        
        Utilise une soustraction binaire pour calculer la direction :
        - (1 - 0) = 1  (Droite/Bas)
        - (0 - 1) = -1 (Gauche/Haut)
        - (1 - 1) ou (0 - 0) = 0 (Neutre)
        
        Le vecteur 'self.velocity' ainsi mis à jour contient des composantes 
        x et y allant de -1 à 1, permettant aussi la gestion des diagonales.
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )


    def update(self):
        """
        Gère l'update côté client à chaque frame.
        
        Cette méthode effectue trois actions principales :
        1. Détermine l'intention de mouvement et la direction cardinale du Client.
        2. Synchronise les données avec le serveur (Envoi / Réception).
        3. Met à jour l'état des animations pour le Client et l'Hôte.
        """
        self.guest_data["moving_intent"] = self.velocity.length_squared() > 0
        if self.guest_data["moving_intent"]:
            # gestion de look_direction pour les attaques dans le future 
            self.look_direction = self.velocity.normalize()

            # gestion de la direction
            if self.velocity.x > 0:
                self.guest_data["direction"] = "right"
            elif self.velocity.x < 0:
                self.guest_data["direction"] = "left"
            """ Optionnel : en attente animation up et down
            elif self.velocity.y > 0:
                self.guest_data["direction"] = "down"
            elif self.velocity.y < 0:
                self.guest_data["direction"] = "up"
            """
        
        # GESTION RESEAU

        # envoie info à l'hôte
        data_to_send = {"velocity": list(self.velocity)}

        # reçoie info de l'hôte
        data_to_receive = {"host" : {"position" : [595, 1474],
                                      "moving_intent" : True,
                                        "direction" : "right"}, 
                            "guest" : {"position" : [2, 36]}}
        
        self.update_data(data_to_receive)

        # FIN GESTION RESEAU
        
        # gestion animation frame pour client et hôte
        self.guest_animation.update(self.guest_data["moving_intent"], self.guest_data["direction"])
        self.host_animation.update(self.host_data["moving_intent"], self.host_data["direction"])


    def display(self):
        """
        Gère le rendu graphique des joueurs (Client et Hôte) à l'écran.
        
        Calcule les coordonnées d'affichage en appliquant un décalage
        pour centrer les sprites par rapport à leurs positions logiques.
        
        Note : Les offsets (-34, -70) permettent d'aligner le bas du sprite 
        avec la position de la hitbox.
        """
        self.guest_animation.display((self.guest_data["position"][0]- 34, self.guest_data["position"][1] - 70))
        self.host_animation.display((self.host_data["position"][0]- 34, self.host_data["position"][1] - 70))


    def update_data(self, data_to_receive: Dict[str, Dict]):
        """
        Met à jour les données stocké par le client à partir du dictionnaire reçu du serveur.
        Synchronise l'hôte et le client (juste la position pour client).
        """
        if "host" in data_to_receive:
            host_info = data_to_receive["host"]
            
            # On met à jour la position (on convertit la liste en Vector2)
            self.host_data["position"] = pygame.Vector2(host_info["position"])
            
            # On met à jour le reste
            self.host_data["direction"] = host_info["direction"]
            self.host_data["moving_intent"] = host_info["moving_intent"]

        if "guest" in data_to_receive:
            guest_info = data_to_receive["guest"]
            
            # On met à jour la position (validée par le serveur)
            self.guest_data["position"] = pygame.Vector2(guest_info["position"])
            
            # Note: moving_intent et direction du client sont déjà gérés localement dans update()