import pygame

pygame.init()

WINDOWS = pygame.display.get_desktop_sizes()[0]   #dimention de l'écran

screen = pygame.display.set_mode(WINDOWS)
clock = pygame.time.Clock()
running = True

bouton = pygame.Rect(WINDOWS[0]-200,0,200,200)
surface = pygame.Surface((200,200))
color = pygame.Color(0,255,0)

while running:
    
    screen.fill((0, 0, 0)) #background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN: #si bouton est cliqué alors on ferme le menu
            x,y = pygame.mouse.get_pos()
            if bouton.collidepoint(x,y):
                running = False


    surface.fill((0, 0, 255))                #affichage du bouton
    pygame.draw.rect(surface,color,bouton)
    screen.blit(surface, (WINDOWS[0]-200, 0))

    pygame.display.update()


    clock.tick(60)

pygame.quit()