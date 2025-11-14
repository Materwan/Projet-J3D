import pygame

screen = pygame.display.set_mode((0, 0))


class Animation:

    def __init__(self, screen: pygame.surface.Surface):
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

    def __init__(self, screen: pygame.surface.Surface):

        self.screen = screen
        self.position = [0, 0]
        self.speed = [0, 0]
        self.velocity = [0, 0]
        self.direction = "right"
        self.pressed = False

        self.Animation = Animation(self.screen)

    def event(self, events: pygame.event.Event):

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.direction = "right"
                    self.pressed = True
                    self.velocity[0] += 2
                if event.key == pygame.K_LEFT:
                    self.direction = "left"
                    self.pressed = True
                    self.velocity[0] += -2
                if event.key == pygame.K_DOWN:
                    self.direction = "down"
                    self.pressed = True
                    self.velocity[1] += 2
                if event.key == pygame.K_UP:
                    self.direction = "up"
                    self.pressed = True
                    self.velocity[1] += -2

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.pressed = False
                    self.velocity[0] -= 2
                if event.key == pygame.K_LEFT:
                    self.pressed = False
                    self.velocity[0] -= -2
                if event.key == pygame.K_DOWN:
                    self.pressed = False
                    self.velocity[1] -= 2
                if event.key == pygame.K_UP:
                    self.pressed = False
                    self.velocity[1] -= -2

    def update(self):

        if self.pressed:
            self.speed[0] += self.velocity[0]
            self.speed[1] += self.velocity[1]

        self.position[0] += self.speed[0]
        self.position[1] += self.speed[1]

        self.speed = [0, 0]

        if self.pressed:
            self.Animation.frame += 1
        else:
            self.Animation.frame = 0
        self.Animation.update(self.direction)

    def display(self):

        self.Animation.display(self.position)
