import pygame
from camera_system import Camera
from particule import spawn_local_particle


class HUD:
    def __init__(self, screen: pygame.Surface, camera: Camera):
        # --- RÉGLAGE TAILLE ET ÉCART ---
        self.screen = screen
        self.camera = camera

        self.size = 120
        self.particles = pygame.sprite.Group()
        self.max_health = 12
        self.health = 12
        self.gap = self.size // 3

        self.margin_x = 20
        self.margin_y = 20

        self.anim_timer = 0
        self.is_flashing = False
        self.take_damage = False

        # image :
        self.base_heart = pygame.transform.scale(
            pygame.image.load("Ressources/HUD/sprite_5.png").convert_alpha(),
            (self.size, self.size),
        )
        self.damaged_heart = pygame.transform.scale(
            pygame.image.load("Ressources/HUD/sprite_6.png").convert_alpha(),
            (self.size, self.size),
        )
        self.empty_heart = pygame.transform.scale(
            pygame.image.load("Ressources/HUD/sprite_7.png").convert_alpha(),
            (self.size, self.size),
        )

    # affichage du HUD
    def draw(self, dt):
        current_time = pygame.time.get_ticks()

        if self.take_damage:
            self.take_damage = False
            self.health = max(0, self.health - 1)
            self.anim_timer = current_time
            self.is_flashing = True

            ## effet de particule
            for i in range(10):
                spawn_local_particle(
                    group=self.particles,
                    pos=(
                        self.margin_x
                        + ((self.health - 1) * self.gap)
                        + (self.size * 0.45),
                        self.margin_y + (self.size * 0.23),
                    ),
                    sprite_path="Ressources/particles/damage.png",
                    chaos=0,
                    speed_range=(150, 400),
                    rot=0,
                    angles=(0, 360),
                    shrink_range=(12, 40),
                    size=7,
                )

            ## effet de caméra
            self.camera.start_shake(intensity=8, duration=8)

        if self.is_flashing and (current_time - self.anim_timer) > 60:
            self.is_flashing = False

        for i in range(self.max_health):
            x = self.margin_x + (i * self.gap)
            y = self.margin_y

            # HP : état normal
            if i < self.health:
                self.screen.blit(self.base_heart, (x, y))

            # HP : flash blanc
            elif i == self.health and self.is_flashing:
                self.screen.blit(self.damaged_heart, (x, y))

            # HP : vide
            else:
                self.screen.blit(self.empty_heart, (x, y))

            self.particles.update(dt)
            self.particles.draw(self.screen)
