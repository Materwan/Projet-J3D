import pygame
from moteur import Moteur

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
        self.keybinds = None # il sera defini quand on passe du menu au game
    
        self.hitbox = pygame.Rect(x, y, 32, 15)
        self.velocity = [0, 0]
        self.direction = "right"


    def event(self, keys):
        # gestion de la vélocité en regardant les touches pressées
        self.velocity[0] = int(keys[self.keybinds["right"]]) - int(
            keys[self.keybinds["left"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en x
        self.velocity[1] = int(keys[self.keybinds["down"]]) - int(
            keys[self.keybinds["up"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en y

    def update(self):
        # gestion collision
        nearby_obstacles = self.moteur.get_nearby_obstacles(self.hitbox)
        self.velocity = self.moteur.collision(self.hitbox, self.velocity, nearby_obstacles)

        # gestion de la position de la hitbox / modifie la position de la hitbox en décalant de x, y
        self.hitbox.move_ip(self.velocity[0] * 2, self.velocity[1] * 2)

        # gestion de la direction via self.dico /// en attente de animation up et down
        if self.velocity[0] == -1:
            self.direction = "left"
        elif self.velocity[0] == 1:
            self.direction = "right"

        self.Animation.update(self.direction, self.velocity != [0, 0])

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
        # gestion de la vélocité en regardant les touches pressées
        self.Lplayer["player1"][1][0] = int(keys[self.keybinds["right"]]) - int(
            keys[self.keybinds["left"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en x
        self.Lplayer["player1"][1][1] = int(keys[self.keybinds["down"]]) - int(
            keys[self.keybinds["up"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en y

    def receive_info(self):
        """
        recupere des infos : (nom, keybinds, touche appuyé) des joueurs 
        """
        pass

    def update(self):
        """
        traite les infos donc gestion de la velocité, hitbox, direction, collision pour tous les joueurs
        """
        pass

    def give_info(self):
        """
        donne des infos a tous les joueurs : (la carte (ou seed) une fois) 
        et (position, direction, bool) des joueurs  
        """
        pass

    def display(self):
        """
        affiche tous les joueurs grâce à leurs positions, directions et bool (bool = en mouvement)
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
    
    def event(self):
        pass

    def give_info(self):
        """
        donne des infos : nom, keybinds, touche appuyé, ...
        """
        pass

    def receive_info(self):
        """
        recupere une info unique : la carte (ou seed)
        recupere des infos : (position, direction, bool) des joueurs  
        """
        pass

    def update(self):
        """
        gere au moins l'animation de chaque joueur
        """
        pass

    def display(self):
        """
        affiche tous les joueurs grâce à leurs positions, directions et bool (bool = en mouvement)
        """
        pass
