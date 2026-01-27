import pygame
from moteur import Moteur
from typing import Tuple

def load_image(path: str, size: tuple[int, int]) -> pygame.surface.Surface:

    image = pygame.image.load(path)  # Import image as surface
    image = image.convert_alpha()  # Make background transparent
    image = pygame.transform.scale(image, size=size)  # Resize image

    return image


class Animation:
    def __init__(self, screen):
        self.screen = screen
        self.frame = 0
        self.last_direction = "right"
        self.path = "Ressources/Animations/runAnimation/"
        self.images = [
            "run animation frame 1.png",
            "run animation frame 2.png",
            "run animation frame 3.png",
        ]

        # Load all images
        for index in range(len(self.images)):
            self.images[index] = load_image(self.path + self.images[index], (100, 100))

        # For each direction flip image
        self.right = [image for image in self.images]
        self.left = [
            pygame.transform.flip(image, flip_x=True, flip_y=False)
            for image in self.images
        ]
        # There is no animation for up and down for now
        self.up = [image for image in self.right]
        self.down = [image for image in self.left]

    def update(self, direction, bool):

        # gestion des frames selon si touche appuyer ou non (bool = True si une des 4 touches motrice appuyé)
        if bool:
            self.frame += 1
        else:
            self.frame = 0
        
        if self.last_direction != direction:
            self.frame = 0
            self.last_direction = direction

        elif self.frame >= 60:
            self.frame = 0

    def display(self, pos):
        if self.last_direction == "right":
            images = self.right
        elif self.last_direction == "up":
            images = self.up
        elif self.last_direction == "left":
            images = self.left
        elif self.last_direction == "down":
            images = self.down
        else:
            images = self.right
        self.screen.blit(images[self.frame // 6 % 3], pos)


class Player:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.moteur = Moteur(self.screen)
        self.Animation = Animation(self.screen)
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        } # il sera defini quand on passe du menu au game
    
        self.hitbox = pygame.Rect(x, y, 32, 15)
        self.velocity = pygame.Vector2(0, 0) # == [0, 0]
        self.direction = "right"
        self.is_moving = False


    def event(self, keys: Tuple[bool]):
        # gestion de la vélocité en regardant les touches pressées
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )
        # vaut soit -1, 0 ou 1 pour la velocité en x et en y 

    def update(self):
        moving_intent = self.velocity.length_squared() > 0
        if moving_intent: # si le joueur veut se deplacer alors :

            # gestion collision
            self.moteur.collision(self.hitbox, self.velocity)

            is_moving = self.velocity.length_squared()
            if is_moving > 0: # si on se deplace toujours alors :
                
                # gestion des déplacements en diagonales
                if is_moving > 1: # si deplacement en diagonale
                    self.velocity.normalize_ip() # [1, 1] devient [0.707107, 0.707107]
            
                # gestion de la position de la hitbox / modifie la position de la hitbox en décalant de x et y
                self.hitbox.move_ip(self.velocity.x * 2, self.velocity.y * 2)

                # gestion de la direction /// en attente de animation up et down
                if self.velocity.x < 0:
                    self.direction = "left"
                elif self.velocity.x > 0:
                    self.direction = "right"

        self.Animation.update(self.direction, moving_intent)

    def display(self):
        self.Animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox, 2) # pour voir la hitbox du joueur (pas touche)



class Hôte:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.moteur = Moteur(self.screen)
        self.Animation = Animation(self.screen)
        self.keybinds = None
        
        self.Lplayer = {"player1" : [pygame.Rect(x,y,32,15), [0,0], "right", self.keybinds]}
        # dico des infos des joueurs : hitbox, velocité, direction, config de touche, ext..

    def event(self, keys):
        """
        Modifie la vélocité en regardant les touches pressées
        x et y vale chacun soit -1, 0 ou 1
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )

    def update(self):
        """
        - doit recuperer : la vélocité de tous les joueurs
        - traite l'info : verification velocité
        - gestion collision, position et direction de tous les joueurs
        - gestion de l'animation de chaque joueur (frame)
        - doit envoyer des infos : position, direction 
          et is_moving de tous les joueurs (une fois la map ou seed)
        """
        pass

    def display(self):
        """
        affiche tous les joueurs grâce à leurs positions, directions et is_moving
        """
        pass

    def new_player(self, x, y, keybinds): # prendra en argument le nom du joueur
        """
        Ajoute le client à la liste des joueurs
        """
        self.Lplayer["player"+str(len(self.Lplayer)+1)] = [pygame.Rect(x,y,32,15), [0,0], "right", keybinds]
    
    def del_player(self, name):
        """
        Supprime le client de la liste des joueurs grâce à son nom
        """
        del self.Lplayer[name]


class Client:
    def __init__(self, screen):
        self.screen = screen
        self.Animation= Animation(self.screen)
        self.keybinds = None
    
    def event(self, keys):
        """
        Modifie la vélocité en regardant les touches pressées
        x et y vale chacun soit -1, 0 ou 1
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )

    def update(self):
        """
        - doit donner des infos : vélocité, ...
        - gestion de l'animation de chaque joueur (frame)
        - doit recuperer des infos : position, direction 
          et is_moving de tous les joueurs (une fois la map ou seed)
        """
        pass

    def display(self):
        """
        affichage de tous les joueurs via Animation
        grâce à leurs positions, directions et is_moving
        """
        pass