"Module pour la gestion et création des particules."

import random
from typing import Tuple, List

import pygame

# from main import TAILLE_ECRAN


CACHED_IMAGES = {}


class Particle(pygame.sprite.Sprite):
    """Classe pour une particule."""

    def __init__(
        self,
        groups: pygame.sprite.Group,
        pos: Tuple[int, int] | List[int],
        image: pygame.Surface,
        speed: float,
        rotation_speed: float,
        angle_range: Tuple[int, int] | List[int],
        chaos: float,
        shrink_speed: float,
        size: int,
    ):
        super().__init__(groups)
        self.pos = pygame.Vector2(pos)

        # Direction
        angle = random.uniform(angle_range[0], angle_range[1])
        self.direction = pygame.Vector2(1, 0).rotate(angle)

        self.speed = speed  # Vitesse déjà calculée (fixe ou aléatoire)
        self.base_image = image
        self.angle = random.uniform(0, 360)
        self.rotation_speed = rotation_speed
        self.chaos = chaos
        self.shrink_speed = shrink_speed
        self.size = size
        self.create_surf()

    def create_surf(self):
        """Créer le rectangle de l'image"""

        if self.size <= 2:
            self.kill()
            return
        scaled = pygame.transform.scale(
            self.base_image, (int(self.size), int(self.size))
        )
        self.image = pygame.transform.rotate(scaled, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        """Met à jour l'image, sa rotation, sa taille et sa position."""

        if self.chaos > 0:
            deviation = (
                pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                * self.chaos
            )
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
    """Récupères les images des particules."""

    if path not in CACHED_IMAGES:
        CACHED_IMAGES[path] = pygame.image.load(path).convert_alpha()
    return CACHED_IMAGES[path]


# Particule qui apparaît à une position définie (pos) avec des paramètres aléatoires
def spawn_local_particle(
    group: pygame.sprite.Group,
    pos: Tuple[int, int] | List[int],
    sprite_path: str,
    speed_range: Tuple[int, int] | List[int] | None = (80, 150),
    rot: int | None = 200,
    angles: Tuple[int, int] | List[int] | None = (0, 360),
    chaos: float | None = 0.1,
    shrink_range: Tuple[int, int] | List[int] | None = (40, 90),
    size: int | None = 30,
):
    img = get_image(sprite_path)

    # --- CALCUL DES VALEURS ALÉATOIRES ICI ---
    # Vitesse aléatoire
    vitesse = random.uniform(speed_range[0], speed_range[1])
    # Durée de vie aléatoire
    vitesse_shrink = random.uniform(shrink_range[0], shrink_range[1])

    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)


# Particule qui peut apparaître n'importe où à l'écran(sans zone à définir) et avec des paramètres aléatoires
def spawn_global_particle(
    group: pygame.sprite.Group,
    sprite_path: str,
    speed_range: Tuple[int, int] | List[int] | None = (50, 100),
    rot: int | None = 200,
    angles: Tuple[int, int] | List[int] | None = (0, 360),
    chaos: float | None = 0.1,
    shrink_range: Tuple[int, int] | List[int] | None = (40, 90),
    size: int = 30,
):
    pos = (random.randint(0, 500), random.randint(0, 500))
    img = get_image(sprite_path)

    vitesse = random.uniform(speed_range[0], speed_range[1])
    vitesse_shrink = random.uniform(shrink_range[0], shrink_range[1])

    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)


# comme la global_particles mais avec une zone définie (width, height) au lieu de tout l'écran :)
def spawn_area_particle(
    group: pygame.sprite.Group,
    sprite_path: str,
    width: int,
    height: int,
    speed_range: Tuple[int, int] | List[int] | None = (50, 100),
    rot: int | None = 200,
    angles: Tuple[int, int] | List[int] | None = (0, 360),
    chaos: float | None = 0.1,
    shrink_range: Tuple[int, int] | List[int] | None = (40, 90),
    size: int | None = 30,
):
    pos = (random.randint(0, width), random.randint(0, height))
    img = get_image(sprite_path)

    vitesse = random.uniform(speed_range[0], speed_range[1])
    vitesse_shrink = random.uniform(shrink_range[0], shrink_range[1])

    Particle(group, pos, img, vitesse, rot, angles, chaos, vitesse_shrink, size)
