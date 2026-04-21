"Module pour la carte"

from typing import Tuple, List, Dict
from collections.abc import Callable
from itertools import combinations
from os import path
import math
import json
import heapq

import numpy as np
from perlin_numpy import generate_perlin_noise_2d
from camera_system import Camera
import matplotlib.pyplot as plt
import pygame


REPLACE_VALUE = 0.3
TILE_SIZE = (32, 32)
ASSET_DIRECTORY = r"Ressources\TileSet"
TILESET_DIRECTORY = r"Ressources\tileset"


def load_assets(file: str, asset_folder: str, tile_size: Tuple[int, int]):

    def _build_tile_list(size, raw_value) -> List:
        if raw_value == -1:
            return [[x, y] for x in range(size[0]) for y in range(size[1])]
        return raw_value

    with open(file, "r") as f:
        s = f.read()
    dic = json.loads(s)
    res = {}
    for key, value in dic.items():
        if isinstance(value["width"], list):

            temp = []
            directory = path.join(asset_folder, value["file"])
            image = pygame.image.load(directory)

            for i in range(len(value["width"])):
                temp2 = {}
                top = value["top"][i]
                left = value["left"][i]
                width = value["width"][i]
                height = value["height"][i]

                # Size
                temp2["size"] = (
                    width // tile_size[0],
                    height // tile_size[1],
                )

                # Occupied Tiles
                temp2["occupied_tiles"] = _build_tile_list(
                    temp2["size"], value["occupied_tiles"]
                )

                # Collision Tiles
                temp2["collision_tiles"] = _build_tile_list(
                    temp2["size"], value["collision_tiles"]
                )

                # Image
                asset_image = image.subsurface(left, top, width, height)
                temp2["image"] = asset_image
                temp.append(temp2)

            res[key] = temp

        else:
            temp = {}

            # Size
            temp["size"] = (
                value["width"] // tile_size[0],
                value["height"] // tile_size[1],
            )

            # Occupied Tiles
            temp["occupied_tiles"] = _build_tile_list(
                temp["size"], value["occupied_tiles"]
            )

            # Collision Tiles
            temp["collision_tiles"] = _build_tile_list(
                temp["size"], value["collision_tiles"]
            )

            # Image
            directory = path.join(asset_folder, value["file"])
            image = pygame.image.load(directory)
            asset_image = image.subsurface(
                value["left"], value["top"], value["width"], value["height"]
            )
            temp["image"] = asset_image
            res[key] = temp

    return res


def invert(val: np.ndarray) -> np.ndarray:
    """Renvoie l'inverse d'une matrice de valeur entre 0 et 1. (0 -> 1, 1 -> 0)"""
    # Vérifie que les valeurs sont entre 0 et 1
    assert 0 <= np.min(val) <= 1 and 0 <= np.max(val) <= 1

    return np.abs(val - 1)


def normalize(
    val: np.ndarray,
    scale: Tuple[float, float] | None = (0, 1),
    minimum: float | None = None,
) -> np.ndarray:
    """Normalise toutes les valeurs d'une matrice dans un interval."""

    # Si aucun minimum n'est donné, on prend la valeur minimale de la matrice
    min_value = np.min(val)
    if minimum is None:
        minimum = min_value

    max_value = np.max(val)
    assert minimum != max_value  # Vérifie que le minimum est différent du max
    assert scale[0] < scale[1]  # Vérifie si l'interval est valide

    normalize_0_1 = (val - min_value) / (
        max_value - min_value
    )  # Normalise entre 0 et 1
    return scale[0] + normalize_0_1 * (scale[1] - scale[0])  # Normalise sur l'interval


def scale(
    val: np.ndarray, pad_val: float, func: Callable[[float], float]
) -> np.ndarray:
    """Applique une fonction func sur toutes les valeur + pad_val d'une matrice."""
    return func(val + pad_val)


def calc_distance(
    points: Tuple[int, int] | Tuple[np.ndarray, np.ndarray], center: Tuple[int, int]
) -> float | np.ndarray:
    """Renvoie une matrice de distance entre le centre les autres valeurs."""

    return ((points[0] - center[0]) ** 2 + (points[1] - center[1]) ** 2) ** 0.5


def mask_distance(val: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Créer une matrice où la valeur à la i-ème ligne et j-ème colonne
    est la distance entre la i-ème ligne j-ème colonne et le centre de la matrice."""

    center = (size[0] // 2, size[1] // 2)
    points = np.ogrid[: size[0], : size[1]]

    dist_x = np.abs(points[0] - center[0])
    dist_y = np.abs(points[1] - center[1])

    return np.maximum(dist_x, dist_y).astype(np.float32)


def get_min_val_circle(val: np.ndarray, distance: int, size: Tuple[int, int]):
    """Récupère la valeur minimale d'une matrice excepté les valeur
    trop proches du centre."""

    center = (size[0] // 2, size[1] // 2)

    masked_val = np.copy(val)
    mask = np.zeros(shape=size, dtype=bool)

    # Récupère les positions de tous les d'une matrice
    points = np.ogrid[: size[0], : size[1]]

    dist = calc_distance(points, center)  # Récupère le matrice de distance au centre

    # Récupère une matrice de booléen : Vrai si distance du centre > distance
    mask = dist >= distance
    masked_val[mask] = 1  # Suprime les valeurs qui sont trop proches du centre

    return np.min(masked_val)  # Récupère la valeur minimale


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


def get_neighbors(grid: np.ndarray, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Voisins valides (8 directions, sans obstacles)."""
    x, y = pos
    rows, cols = grid.shape
    moves = [
        (x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0
    ]
    return [
        (nx, ny)
        for nx, ny in moves
        if 0 <= nx < rows and 0 <= ny < cols and grid[nx, ny] >= 0
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
    grid: np.ndarray, start: Tuple[int, int], goal: Tuple[int, int], randomness: float
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
            road_bonus = 0.1 if grid[neigh_pos] == REPLACE_VALUE else 1.0
            tent_g = current["g"] + heuristic(current_pos, neigh_pos) * road_bonus

            if neigh_pos not in open_dict or tent_g < open_dict[neigh_pos]["g"]:
                neigh_node = create_node(
                    neigh_pos,
                    tent_g
                    + np.random.choice([0, 10000], p=[1 - randomness, randomness]),
                    heuristic(neigh_pos, goal),
                    current,
                )
                open_dict[neigh_pos] = neigh_node
                heapq.heappush(open_list, (neigh_node["f"], neigh_pos))

    return []  # Pas de chemin


class Chunk:

    def __init__(
        self,
        chunk_size: np.ndarray,
        position: Tuple[int, int],
        map: np.ndarray,
        tile_size: np.ndarray,
        asset: Dict,
    ):
        self.chunk_size = chunk_size
        self.position = np.array(position)
        self.tile_size = tile_size
        self.asset = asset
        self.ground = self.get_ground(map)
        not_ground = ~self.ground
        self.occupied = not_ground.copy()
        self.collision = not_ground.copy()
        self.object = []

    def get_ground(self, map: np.ndarray):
        """Récupère les tuiles non vides."""
        topleft = self.position * self.chunk_size
        bottomright = (self.position + 1) * self.chunk_size
        sub_map = map[topleft[0] : bottomright[0], topleft[1] : bottomright[1]]
        return sub_map > 0.5

    def render(self) -> pygame.Surface:
        """Génére une image correspondant au chunk.\n
        Créer une surface pour le sol, puis un mask d'éléments qu'il supperpose
        au sol."""
        ground_sur = pygame.Surface(
            (self.chunk_size + 5) * self.tile_size, pygame.SRCALPHA
        )
        asset_sur = pygame.Surface(
            (self.chunk_size + 5) * self.tile_size, pygame.SRCALPHA
        )

        blit_sequence = [
            (
                self.asset["ground"]["image"],
                (x * self.tile_size[0], y * self.tile_size[1]),
            )
            for x, y in zip(*np.where(self.ground))
        ]

        ground_sur.blits(blit_sequence)

        objects = sorted(self.object, key=lambda x: x["z"])

        for object in objects:

            type = object["type"]
            x = object["x"]
            y = object["y"]
            variant = object["variant"]

            if variant == -1:
                asset_sur.blit(
                    self.asset[type]["image"],
                    (x * self.tile_size[0], y * self.tile_size[1]),
                )

            else:

                asset_sur.blit(
                    self.asset[type][variant]["image"],
                    (x * self.tile_size[0], y * self.tile_size[1]),
                )

        ground_sur.blit(asset_sur, (0, 0))
        return ground_sur


class Map:

    def __init__(
        self,
        nb_chunks: Tuple[int, int],
        chunk_size: Tuple[int, int],
        octaves: Tuple[int, int],
        screen: pygame.Surface,
        seed: int | None,
    ):
        self.nb_chunks = np.array(nb_chunks, dtype=np.int32)
        self.chunk_size_tile = np.array(chunk_size, dtype=np.int32)
        self.size = self.nb_chunks * self.chunk_size_tile
        self.octaves = octaves
        self.tile_size = np.array(TILE_SIZE, dtype=np.int32)
        self.chunk_size_pix = self.chunk_size_tile * self.tile_size
        self.asset = load_assets(
            path.join(ASSET_DIRECTORY, "tile_data.json"),
            ASSET_DIRECTORY,
            self.tile_size,
        )
        self.screen = screen
        if seed is None:  # Si aucune graine n'est donnée, prend en une au hasard
            self.seed = np.random.randint(0, 999999999)
        else:
            self.seed = seed

        self.map_scale = (0, 1)
        self.map = self.create_map(octaves)
        self.chunks = self.create_chunks()
        self.road_map = np.where(self.map < 0.5, -np.inf, self.map)
        self.structures = []

        self.add_object_pos("place", 128, 128, 3, occupe=True)
        self.structures.append((128, 128))
        self.add_structure("place", nb=3, z=3, distance=10)
        self.generate_paths(0.3, prop=1)
        self.add_road(0, 2)
        self.add_objects("grass", prob=0.1, z=-1, occupe=True)
        self.add_objects("tree", prob=0.01, z=2)
        self.add_objects("bush", prob=0.1, z=0)
        self.add_objects("rock", prob=0.01, z=1)

        self.loaded_chunks = {}

    def create_map(
        self,
        octaves: Tuple[int, int],
        mask_weight: float | None = 0.5,
        mask_func: Callable[[float], float] | str | None = np.log,
        mask_pad_value: float | int | None = math.e,
        mask_scale: Tuple[float, float] | None = (0, 1),
    ) -> np.ndarray:
        """Créer une map aléatoire où :
        - self.size est la taille de la map
        - self.map_scale est l'interval des valeur de la map
        - self.seed est la graine utilisé pour créer la map
        - octave est la distance entre chaque vecteur pendant la création du bruit de perlin
        - mask_weight is the importance of the mask (between 0 and 1)
        - mask_func est la fonction utilisé pour le mask
        - mask_pad_value est la valeur ajouté durant le calcule du mask
        - mask_scale est l'interval pour le mask"""

        # Génère le bruit de perlin
        np.random.seed(self.seed)  # Donne la graine à numpy
        noise = generate_perlin_noise_2d(
            self.size, octaves
        )  # Récupère le bruit de perlin
        noise = normalize(noise, (0, 1))  # Normalise les valeurs sur l'interval (0, 1)

        # Créer le mask basique
        mask = np.zeros(self.size, dtype=np.float32)  # Créer une matrice de zeros
        mask = mask_distance(mask, size=self.size)  # Remplace par la distance au centre
        minimum = get_min_val_circle(
            mask, 500, self.size
        )  # Récupère la valeur minimale à une distance de 500 du centre
        mask = normalize(
            mask, minimum=minimum
        )  # Normalise sur (0, 1) mais les valeurs trop loin sont 1
        mask = invert(mask)  # Inverse les valeurs

        # Applique la fonction de masque et normalise
        mask = scale(mask, mask_pad_value, mask_func)  # Applique la fonction de masque
        mask = normalize(mask, mask_scale)  # Change l'interval

        # print(np.min(mask), np.max(mask))
        # print(np.min(noise), np.max(noise))

        # Fusione le masque et le bruit de perlin Merge noise with mask
        noise = np.add(
            noise * (1 - mask_weight), mask * mask_weight
        )  # Additione le masque et le bruit de perlin
        noise = normalize(noise, self.map_scale)  # Change l'interval

        # print("\n", np.min(noise), np.max(noise))

        return noise

    def create_chunks(self) -> Dict[Tuple[int, int], Chunk]:
        """Créer l'ensemble des chunks."""
        return {
            (x, y): Chunk(
                self.chunk_size_tile, (x, y), self.map, self.tile_size, self.asset
            )
            for x in range(self.nb_chunks[0])
            for y in range(self.nb_chunks[1])
        }

    def is_occupied(self, x, y, dx, dy) -> bool:
        """Renvoie si une tuile en xy + dxdy est occupé."""

        tx, ty = x + dx, y + dy
        x_chunk, y_chunk = tx // self.chunk_size_tile[0], ty // self.chunk_size_tile[1]
        rel_x, rel_y = tx % self.chunk_size_tile[0], ty % self.chunk_size_tile[1]

        return (
            x_chunk >= self.nb_chunks[0]
            or y_chunk >= self.nb_chunks[1]
            or self.chunks[(x_chunk, y_chunk)].occupied[rel_x][rel_y]
        )

    def add_object_pos(
        self, obj_type: str, x: int, y: int, z: int, occupe: bool | None = False
    ) -> bool:
        """Essaye d'ajouter un élément obj à la position x, y. Renvoie si il a réussi."""

        x_map_size, y_map_size = self.chunk_size_tile
        occupied = False

        for dx, dy in self.asset[obj_type]["occupied_tiles"]:

            if self.is_occupied(x, y, dx, dy):
                occupied = True
                break

        if not occupied:

            if occupe:
                for dx, dy in self.asset[obj_type]["occupied_tiles"]:

                    tx, ty = x + dx, y + dy
                    x_chunk, y_chunk = tx // x_map_size, ty // y_map_size
                    rel_x, rel_y = tx % x_map_size, ty % y_map_size

                    self.chunks[(x_chunk, y_chunk)].occupied[rel_x][rel_y] = True

                for dx, dy in self.asset[obj_type]["collision_tiles"]:

                    tx, ty = x + dx, y + dy
                    x_chunk, y_chunk = tx // x_map_size, ty // y_map_size
                    rel_x, rel_y = tx % x_map_size, ty % y_map_size

                    self.chunks[(x_chunk, y_chunk)].collision[rel_x][rel_y] = True

            x_chunk, y_chunk = x // x_map_size, y // y_map_size
            rel_x, rel_y = x % x_map_size, y % y_map_size

            self.chunks[(x_chunk, y_chunk)].object.append(
                {"type": obj_type, "x": rel_x, "y": rel_y, "z": z, "variant": -1}
            )

            return True
        return False

    def add_objects(
        self,
        obj_type: str,
        *,
        occupe: bool | None = True,
        nb: int | None = None,
        prob: int | None = None,
        z: int | None = 0,
    ) -> List[Tuple[int, int]]:
        """Ajoute des éléments "obj" sur la carte. Soit en créer un nombre nb ou utilise
        prob pour déterminer le nombre à créer.\n
        Met à jour occupied et collisions et ajoute l'élément dans objects de chaques chunks.\n
        Ici z définit la priotité d'un élément, plus elle est haute, plus il sera affiché en dernier.
        """
        assert (nb is not None or prob is not None) and (nb is None or prob is None)
        if prob is not None:
            assert 0 <= prob <= 1
            strict = False
            nb = int((self.size[0] * self.size[1]) * prob)
        else:
            strict = True
        count = 0

        positions = []

        xs = np.random.randint(0, self.size[0], size=nb * 3)
        ys = np.random.randint(0, self.size[1], size=nb * 3)
        i = 0

        while count < nb:

            if not strict:
                count += 1

            if self.add_object_pos(obj_type, xs[i], ys[i], z, occupe) and strict:
                count += 1
                positions.append((xs[i], ys[i]))

            i += 1

        return positions

    def add_structure(
        self,
        obj_type: str,
        *,
        nb: int | None = None,
        z: int | None = 0,
        distance: float | None = 10,
    ):

        xs = np.random.randint(0, self.size[0], size=nb * 3)
        ys = np.random.randint(0, self.size[1], size=nb * 3)
        nb_pos = nb * 3
        i = 0
        j = 0
        count = 0

        while count < nb:

            if self.structures:
                struct = np.array(self.structures)
                diff = struct - np.array([xs[i], ys[i]])
                if np.all(np.hypot(diff[:, 0], diff[:, 1]) > distance):
                    if self.add_object_pos(obj_type, xs[i], ys[i], z, True):
                        count += 1
                        self.structures.append((xs[i], ys[i]))

            i += 1

            if i >= nb_pos:
                if j == 5:
                    raise ValueError("Trop de structures demandé, ou trop proches.")
                xs = np.random.randint(0, self.size[0], size=nb * 3)
                ys = np.random.randint(0, self.size[1], size=nb * 3)
                i = 0
                j += 1

    def generate_paths(
        self,
        randomness: float,
        *,
        nb: int | None = None,
        prop: int | None = None,
    ):
        """Créer un chemin entre la position de départ et d'arrivé en ajoutant
        du hasard pour générer des tuiles au hasard."""
        assert (nb is not None or prop is not None) and (nb is None or prop is None)
        nb_struct = len(self.structures)
        if prop is not None:
            assert 0 <= prop <= 1
            nb = int((nb_struct * (nb_struct - 1)) / 2 * prop)

        all_pairs = list(combinations(range(nb_struct), 2))
        choosen = np.random.choice(
            len(all_pairs),
            nb,
            replace=False,
        )

        for i in choosen:
            start = self.structures[all_pairs[i][0]]
            end = self.structures[all_pairs[i][1]]
            path = a_star(self.road_map, start, end, randomness)

            for x, y in path:

                self.road_map[x, y] = REPLACE_VALUE

    def add_road(self, z: int, nb_tiles: int | None = 3):

        tiles = np.where(self.road_map == REPLACE_VALUE)
        choices = [i for i in range(len(self.asset["pave"]))]

        n = len(tiles[0])
        all_dx = np.random.randint(-1, 2, size=(n, nb_tiles))
        all_dy = np.random.randint(-1, 2, size=(n, nb_tiles))

        for i, (x, y) in enumerate(zip(*tiles)):

            for j in range(nb_tiles):

                dx = all_dx[i][j]
                dy = all_dy[i][j]

                if not self.is_occupied(x, y, dx, dy):

                    tx, ty = x + dx, y + dy
                    x_chunk, y_chunk = (
                        tx // self.chunk_size_tile[0],
                        ty // self.chunk_size_tile[1],
                    )
                    rel_x, rel_y = (
                        tx % self.chunk_size_tile[0],
                        ty % self.chunk_size_tile[1],
                    )

                    self.chunks[(x_chunk, y_chunk)].occupied[rel_x][rel_y] = True
                    self.chunks[(x_chunk, y_chunk)].object.append(
                        {
                            "type": "pave",
                            "x": rel_x,
                            "y": rel_y,
                            "z": z,
                            "variant": np.random.choice(choices),
                        }
                    )

    def load_chunks(self, absolute_position: Tuple[int, int]):
        """Prend la position du joueur sur la map, et charge les chunks atours"""
        abs_position = np.array(absolute_position, dtype=np.int32)
        assert np.less(abs_position, self.size * self.chunk_size_pix).all()

        chunk = abs_position // self.chunk_size_pix

        for x in range(chunk[0] - 1, chunk[0] + 2):
            for y in range(chunk[1] - 1, chunk[1] + 2):
                if (
                    0 <= x < self.nb_chunks[0]
                    and 0 <= y < self.nb_chunks[1]
                    and not (x, y) in self.loaded_chunks
                ):
                    self.loaded_chunks[(x, y)] = self.chunks[(x, y)].render()

        valid = {
            (x, y)
            for x in range(chunk[0] - 1, chunk[0] + 2)
            for y in range(chunk[1] - 1, chunk[1] + 2)
            if 0 <= x < self.nb_chunks[0] and 0 <= y < self.nb_chunks[1]
        }
        for key in list(self.loaded_chunks):
            if key not in valid:
                del self.loaded_chunks[key]

    def update(self, absolute_position: Tuple[int, int]):

        self.load_chunks(absolute_position)

    def get_nearby_obstacles(self, hitbox: pygame.Rect):
        """
        Récupère la matrice de la map du jeu.
        Analyse une zone de 3x3 tuiles autour de la position
        centrale du joueur pour optimiser les tests de collision.

        Args:
            hitbox (pygame.Rect): La hitbox du joueur pour calculer sa position sur la grille.
        Returns:
            list[pygame.Rect]: Liste des obstacles à proximité immédiate.
        """
        nearby_obstacles = []

        # Trouver la position du joueur dans la grille
        grid_x = hitbox.centerx // self.tile_size[0]
        grid_y = hitbox.centery // self.tile_size[1]

        # Vérifier un carré de 3x3 tuiles autour du joueur
        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):

                x_chunk = x // self.chunk_size_tile[0]
                y_chunk = y // self.chunk_size_tile[1]
                rel_x = x % self.chunk_size_tile[0]
                rel_y = y % self.chunk_size_tile[1]
                # Collision sur la tuile
                if self.chunks[(x_chunk, y_chunk)].collision[rel_x][rel_y]:
                    # On crée le rectangle de collision pour cette tuile
                    nearby_obstacles.append(pygame.Rect(x * 32, y * 32, 32, 32))

        return nearby_obstacles

    def display(self, camera: Camera):

        L = list(self.loaded_chunks.keys())
        L.sort(key=lambda p: p[1] * 10 + p[0], reverse=True)

        for x, y in L:
            chunk_world_x = x * self.chunk_size_pix[0]
            chunk_world_y = y * self.chunk_size_pix[1]

            # Ces deux lignes doivent être DANS la boucle (indentation manquante)
            screen_x = chunk_world_x + camera.camera.x + camera.offset_x
            screen_y = chunk_world_y + camera.camera.y + camera.offset_y

            self.screen.blit(self.loaded_chunks[(x, y)], (screen_x, screen_y))

    def render_full_map(self) -> pygame.Surface:
        """Génère une surface complète de la map en rendant tous les chunks."""

        full_width = self.nb_chunks[0] * self.chunk_size_pix[0]
        full_height = self.nb_chunks[1] * self.chunk_size_pix[1]
        full_surface = pygame.Surface((full_width, full_height), pygame.SRCALPHA)

        for x in range(self.nb_chunks[0]):
            for y in range(self.nb_chunks[1]):
                chunk_surface = self.chunks[(x, y)].render()
                full_surface.blit(
                    chunk_surface,
                    (x * self.chunk_size_pix[0], y * self.chunk_size_pix[1]),
                )

        return full_surface

    def _display(self):

        plt.subplot(221)
        plt.imshow(self.map.T)
        plt.colorbar()

        plt.subplot(222)
        plt.imshow(self.road_map.T)
        plt.colorbar()

        plt.show()


class Hub:

    def __init__(self, screen: pygame.Surface):

        self.screen = screen

        with open(path.join(TILESET_DIRECTORY, "tileset_data.json"), "r") as file:
            data = json.loads(file.read())

        self.image = pygame.image.load(
            path.join(TILESET_DIRECTORY, data["hub"]["file"])
        )
        self.image = pygame.transform.scale_by(self.image, 2)
        self.size = (data["hub"]["width"] * 2, data["hub"]["height"] * 2)

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        return []

    def update(self, absolute_position: Tuple[int, int]):

        pass

    def display(self, camera: Camera):

        screen_x = camera.camera.x + camera.offset_x
        screen_y = camera.camera.y + camera.offset_y

        self.screen.blit(self.image, (screen_x, screen_y))


class MapManager:

    def __init__(self, principal_map: Map, hub: Hub):
        self.maps = {
            "Principale": principal_map,
            "Hub": hub,
        }
        self.map = self.maps["Hub"]

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        return self.map.get_nearby_obstacles(hitbox)

    def update(self, absolute_position: Tuple[int, int]):

        self.map.update(absolute_position)

    def display(self, camera: Camera):

        self.map.display(camera)


if __name__ == "__main__":

    pygame.init()

    screen = pygame.display.set_mode((500, 500))

    class Loop:

        def __init__(self, screen: pygame.Surface):
            self.running = True
            self.screen = screen
            self.screen_size = pygame.Vector2(self.screen.get_size())
            self.clock = pygame.time.Clock()
            self.map = Map(
                (8, 8),
                (32, 32),
                (8, 8),
                self.screen,
                0,
            )
            self.surf = self.map.render_full_map()
            self.surf = pygame.transform.scale(self.surf, self.screen_size)

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

        def update(self):

            pass

        def display(self):

            self.screen.fill((0, 0, 0))

            self.screen.blit(self.surf, (0, 0))

            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    loop = Loop(screen)

    loop.map._display()

    loop.run()

    pygame.quit()

    # map = Map((8, 8), (32, 32), (8, 8), (32, 32), screen, 0)

    load_assets("tile_data.json")
