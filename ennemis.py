import pygame
import numpy as np
from tqdm import tqdm
from typing import List, Tuple, Dict
import heapq
import math
import time
from map import Map


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
    """Voisins valides (8 directions, sans obstacles)."""
    x, y = pos
    cols, rows = grid.size
    moves = [
        (x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0
    ]
    """for nx, ny in moves:
        print(0, nx, cols, 0 <= nx < cols)
        print(0, ny, rows, 0 <= ny < rows)
        print(
            int(
                grid.chunks[
                    (nx // grid.chunk_size_tile[0], ny // grid.chunk_size_tile[1])
                ].collision[nx % grid.chunk_size_tile[0]][ny % grid.chunk_size_tile[1]]
            ),
            grid.chunks[
                (nx // grid.chunk_size_tile[0], ny // grid.chunk_size_tile[1])
            ].collision[nx % grid.chunk_size_tile[0]][ny % grid.chunk_size_tile[1]]
            == 0,
        )"""
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
        self, screen: pygame.Surface, position: List[int], speed: int, map: Map
    ):
        self.screen = screen
        self.position = pygame.Vector2(position)
        self.speed = speed
        self.last_objectif = None
        self.last_vect = None
        self.map = map

    def update(self, player_pos: pygame.Vector2):

        start = (
            int(self.position.x // self.map.tile_size[0]),
            int(self.position.y // self.map.tile_size[1]),
        )
        end = (
            int(player_pos.x // self.map.tile_size[0]),
            int(player_pos.y // self.map.tile_size[1]),
        )
        path = a_star(self.map, start, end)

        return path

    def display(self):

        pygame.draw.rect(
            self.screen,
            (255, 0, 0),
            pygame.Rect(self.position[0], self.position[1], 50, 50),
        )


if __name__ == "__main__":

    pygame.font.init()

    screen = pygame.display.set_mode((8192 // 8, 8192 // 8))
    map = Map(
        (8, 8),
        (32, 32),
        (8, 8),
        (32, 32),
        r"Ressources\Pixel Art Top Down - Basic v1.2.3",
        screen,
        0,
    )

    np.savetxt("save.txt", map.chunks[(4, 4)].collision)

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
            self.ennemi = Ennemi(screen, (4096, 4096), 1, map)
            self.t = time.time()
            self.path = []

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

            self.mouse_pos = pygame.mouse.get_pos()

        def update(self):

            self.t = time.time()
            self.path = self.ennemi.update(pygame.Vector2(self.mouse_pos) * 8)
            print(time.time() - self.t)

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
            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    Loop(screen).run()

    pygame.quit()
