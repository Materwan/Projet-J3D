import pygame
from random import uniform, randint
from constants import SCREEN_WIDTH, SCREEN_HEIGHT

CACHED_IMAGES = {}

class Particle(pygame.sprite.Sprite):
    def __init__(self, groups, pos, image, speed, rotation_speed, angle_range, chaos, shrink_speed, size):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        
        # Direction
        angle = uniform(angle_range[0], angle_range[1])
        self.direction = pygame.math.Vector2(1, 0).rotate(angle)
        
        self.speed = speed # Vitesse déjà calculée (fixe ou aléatoire)
        self.base_image = image
        self.angle = uniform(0, 360)
        self.rotation_speed = rotation_speed
        self.chaos = chaos
        self.shrink_speed = shrink_speed
        self.size = size
        self.create_surf()  

    def create_surf(self):
        if self.size <= 2: 
            self.kill()
            return
        scaled = pygame.transform.scale(self.base_image, (int(self.size), int(self.size)))
        self.image = pygame.transform.rotate(scaled, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        if self.chaos > 0:
            deviation = pygame.math.Vector2(uniform(-1, 1), uniform(-1, 1)) * self.chaos
            self.direction = (self.direction + deviation).normalize()
            
        self.pos += self.direction * self.speed * dt
        self.angle += self.rotation_speed * dt
        self.size -= self.shrink_speed * dt
        if self.size <= 2:
            self.kill()
        else:
            self.create_surf()

# --- FONCTIONS D'APPEL AVEC ALÉATOIRE ---

def get_image(path):
    if path not in CACHED_IMAGES:
        CACHED_IMAGES[path] = pygame.image.load(path).convert_alpha()
    return CACHED_IMAGES[path]


# Particule qui apparaît à une position définie (pos) avec des paramètres aléatoires
def spawn_local_particle(group, pos, sprite_path, speed_range=(80, 150), rot=200, angles=(0, 360), chaos=0.1, shrink_range=(40, 90), size=30):
    img = get_image(sprite_path)
    
    # --- CALCUL DES VALEURS ALÉATOIRES ICI ---
    # Vitesse aléatoire
    vitesse = uniform(speed_range[0], speed_range[1])
    # Durée de vie aléatoire
    vitesse_shrink = uniform(shrink_range[0], shrink_range[1])
    
    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)


# Particule qui peut apparaître n'importe où à l'écran(sans zone à définir) et avec des paramètres aléatoires
def spawn_global_particle(group, sprite_path, speed_range=(50, 100), rot=200, angles=(0, 360), chaos=0.1, shrink_range=(40, 90), size=30):
    pos = (randint(0, SCREEN_WIDTH), randint(0, SCREEN_HEIGHT))
    img = get_image(sprite_path)
    
    vitesse = uniform(speed_range[0], speed_range[1])
    vitesse_shrink = uniform(shrink_range[0], shrink_range[1])
    
    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)



# comme la global_particles mais avec une zone définie (width, height) au lieu de tout l'écran :)
def spawn_area_particle(group, sprite_path, width, height, speed_range=(50, 100), rot=200, angles=(0, 360), chaos=0.1, shrink_range=(40, 90), size=30):
    pos = (randint(0, width), randint(0, height))
    img = get_image(sprite_path)
    
    vitesse = uniform(speed_range[0], speed_range[1])
    vitesse_shrink = uniform(shrink_range[0], shrink_range[1])
    
    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)