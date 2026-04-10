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
        self.gap = self.size / 3

        self.margin_x = 20
        self.margin_y = 20

        self.anim_timer = 0
        self.is_flashing = False
        self.h_was_pressed = False

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

        keys = pygame.key.get_pressed()
        if keys[pygame.K_h]:
            if not self.h_was_pressed:
                self.health = max(0, self.health - 1)
                self.anim_timer = current_time
                self.is_flashing = True
                self.h_was_pressed = True

                ## effet de particule

                damaged_index = self.health - 1
                pos_x = self.margin_x + (damaged_index * self.gap) + self.size // 2
                pos_y = self.margin_y + self.size // 2 - 40
                for i in range(10):
                    spawn_local_particle(
                        group=self.particles,
                        pos=(pos_x, pos_y),
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
        else:
            self.h_was_pressed = False

        if self.is_flashing and (current_time - self.anim_timer) > 50:
            self.is_flashing = False

        max_h = self.max_health
        current_h = self.health

        for i in range(max_h):
            x = self.margin_x + (i * self.gap)
            y = self.margin_y

            # HP état normal ( pas perdu quoi )
            if i < current_h:
                self.screen.blit(self.base_heart, (x, y))

            # HP quand on se fait taper ( flash blanc)
            elif i == current_h and self.is_flashing:
                self.screen.blit(self.damaged_heart, (x, y))

            # HP vide
            else:
                self.screen.blit(self.empty_heart, (x, y))

            self.particles.update(dt)
            self.particles.draw(self.screen)
