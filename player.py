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
        if moving_intent:  # si le joueur veut se deplacer alors :

            # gestion collision
            self.moteur.collision(self.hitbox, self.velocity)

            is_moving = self.velocity.length_squared()
            if is_moving > 0:  # si on se deplace toujours alors :

                # gestion des déplacements en diagonales
                if is_moving > 1:  # si deplacement en diagonale
                    self.velocity.normalize_ip()  # [1, 1] devient [0.707107, 0.707107]

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


class Hôte:
    def __init__(self, screen, x, y, name):
        self.screen = screen
        self.moteur = Moteur(self.screen)
        animation_images = create_player_animation(
            r"Ressources\Animations\Idle_Animations",
            r"Ressources\Animations\runAnimation",
            (100, 100),
        )
        self.animation = AnimationController(animation_images, self.screen)
        self.moteur.new_player(name, x, y)
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }
        self.velocity = pygame.Vector2(0, 0) # == [0, 0]
        self.position = None
        self.direction = "right"

    def event(self, keys):
        """
        Modifie la vélocité en regardant les touches pressées
        x et y vale chacun soit -1, 0 ou 1
        """
        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]]
        )

    def update(self, dico):
        """
        - doit recuperer : la vélocité de tous les joueurs
        - traite l'info : verification velocité
        - gestion collision, position et direction de tous les joueurs
        - gestion de l'animation de chaque joueur (frame)
        - doit envoyer des infos : position, vélocité 
          de tous les joueurs + (une fois la map ou seed)
        """
        return self.moteur.handle_info(dico)

    def display(self):
        """
        affichage de tous les joueurs via Animation
        grâce à leurs positions, directions et moving_intent
        """
        pass


class Client:
    def __init__(self, screen):
        self.screen = screen
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
        self.velocity = pygame.Vector2(0, 0) # == [0, 0]
        self.position = None
        self.direction = "right"

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
          et moving_intent de tous les joueurs + (une fois la map ou seed)
        """
        pass

    def display(self):
        """
        affichage de tous les joueurs via Animation
        grâce à leurs positions, directions et moving_intent
        """
        pass