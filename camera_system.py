import pygame
import random


class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

        # variables pour le tremblement de caméra
        self.shake_timer = 0
        self.shake_intensity = 0
        self.offset_x = 0
        self.offset_y = 0

    def start_shake(self, intensity, duration):
        # Démarre / initialise un effet de tremblement de la caméra
        self.shake_intensity_initial = intensity
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration

    def display_map(self, map_obj):
        L = list(map_obj.loaded_chunks.keys())
        L.sort(key=lambda p: p[1] * 10 + p[0], reverse=True)

        for x, y in L:
            chunk_world_x = x * map_obj.chunk_size_pix[0]
            chunk_world_y = y * map_obj.chunk_size_pix[1]

            # Ces deux lignes doivent être DANS la boucle (indentation manquante)
            screen_x = chunk_world_x + self.camera.x + self.offset_x
            screen_y = chunk_world_y + self.camera.y + self.offset_y

            map_obj.screen.blit(map_obj.loaded_chunks[(x, y)], (screen_x, screen_y))

    def apply(self, entity_rect):
        """
        Argument : Rect
        """
        return entity_rect.move(
            self.camera.x + self.offset_x, self.camera.y + self.offset_y
        )

    def update(self, target):
        target: pygame.Rect

        # 1. Calcul de la destination (centrage) - On utilise target_rect maintenant
        target_x = -target.centerx + int(self.width / 2)
        target_y = -target.centery + int(self.height / 2)

        # 2. Fluidité (Lerp)
        self.camera.x += (target_x - self.camera.x) * 0.075
        self.camera.y += (target_y - self.camera.y) * 0.075

        # Tremblement de caméra
        # On applique le décalage directement sur self.camera.x/y
        if self.shake_timer > 0:

            intensity = int(
                self.shake_intensity_initial * (self.shake_timer / self.shake_duration)
            )

            self.offset_x = random.randint(-intensity, intensity)
            self.offset_y = random.randint(-intensity, intensity)
            self.shake_timer -= 1
            self.shake_intensity *= 0.9
        else:
            self.offset_x = 0
            self.offset_y = 0

        # 4. Limites du monde (Clamping)
        # On s'assure que même avec le tremblement, on ne sort pas de la map. BTW erwan faudra renseigner les dimensions de la map dans le constructeur de la caméra pour que ca marche
        self.camera.x = max(-(self.map_width - self.width), min(0, self.camera.x))
        self.camera.y = max(-(self.map_height - self.height), min(0, self.camera.y))
