import pygame


def load_image(path: str, size: tuple[int, int]) -> pygame.surface.Surface:

    image = pygame.image.load(path)  # Import image as surface
    image = image.convert_alpha()  # Make background transparent
    image = pygame.transform.scale(image, size=size)  # Resize image

    return image


class Animation:
    def __init__(self, screen):
        self.screen = screen
        self.last_direction = "right"
        self.path = "runAnimation/"
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

    def update(self, direction):
        if self.last_direction != direction:
            self.frame = 0
            self.last_direction = direction

        if self.frame >= 60:
            self.frame = 0

    def display(self, pos):
        if self.last_direction == "rigth":
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
        self.velocity[0] = int(keys[self.keybinds["right"]]) - int(
            keys[self.keybinds["left"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en x
        self.velocity[1] = int(keys[self.keybinds["down"]]) - int(
            keys[self.keybinds["up"]]
        )  # vaut soit 0, 1 ou -1 pour la vélocité en y

    def update(self, keybinds):
        # reception des touches
        self.keybinds = keybinds

        # gestion collision
        self.velocity = self.moteur.collision(self.velocity, self.hitbox)

        # gestion de la position de la hitbox / modifie la position de la hitbox en décalant de x, y
        self.hitbox.move_ip(
            self.velocity[0] * self.speed, self.velocity[1] * self.speed
        )

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
