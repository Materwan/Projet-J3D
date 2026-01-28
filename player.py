import pygame
from moteur import Moteur
from animations import AnimationController, create_player_animation
from typing import Tuple


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
        }  # il sera defini quand on passe du menu au game

        self.hitbox = pygame.Rect(x, y, 32, 15)
        self.velocity = pygame.Vector2(0, 0)  # == [0, 0]
        self.position = pygame.Vector2(x, y)
        self.direction = "right"
        self.is_moving = False

    def event(self, keys: Tuple[bool]):
        # gestion de la vélocité en regardant les touches pressées
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
        )
        # vaut soit -1, 0 ou 1 pour la velocité en x et en y

    def update(self):
        moving_intent = self.velocity.length_squared() > 0
        if moving_intent:  # si le joueur veut se deplacer alors :

            # gestion collision
            self.moteur.collision(self.hitbox, self.velocity)

            is_moving = self.velocity.length_squared()
            if is_moving > 0:  # si on se deplace toujours alors :

                # gestion des déplacements en diagonales
                if is_moving > 1:  # si deplacement en diagonale
                    self.velocity.normalize_ip()  # [1, 1] devient [0.707107, 0.707107]

                # gestion de la position de la hitbox / modifie la position de la hitbox en décalant de x et y
                self.hitbox.move_ip(self.velocity.x * 2, self.velocity.y * 2)
                self.position.update(self.hitbox.x, self.hitbox.y)

                # gestion de la direction /// en attente de animation up et down
                if self.velocity.x < 0:
                    self.direction = "left"
                elif self.velocity.x > 0:
                    self.direction = "right"

        self.animation.update(moving_intent, self.direction)

    def display(self):
        self.animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox, 2) # pour voir la hitbox du joueur (pas touche)


class Hôte:
    def __init__(self, screen, x, y):
        self.screen = screen
        self.moteur = Moteur(self.screen)
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)
        self.keybinds = None

        self.Lplayer = {
            "player1": [pygame.Rect(x, y, 32, 15), [0, 0], "right", self.keybinds]
        }
        # dico des infos des joueurs : hitbox, velocité, direction, config de touche, ext..

    def event(self, keys):
        """
        Modifie la vélocité en regardant les touches pressées
        x et y vale chacun soit -1, 0 ou 1
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
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

    def new_player(self, x, y, keybinds):  # prendra en argument le nom du joueur
        """
        Ajoute le client à la liste des joueurs
        """
        self.Lplayer["player" + str(len(self.Lplayer) + 1)] = [
            pygame.Rect(x, y, 32, 15),
            [0, 0],
            "right",
            keybinds,
        ]

    def del_player(self, name):
        """
        Supprime le client de la liste des joueurs grâce à son nom
        """
        del self.Lplayer[name]


class Client:
    def __init__(self, screen):
        self.screen = screen
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)
        self.keybinds = None

    def event(self, keys):
        """
        Modifie la vélocité en regardant les touches pressées
        x et y vale chacun soit -1, 0 ou 1
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
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
