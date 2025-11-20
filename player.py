import pygame

class Animation:
    def __init__(self, screen):
        self.path = "runAnimation/"
        self.images = {}
        flip = False
        self.last_direction = "right"
        self.frame = 0
        self.screen = screen

        for key in ["right", "left", "up", "down"]:

            self.images[key] = []

            for i in range(3):

                self.images[key].append(
                    pygame.transform.flip(
                        pygame.transform.scale(
                            pygame.image.load(
                                f"{self.path}run animation frame {i+1}.png"
                            ).convert_alpha(),
                            (100, 100),
                        ),
                        flip_x=flip,
                        flip_y=False,
                    )
                )
            flip = True


    def update(self, direction):
        if self.last_direction != direction:
            self.frame = 0
            self.last_direction = direction

        if self.frame >= 60:
            self.frame = 0


    def display(self, pos):
        self.screen.blit(self.images[self.last_direction][self.frame // 6 % 3], pos)


class Player:
    def __init__(self, screen, x, y, moteur):
        self.moteur = moteur
        self.screen = screen
        self.velocity = [0, 0]
        self.speed = 2
        self.direction = "right"
        self.dico = {(1, 0): "right", (-1, 0): "left", (0, 1): "down", (0, -1): "up"}
        self.Animation = Animation(self.screen)
        self.hitbox = pygame.Rect(x, y, 32, 15)


    def event(self, keys):
        # gestion de la vélocité en regardant les touches pressées
        self.velocity[0] = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT]) # vaut soit 0, 1 ou -1 pour la vélocité en x
        self.velocity[1] = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP]) # vaut soit 0, 1 ou -1 pour la vélocité en y


    def update(self):
        # gestion collision
        self.velocity = self.moteur.collision(self.velocity, self.hitbox)

        # gestion de la position de la hitbox / modifie la position de la hitbox en décalant de x, y
        self.hitbox.move_ip(self.velocity[0] * self.speed, self.velocity[1] * self.speed)

        # gestion de la direction via self.dico
        if (self.velocity[0], self.velocity[1]) in self.dico: 
            self.direction = self.dico[(self.velocity[0], self.velocity[1])]

        # gestion des frames selon si touche appuyer ou non
        if (self.velocity[0], self.velocity[1]) != (0, 0):
            self.Animation.frame += 1
        else:
            self.Animation.frame = 0
        self.Animation.update(self.direction)   


    def display(self):
        self.Animation.display((self.hitbox.x - 34, self.hitbox.y - 70))
        # pygame.draw.rect(self.screen, "red", self.hitbox) / pour voir la hitbox (pas touche)
