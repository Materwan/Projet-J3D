import pygame

screen = pygame.display.set_mode((700, 700))

animation = ["Projet-J3D/runAnimation/run animation frame 1.png",
             "Projet-J3D/runAnimation/run animation frame 2.png",
             "Projet-J3D/runAnimation/run animation frame 3.png"]

animation = list(map(lambda x: pygame.transform.scale(pygame.image.load(x).convert_alpha(), (100, 100)), animation))

class Game:

    def __init__(self):
        self.running = True
        self.screen = screen
        self.pressed = False
        self.frame = 0
        self.i = 0
        self.position = [0, 0]
        self.clock = pygame.time.Clock()

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.pressed = True
                    self.frame = 1
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    self.pressed = False

        if self.pressed:
            self.i = self.frame // 6 % 3

    def update(self):
        self.frame = self.frame + 1 if self.frame < 59 else 0
        if self.pressed:
            self.position[0] += 2

    def display(self):
        self.screen.fill((0, 0, 0))
        self.screen.blit(animation[self.i], self.position)
        pygame.display.update( )

    def run(self):

        while self.running == True:

            self.event()
            self.update()
            self.display()

            self.clock.tick(60) # à ne pas toucher
