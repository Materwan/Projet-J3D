import pygame
from player import Player

screen = pygame.display.set_mode((700, 700))

animation = ["runAnimation/run animation frame 1.png",
             "runAnimation/run animation frame 2.png",
             "runAnimation/run animation frame 3.png"]

animation = list(map(lambda x: pygame.transform.scale(pygame.image.load(x).convert_alpha(), (100, 100)), animation))

class Game:

    def __init__(self):
        self.running = True
        self.screen = screen
        self.pressed = False
        self.frame = 0
        self.i = 0
        self.position = [0, 0]
        self.player = Player(self.screen)
        self.clock = pygame.time.Clock()

    def event(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

        self.player.event(events)

    def update(self):
        self.player.update()

    def display(self):
        self.screen.fill((0, 0, 0))
        self.player.display()
        #self.screen.blit(animation[self.i], self.position)
        pygame.display.update( )

    def run(self):

        while self.running == True:

            self.event()
            self.update()
            self.display()

            self.clock.tick(60) # à ne pas toucher
