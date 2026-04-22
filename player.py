"""Module pour la gestion du joueur en solo/multi"""

import time
import pygame
from typing import Tuple, Dict
from moteur import Moteur
from camera_system import Camera
from animations import AnimationController


SPEED = 3


class PlayerControllerBase:
    """Classe de joueur basique.

    Implémente les interactions et l'affichage"""

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        moteur: Moteur,
        start_pos: Tuple[int, int],
    ):
        """Initialise les éléments nécessaires à un joueur"""

        # -- Controlleur --
        self.screen = screen
        self.camera = camera
        self.moteur = moteur
        self.keybinds: Dict = None

        # -- Animations --
        self.animation = AnimationController(
            r"Ressources\Animations\Player", (100, 100), self.screen
        )
        self.im_size = pygame.Vector2(self.animation.im_size)

        # -- Joueur --
        self.position = pygame.Vector2(start_pos)
        self.hitbox = pygame.Rect(0, 0, 25, 15)
        self.hitbox.center = self.position
        self.hitbox_damage = pygame.Rect(0, 0, 30, 45)
        self.hitbox_damage.midbottom = self.position
        self.velocity = pygame.Vector2(0, 0)
        self.direction = "right"
        self.moving_intent = False

        # -- PV --
        self.max_pv = 10
        self.pv = 10

        # -- Invincibilité --
        self.last_hit = 0.0
        self.hit_interval = 1.0

        # -- Mort --
        self.is_dead = False
        self.death_time: float | None = None

        # -- Attaque --
        self.attaque = False
        self.attaque_rect = None
        self.timer: float | None = 0.0
        self.attack_duration = 0.2

    def update_pv(self, modif: int):
        """Met à jour les PV et tue le joueur si besoin."""
        if self.last_hit + self.hit_interval < time.time():

            self.pv = max(0, self.pv + modif)
            self.last_hit = time.time()

            if self.pv <= 0 and not self.is_dead:
                self.is_dead = True
                self.death_time = time.time()

    def respawn(self, position: Tuple[int, int], pv: int):
        """Réinitialise le joueur à une position donnée avec des PV réduits."""
        self.is_dead = False
        self.death_time = None
        self.pv = pv
        self.position.update(position)

    def event(self, keys: Tuple[bool]):
        """Détermine le vecteur de mouvement à partir des entrées clavier."""

        self.velocity.update(
            keys[self.keybinds["right"]] - keys[self.keybinds["left"]],
            keys[self.keybinds["down"]] - keys[self.keybinds["up"]],
        )

    def update_direction(self):
        """Update the direction of the animation"""

        if self.velocity.x < 0:
            self.direction = "left"
        elif self.velocity.x > 0:
            self.direction = "right"

    def authority_update(self, collision_hitbox: list[pygame.Rect]):

        if self.velocity.length_squared() > 0:
            self.update_direction()
            self.moteur.collision(self.hitbox, self.velocity, collision_hitbox)

            mov = self.velocity.length_squared()
            if mov > 0:  # Si toujours du mouvement après moteur.collision

                if mov > 1:  # Si en diagonale
                    self.velocity.normalize_ip()

                self.position += self.velocity * SPEED
                self.hitbox.center = self.position
                self.hitbox_damage.midbottom = self.position

        self.update_animation()

    def update_animation(self):
        """Logique d'animation partagée par les deux méthodes."""

        state = "run" if self.moving_intent else "idle"

        if self.attaque and self.animation.current_state != "attack":
            state = "attack"
            if self.moteur:
                self.attaque_rect = self.moteur.create_rect_attaque(
                    self.position, self.direction
                )
            self.timer = time.time()
            self.attaque = False

        if self.attaque_rect and self.timer + self.attack_duration < time.time():
            self.attaque_rect = None

        self.animation.update(state, self.direction)

    def display(self):
        """Affiche tous les éléments avec la camera."""
        if not self.is_dead:
            self.animation.display(
                pygame.Vector2(self.camera.apply(self.hitbox).center)
                - pygame.Vector2(self.im_size[0] // 2, self.im_size[1] - 22)
            )  # -22 pour afficher le joueur un peu au dessus de la hitbox


class SoloPlayerController(PlayerControllerBase):
    """Classe pour un joueur solo"""

    def update(self, ennemis):
        """Met à jour les éléments nécessaire du joueur."""

        if not self.is_dead:
            # -- Joueur --
            self.moving_intent = self.velocity.length_squared() > 0
            self.authority_update([e.hitbox for e in ennemis.values() if e.hitbox])


class HostController(PlayerControllerBase):
    """Contrôleur pour l'hôte : gère le joueur local et l'état du guest."""

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        moteur: Moteur,
        start_pos: Tuple[int, int],
    ):
        """Contrôleur pour l'hôte : gère le joueur local et l'état du guest."""

        # -- Joueur --
        super().__init__(screen, camera, moteur, start_pos)

        # -- Invité --
        self.guest = PlayerControllerBase(
            screen, camera, moteur, (start_pos[0] + 50, start_pos[1])
        )

    def update(self, ennemis):
        """Met à jour les éléments nécessaire du joueur et du client."""

        # -- Ennemie --
        ennemis_hitboxes = [e.hitbox for e in ennemis.values() if e.hitbox]

        # -- Update Host --
        if not self.is_dead:
            self.moving_intent = self.velocity.length_squared() > 0
            guest_hitbox = [self.guest.hitbox] if not self.guest.is_dead else []
            self.authority_update(ennemis_hitboxes + guest_hitbox)

        # -- Update Client --
        if not self.guest.is_dead:
            host_hitbox = [self.hitbox] if not self.is_dead else []
            self.guest.authority_update(ennemis_hitboxes + host_hitbox)

    def display(self):
        """Affiche l'invité puis le joueur"""

        # -- Client --
        self.guest.display()

        # -- Host --
        super().display()


class GuestController(PlayerControllerBase):
    """Contrôleur pour le guest : gère le joueur local et la réplique du host."""

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        moteur: Moteur,
        start_pos: Tuple[int, int],
    ):

        # -- Joueur --
        super().__init__(screen, camera, moteur, start_pos)

        # -- Host --
        self.host = PlayerControllerBase(screen, camera, moteur, start_pos)

        # -- Interpolation --
        self.target_pos: pygame.Vector2 = None
        self.host_target_pos: pygame.Vector2 = None

    def update(self, ennemis):
        """Met à jour les éléments nécessaire du joueur et de l'hôte."""

        # -- Guest : Client-Side Prediction--
        if not self.is_dead:
            self.moving_intent = self.velocity.length_squared() > 0
            host_hitbox = [self.host.hitbox] if not self.host.is_dead else []
            self.authority_update(
                [e.hitbox for e in ennemis.values() if e.hitbox] + host_hitbox
            )

        if self.target_pos is not None:
            delta = (self.target_pos - self.position).length()
            if delta > SPEED * 4:  # téléport si désync > 4 frames de mouvement
                self.position.update(self.target_pos)
            elif delta > SPEED * 0.5:
                lerp = 0.3 if self.moving_intent else 0.6
                self.position += (self.target_pos - self.position) * lerp
            self.hitbox.center = self.position
            self.hitbox_damage.midbottom = self.position
            self.target_pos = None

        # -- Host --
        self.host.update_animation()

        if self.host_target_pos is not None:
            delta = (self.host_target_pos - self.host.position).length()
            if delta > SPEED * 1.5:
                self.host.position += (self.host_target_pos - self.host.position) * 0.3
            else:
                self.host.position.update(self.host_target_pos)
            self.host.hitbox.center = self.host.position
            self.host.hitbox_damage.midbottom = self.host.position
            self.host_target_pos = None

    def display(self):
        """Affiche l'hôte puis le joueur"""

        # -- Host --
        self.host.display()

        # -- Guest --
        super().display()
