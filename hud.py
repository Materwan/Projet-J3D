import pygame
from camera_system import Camera
from particule import spawn_local_particle
from player import SoloPlayerController, HostController, GuestController


class HUD:
    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
    ):
        self.screen = screen
        self.camera = camera
        self.player_controller: (
            SoloPlayerController | HostController | GuestController
        ) = None

        self.size = 120
        self.particles = pygame.sprite.Group()
        self.max_pv = None
        self.pv = None

        self.gap = self.size // 3
        self.margin_x = 20
        self.margin_y = 20

        self.anim_timer = 0
        self.is_flashing = False

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

    def update(self, dt):
        current_time = pygame.time.get_ticks()

        new_pv = self.player_controller.pv

        # si perte de PV alors déclencher les effets visuels
        if new_pv < self.pv:
            self.anim_timer = current_time
            self.is_flashing = True
            for _ in range(10):
                spawn_local_particle(
                    group=self.particles,
                    pos=(
                        self.margin_x + ((self.pv - 2) * self.gap) + (self.size * 0.45),
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
            if self.pv == 1:
                self.camera.start_shake(intensity=15, duration=30)
            else:
                self.camera.start_shake(intensity=8, duration=8)

        self.pv = new_pv

        if self.is_flashing and (current_time - self.anim_timer) > 60:
            self.is_flashing = False

        self.particles.update(dt)

    def draw(self):
        for i in range(self.max_pv):
            x = self.margin_x + (i * self.gap)
            y = self.margin_y

            # HP : état normal
            if i < self.pv:
                self.screen.blit(self.base_heart, (x, y))

            # HP : flash blanc
            elif i == self.pv and self.is_flashing:
                self.screen.blit(self.damaged_heart, (x, y))

            # HP : vide
            else:
                self.screen.blit(self.empty_heart, (x, y))

        self.particles.draw(self.screen)
