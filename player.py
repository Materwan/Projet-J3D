import pygame

screen = pygame.display.set_mode((0, 0))

ANIMATIONS = {"right": ["runAnimation/run animation frame 1.png",
                        "runAnimation/run animation frame 2.png",
                        "runAnimation/run animation frame 3.png"],
              "left": ["runAnimation/run animation frame 1.png",
                       "runAnimation/run animation frame 2.png",
                       "runAnimation/run animation frame 3.png"]}
flip = False
for x in ANIMATIONS.keys():
    ANIMATIONS[x] = list(map(lambda i: pygame.transform.flip(pygame.transform.scale(pygame.image.load(i).convert_alpha(), (100, 100)), flip_x=flip, flip_y=False), ANIMATIONS[x]))
    flip = True

class Player:

    def __init__(self, screen: pygame.surface.Surface):
        self.screen = screen
        self.position = [0, 0]
        self.speed = [0, 0]
        self.velocity =  [0, 0]
        self.direction = "right"
        self.pressed = False
    
    def event(self, events: pygame.event.Event):
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.direction = "right"
                    self.pressed = True
                    self.velocity[0] = 2
                if event.key == pygame.K_LEFT:
                    self.direction = "left"
                    self.pressed = True
                    self.velocity[0] = -2
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.pressed = False
                    self.velocity[0] = 0
                if event.key == pygame.K_LEFT:
                    self.pressed = False
                    self.velocity[0] = 0
    
    def update(self):
        #print(self.pressed)
        if self.pressed:
            self.speed[0] += self.velocity[0]
            self.speed[1] += self.velocity[1]

        self.position[0] += self.speed[0]
        self.position[1] += self.speed[1]

        self.speed = [0, 0]

    def display(self):
        self.screen.blit(ANIMATIONS[self.direction][0], self.position)
