"""Module pour la gestion d'ennemis."""

from typing import List, Tuple, Dict, Any
import heapq
import math
import time

import pygame

import numpy as np
from map import Map
from camera_system import Camera
from animations import AnimationController
from moteur import Moteur


RECALC_MAX = 0.5
DEATH_TIME = 1


def create_node(
    position: Tuple[int, int],
    g: float = float("inf"),
    h: float = 0.0,
    parent: Dict = None,
) -> Dict:
    """Crée un noeud pour A*."""
    return {"position": position, "g": g, "h": h, "f": g + h, "parent": parent}


def heuristic(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """Distance euclidienne (heuristique admissible)."""
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def get_neighbors(grid: Map, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Voisins valides (8 dihitboxions, sans obstacles)."""
    x, y = pos
    cols, rows = grid.size
    moves = [(x + 1, y), (x, y - 1), (x, y + 1), (x - 1, y)]
    return [
        (nx, ny)
        for nx, ny in moves
        if 0 <= nx < cols
        and 0 <= ny < rows
        and grid.chunks[
            (nx // grid.chunk_size_tile[0], ny // grid.chunk_size_tile[1])
        ].collision[nx % grid.chunk_size_tile[0]][ny % grid.chunk_size_tile[1]]
        == 0
    ]


def reconstruct_path(node: Dict) -> List[Tuple[int, int]]:
    """Reconstruit le chemin via les parents."""
    path = []
    current = node
    while current:
        path.append(current["position"])
        current = current["parent"]
    return path[::-1]


def a_star(
    grid: Map, start: Tuple[int, int], goal: Tuple[int, int]
) -> List[Tuple[int, int]]:
    """Algorithme A* principal."""
    start_node = create_node(start, 0, heuristic(start, goal))
    open_list = [(start_node["f"], start)]
    open_dict = {start: start_node}
    closed = set()

    while open_list:
        _, current_pos = heapq.heappop(open_list)
        current = open_dict[current_pos]

        if current_pos == goal:
            return reconstruct_path(current)

        closed.add(current_pos)

        for neigh_pos in get_neighbors(grid, current_pos):
            if neigh_pos in closed:
                continue
            tent_g = current["g"] + heuristic(current_pos, neigh_pos)

            if neigh_pos not in open_dict or tent_g < open_dict[neigh_pos]["g"]:
                neigh_node = create_node(
                    neigh_pos,
                    tent_g,
                    heuristic(neigh_pos, goal),
                    current,
                )
                open_dict[neigh_pos] = neigh_node
                heapq.heappush(open_list, (neigh_node["f"], neigh_pos))

    return []  # Pas de chemin


class Ennemi:

    def __init__(
        self,
        screen: pygame.Surface,
        position: List[int],
        speed: float,
        chase_range: float,
        map: Map,
        camera: Camera,
        moteur: Moteur,
    ):
        self.screen = screen

        # -- Game --
        self.camera = camera
        self.moteur = moteur
        self.map = map

        # -- State --
        self.position = np.array(position, dtype=np.float32)
        self.hitbox = pygame.Rect(position[0], position[1], 15, 15)
        self.hitbox_damage = pygame.Rect(position[0], position[1], 30, 80)
        self.speed = speed
        self.path: List[Tuple[int, int]] | None = []
        self.chase_range = chase_range
        self.velocity = np.array((0, 0), dtype=np.float32)
        self.last_calc = 0

        # -- Attaque --
        self.attack_range = 60
        self.attack: bool | None = False
        self.attaque_rect: pygame.Rect | None = None
        self.attack_duration = 0.5
        self.timer = -1

        # -- Animation --
        self.animation = AnimationController(
            r"Ressources\Animations\Ennemis\ennemy_1", None, self.screen
        )
        self.direction = "right"

        # -- PV --
        self.pv = 20
        self.last_hit = time.time()
        self.hit_interval = 1.0

        # -- Mort --
        self.dying = False
        self.death_time = float("inf")
        self.particles_spawned = False

    def update_variables(self, data: Dict[str, Any]):
        """Met à jour les variable."""

        # -- State --
        self.pv = data["PV"]
        self.dying = data["dying"]
        if not self.dying:
            self.position = np.array(data["position"])
            self.hitbox.center = data["position"]
            self.velocity = data["velocity"]
        self.death_time = data["death_time"]

        # -- Attaque --
        self.attack = data["attack"]

    def update_animation(self):
        """Met à jour l'animation."""

        state = "run" if (self.velocity[0] != 0 or self.velocity[1] != 0) else "idle"
        if self.velocity[0] < 0:
            self.direction = "left"
        elif self.velocity[0] > 0:
            self.direction = "right"
        if self.attack:
            state = "attack"
        self.animation.update(state, self.direction)

    def update_path(self, players_pos: List[Tuple[int, int]]):
        """Génère le chemin vers le joueur le plus proche en tiles."""

        # Calcule la position des joueurs et de l'ennemi en tuile
        players_positions = [
            np.array((vec[0], vec[1]), dtype=np.float32) // self.map.tile_size
            for vec in players_pos
        ]
        tile_position = (
            np.array((int(self.position[0]), int(self.position[1])))
            // self.map.tile_size
        )

        # Calcule le joueur le plus proche
        distances = [heuristic(tile_position, x) for x in players_positions]
        closest = min(distances)

        # Si le joueur es assez proche et que le délai est terminé
        if closest < self.chase_range:
            if time.time() - self.last_calc > min(closest * 0.02, RECALC_MAX):
                player = players_positions[distances.index(closest)]
                # Transforme les array en tuples
                player = (int(player[0]), int(player[1]))
                position = (int(tile_position[0]), int(tile_position[1]))
                # Génère le nouveau chemin
                self.path = a_star(self.map, position, player)
                self.last_calc = time.time()

    def update_velocity(self, hitbox_joueur: List[pygame.Rect]):
        """Calcule la vélocité en fonction du chemin si besoin, et la
        normalise si besoin."""

        # Calcule la vélocité
        if len(self.path) > 1:
            diff = (
                np.array(self.path[1], dtype=np.float32) * 32 + self.map.tile_size / 2
            ) - self.position  # Différence à la tuile suivante
            dist = np.linalg.norm(diff)

            # Supprime la tuile du chemin
            if dist < self.speed:
                self.path.pop(0)
            else:
                self.velocity = diff / dist

        # Vérifie les collision
        if (self.velocity**2).sum() > 0:
            self.moteur.collision(self.hitbox, self.velocity, hitbox_joueur)

            if (self.velocity**2).sum() > 0:

                # Normalise la vélocité
                if (self.velocity**2).sum() > 1:
                    norm = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)

                    if norm > 0:
                        self.velocity = self.velocity / norm

                self.position += self.velocity * self.speed
                self.hitbox.center = self.position
                self.hitbox_damage.midbottom = self.position

    def update(self, *hitbox_joueur: pygame.Rect):

        if not self.dying:

            # -- Path --
            self.update_path([hitbox.center for hitbox in hitbox_joueur])

            # -- State --
            self.update_velocity(hitbox_joueur)

            # -- Attaque --
            mini = min(
                [
                    heuristic(hitbox.center, self.hitbox.center)
                    for hitbox in hitbox_joueur
                ]
            )
            if (
                mini < self.attack_range
                and self.timer + self.attack_duration < time.time()
                and self.animation.current_state != "attack"
            ):
                self.attaque_rect = self.moteur.create_rect_attaque(
                    self.hitbox, self.direction
                )
                self.attack = True
                self.timer = time.time()
            else:
                self.attack = False

            if self.attaque_rect and self.timer + self.attack_duration < time.time():
                self.attaque_rect = None

            # -- Animation --
            self.update_animation()

            return self.path

        else:
            self.attaque_rect = None
            return []

    def update_pv(self, modif: int):
        """Met à jour les PV et tue l'ennemi si besoin."""

        # Cooldown entre chaque coup
        if self.last_hit + self.hit_interval < time.time():

            self.pv += modif
            self.last_hit = time.time()

            # Si meurt
            if self.pv <= 0:

                self.dying = True
                self.death_time = time.time() + DEATH_TIME
                self.hitbox = None

    def display(self):
        """Affiche l'ennemis."""

        # -- Vivant --
        if not self.dying:
            screen_pos = pygame.Vector2(self.camera.apply(self.hitbox).center)

            self.animation.display(
                screen_pos
                - pygame.Vector2(
                    self.animation.im_size[0] // 2, self.animation.im_size[1] - 15
                )
            )


if __name__ == "__main__":

    pygame.font.init()

    screen = pygame.display.set_mode((8192 // 8, 8192 // 8))
    map = Map(
        (4, 4),
        (32, 32),
        (8, 8),
        (32, 32),
        r"Ressources\Pixel Art Top Down - Basic v1.2.3",
        screen,
        0,
    )

    t = {
        (x, y): pygame.transform.scale_by(map.chunks[(x, y)].render(), (1 / 8))
        for x in range(map.nb_chunks[0])
        for y in range(map.nb_chunks[1])
    }

    class Loop:

        def __init__(self, screen: pygame.surface.Surface):
            self.running = True
            self.screen = screen
            self.pos = [0, 0]
            self.clock = pygame.time.Clock()
            self.ennemi = Ennemi(screen, (2048, 2048), 5, 50, map)
            self.t = time.time()
            self.path = []

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

            self.mouse_pos = pygame.mouse.get_pos()

        def update(self):

            self.t = time.time()
            self.path = self.ennemi.update((pygame.Vector2(self.mouse_pos) * 8,))
            # print(time.time() - self.t)
            # print(self.path)

        def display(self):

            self.screen.fill((0, 0, 0))
            for x in range(map.nb_chunks[0] - 1, -1, -1):
                for y in range(map.nb_chunks[1] - 1, -1, -1):
                    screen.blit(
                        t[(x, y)],
                        (128 * x, 128 * y),
                    )
            for i in range(1, len(self.path)):
                pygame.draw.line(
                    self.screen,
                    (255, 0, 0),
                    (self.path[i - 1][0] * 4 + 2, self.path[i - 1][1] * 4 + 2),
                    (self.path[i][0] * 4 + 2, self.path[i][1] * 4 + 2),
                )
            self.ennemi.display()
            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    Loop(screen).run()

    pygame.quit()
