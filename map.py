"Module pour la carte"

from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from collections.abc import Callable
from itertools import combinations
from os import path
import time
import math
import json
import heapq

import numpy as np
from perlin_numpy import generate_perlin_noise_2d
from camera_system import Camera
import matplotlib.pyplot as plt
import pygame

if TYPE_CHECKING:
    from ennemis import Ennemi
    from game import Game
    from player import SoloPlayerController, HostController, GuestController

REPLACE_VALUE = 0.3
TILE_SIZE = (32, 32)
TILESET_DIRECTORY = r"Ressources\TileSet"
TILEMAP_DIRECTORY = r"Ressources\TileMap"


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
    """
    Classe pour le stockage de protion de carte.

    Attributes:
        chunk_size (np.ndarray): la taille d'un chunk en tuile en largeur/longueur.
        position (np.ndarray): la position du chunk sur la carte en chunk en largeur/longueure.
        tile_size (np.ndarray): la taille des tuile en largeur/longueure.
        asset: liste des différents assets disponibles.
        ground (np.ndarray): matrice des tuile sol.
        occupied (np.ndarray): matrice des positions libres.
        collision (np.ndarra): matrice des position inacessibles.
        object (List[Dict]): liste des objets sur la carte.

    Méthodes publiques:
        get_ground(map): renvoie un matrice des positions libre grace à la carte.
        render(): renvoie une image su chunk pour l'afficher."""

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


class BaseMap(ABC):
    """
    Structure générale du carte.

    Attributs:
        size (np.ndarray): la taille de la map
        start_position (Tuple[int, int]): la position d'arrivé d'un joueur sur la carte.
        tile_size (np.ndarray): la taille des tuiles de la carte.
        action_tiles (List[Dict[str, Any]]): liste des tuiles avec lequel un joueur peut intéragir.
        screen (pygame.Surface): l'écran.
        ennemis (Dict[int, Ennemi]): un dictionnaire avec tous les ennemis associé à leur id.
        _action_registry (Dict[str, Callable]): liste des action activable via les action_tiles, relié à une fonction.
        update_ennemis: fonction qui met à jour les ennemis et renvoie les chemin (debug).

    Méthodes publiques:
        get_nearby_obstacles(hitbox): renvoie les obstacle à proximité de la hitbox.
        register(name, func): associé un nom à une fonction et le met dans _action_registry.
        update(absolute_position): met à jour les différents éléments d'une carte.
        get_ennemis(): renvoie la liste des ennemis.
        check_action_tiles(absolute_position): actionne les fonction lié au tuiles activés.
        display(camera): affiche une carte.

    Méthodes privées:
        _create_map(screen, game, map_data): méthode alternative de création de carte, dédié au clients.
        _get_to_send_data(): donne les données relative à une carte pour le réseau.
        _register_actions(): appelé uen fois, relie les fonction au nom des action des action_tiles.
        _get_update_ennemis(): renvoie la fonction pour mettre à jour les ennemis.
    """

    size: np.ndarray
    start_position: Tuple[int, int] | None
    tile_size: np.ndarray
    action_tiles: List[Dict[str, Any]]
    screen: pygame.Surface
    ennemis: Dict[int, "Ennemi"]
    _action_registry: Dict[str, Callable]
    update_ennemis: Callable[[], List[Tuple[int, int]]]

    @abstractmethod
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
        pass

    @abstractmethod
    def _create_map(
        screen: pygame.Surface, game: "Game", map_data: Dict[str, Any]
    ) -> "BaseMap":
        """Méthode alternative pour créer une carte, destiné au clients.

        Args:
            screen (pygame.Surface): l'écran.
            game (Game): le controlleur du jeu.
            map_dict (Dict[str, Any]): un dictionnaire qui contient toutes les variable pour la création de la carte.

        Returns:
            BaseMap: une carte en accord avec le type dans map_data.
        """
        pass

    @abstractmethod
    def _get_to_send_data(self) -> Dict[str, Any]:
        """Renvoie les données correspondant à une carte,
        pour l'envoyer à un client."""
        pass

    @abstractmethod
    def _register_actions(self):
        """Chaque sous-classe enregistre ses actions ici."""
        pass

    def register(self, name: str, func: Callable):
        """
        Définit une fonction associé à un nom.

        Args:
            name (str): le nom associé à la fonction.
            func (Callable): la fonction associé.
        """
        self._action_registry[name] = func

    @abstractmethod
    def update(self, absolute_position: Tuple[int, int]) -> Any | str:
        """
        Met à jour les différents éléments d'une carte, charge les chunks
        si besoin, met à jour les ennemis...

        Args:
            absolute_position (Tuple[int, int]): La position du joueursur la carte.
        """
        pass

    @abstractmethod
    def get_ennemis(self) -> Dict[int, "Ennemi"]:
        """Retourne les ennemis actifs de cette map."""
        pass

    def check_action_tiles(self, absolute_position: Tuple[int, int]) -> Any | None:
        """Appel la fonction activé par le joueur sur une tuile si besoin.

        Args:
            absolute_position (Tuple[int, int]): la position absolue d'un joueur.

        Returns:
            Any | None : le retour de la fonction appelé, ou None si aucune fonction."""
        tile_x = absolute_position[0] // self.tile_size[0]
        tile_y = absolute_position[1] // self.tile_size[1]

        for tile in self.action_tiles:
            if tile["x"] == tile_x and tile["y"] == tile_y:
                action = self._action_registry.get(tile["action"])
                if action:
                    return action(**tile.get("params", {}))
        return None

    @abstractmethod
    def _get_update_ennemis(self) -> Callable[[], List[Tuple[int, int]]]:
        """Met à jour les ennemis et retourne les paths (pour le debug)."""
        pass

    @abstractmethod
    def display(self, camera: Camera):
        """
        Affiche une les différents éléments appartenant à une carte,
        et les ennemis...

        Args:
            camera (Camera): La camera du jeu.
        """
        pass


class Map(BaseMap):
    """
    Classe pour la carte principale avec génération procédurale.

    Attributs:
        nb_chunks (np.ndarray): le nombre de chunk en largeur/longeur.
        chunk_size_tile (np.ndarray): le nombre de tuile par chunk en largeur/longeur.
        chunk_size_pix (np.ndarray): le nombre de pixel par chunk en largeur/longeur.
        asset (Dict): liste de tout les assets disponibles.
        map_scale (Tuple[int, int]): intervale des valeur de la carte finale.
        map (np.ndarray): matrice de valeur dans l'interval map_scale.
        chunks (List[Chunk]): liste de tout les chunk.
        road_map (np.ndarray): matrice avec les routes créées.
        structures (List[Dict]): liste des différentes structures sur la carte.
        loaded_chunk (Dict[Tuple[int, int], Chunk]): liste des chunks chargé en méméoire associé à leur position.

    Méthodes publiques:
        create_map(octaves,...): créer une matrice de valeur dans l'interval map_scale.
        create_chunks(): créer l'ensemble des chunks de la carte.

    Méthodes privés:
        _is_occupied(x, y, dx, dy): vérifie sur les tuiles autour d'une position sont occupées.
        _add_object_pos(obj_type, x, y,...): ajoute un élément à la position x, y, et renvoie si il a réussi.
        _add_objects(obj_type,...,nb, prob): ajoute nb éléments, ou proba.
        _add_structure(obj_type,...,nb, prob): ajoute nb structure, ou proba.
        _generate_paths(randomness): créer des chemin entre les différentes structures, avec randomness le facteur de randomisation.
        _add_road(): ajoute les tuiles des chemins au objets.
        _load_chunks(absolute_position): charge les chunk à proximité, si pas déjà en mémoire.
        _update_ennemis_...(): fonction d'update des ennemis, choisi à la création de la carte.
        _render_full_map(): génére la carte entièrement, et renvoie sa surface (pour debug).
        _display(): affiche différents éléments de la carte, avec pyplot (pour debug).
    """

    def __init__(
        self,
        game: "Game",
        nb_chunks: Tuple[int, int],
        chunk_size: Tuple[int, int],
        octaves: Tuple[int, int],
        screen: pygame.Surface,
        seed: int | None,
    ):
        """
        Initialize et créer une carte procédurale.

        Args:
            game (Game): le controlleur du jeu.
            nb_chunks (Tuple[int, int]): le nombre de chunk à généré en largeur/longeur.
            chunk_size (Tuple[int, int]): la taille de chaque chunk en largeur/longeur.
            octaves (Tuple[int, int]): l'espace entre 2 vecteur lors du bruit de perlin, abruptité du terain.
            screen (pygame.Surface): l'écran.
            seed (int): la graine du monde.
        """
        # -- Valeurs initiales --
        self.nb_chunks = np.array(nb_chunks, dtype=np.int32)
        self.chunk_size_tile = np.array(chunk_size, dtype=np.int32)
        self.size = self.nb_chunks * self.chunk_size_tile
        self.octaves = octaves
        self.tile_size = np.array(TILE_SIZE, dtype=np.int32)
        self.start_position = (self.size * self.tile_size // 2).tolist()
        self.chunk_size_pix = self.chunk_size_tile * self.tile_size
        self.action_tiles = []
        self.asset = load_assets(
            path.join(TILESET_DIRECTORY, "tile_data.json"),
            TILESET_DIRECTORY,
            self.tile_size,
        )
        self.screen = screen
        self.game = game
        if seed is None:  # Si aucune graine n'est donnée, prend en une au hasard
            self.seed = np.random.randint(0, 999999999)
        else:
            self.seed = seed

        # -- Création variables spécifique --
        self.map_scale = (0, 1)
        self.map = self.create_map(octaves)
        self.chunks = self.create_chunks()
        self.road_map = np.where(self.map < 0.5, -np.inf, self.map)
        self.structures = []
        self.loaded_chunks = {}

        # -- Ajout éléments --
        self._add_object_pos("place", 128, 128, 3, occupe=True)
        self.structures.append((128, 128))
        self._add_structure("place", nb=3, z=3, distance=10)
        self._generate_paths(0.3, prop=1)
        self._add_road(0, 2)
        self._add_objects("grass", prob=0.1, z=-1, occupe=True)
        self._add_objects("tree", prob=0.01, z=2)
        self._add_objects("bush", prob=0.1, z=0)
        self._add_objects("rock", prob=0.01, z=1)

        # -- Ennemis --
        self.ennemis = {}
        self.update_ennemis = self._get_update_ennemis()
        print(self.update_ennemis)

    def _create_map(
        screen: pygame.Surface, game: "Game", map_data: Dict[str, Any]
    ) -> "Map":
        return Map(
            game,
            map_data["nb_chunks"],
            map_data["chunk_size"],
            map_data["octaves"],
            screen,
            map_data["seed"],
        )

    def _register_actions(self):
        pass

    def _get_to_send_data(self) -> Dict[str, Any]:
        return {
            "type": "map",
            "nb_chunks": self.nb_chunks.tolist(),
            "chunk_size": self.chunk_size_tile.tolist(),
            "octaves": self.octaves,
            "seed": self.seed,
        }

    def create_map(
        self,
        octaves: Tuple[int, int],
        mask_weight: float | None = 0.5,
        mask_func: Callable[[float], float] | str | None = np.log,
        mask_pad_value: float | int | None = math.e,
        mask_scale: Tuple[float, float] | None = (0, 1),
    ) -> np.ndarray:
        """Créer une carte procédurale, à partir d'un bruit de Perlin.

        Args:
            octave (Tuple[int, int]): la distance entre chaque vecteur pendant la création du bruit de perlin.
            mask_weight (float): le poids du mask lors de la fusion (entre 0 et 1).
            mask_func (Callable): la fonction utilisé pour le mask.
            mask_pad_value (float): la valeur ajouté durant le calcule du mask.
            mask_scale (Tuple[float, float]): l'interval des valeur pour le mask.

        Returns:
            np.ndarray : une matrice de valeur dans l'interval map_scale.
        """

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

    def _is_occupied(self, x, y, dx, dy) -> bool:
        """Renvoie si une tuile en xy + dxdy est occupé."""

        tx, ty = x + dx, y + dy
        x_chunk, y_chunk = tx // self.chunk_size_tile[0], ty // self.chunk_size_tile[1]
        rel_x, rel_y = tx % self.chunk_size_tile[0], ty % self.chunk_size_tile[1]

        return (
            x_chunk >= self.nb_chunks[0]
            or y_chunk >= self.nb_chunks[1]
            or self.chunks[(x_chunk, y_chunk)].occupied[rel_x][rel_y]
        )

    def _add_object_pos(
        self, obj_type: str, x: int, y: int, z: int, occupe: bool | None = False
    ) -> bool:
        """Essaye d'ajouter un élément obj à la position x, y. Renvoie si il a réussi."""

        x_map_size, y_map_size = self.chunk_size_tile
        occupied = False

        for dx, dy in self.asset[obj_type]["occupied_tiles"]:

            if self._is_occupied(x, y, dx, dy):
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

    def _add_objects(
        self,
        obj_type: str,
        *,
        occupe: bool | None = True,
        nb: int | None = None,
        prob: int | None = None,
        z: int | None = 0,
    ) -> List[Tuple[int, int]]:
        """Ajoute des éléments "obj" sur la carte. Soit en créer un nombre nb ou utilise
        prob pour déterminer le nombre à créer.

        Met à jour occupied et collisions et ajoute l'élément dans objects de chaques chunks.

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

            if self._add_object_pos(obj_type, xs[i], ys[i], z, occupe) and strict:
                count += 1
                positions.append((xs[i], ys[i]))

            i += 1

        return positions

    def _add_structure(
        self,
        obj_type: str,
        *,
        nb: int | None = None,
        z: int | None = 0,
        distance: float | None = 10,
    ):
        """Essaie d'ajouter nb structure sur la carte, en respectant les différentes
        contraintes, la distance entre les structures et leur nombre."""

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
                    if self._add_object_pos(obj_type, xs[i], ys[i], z, True):
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

    def _generate_paths(
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

    def _add_road(self, z: int, nb_tiles: int | None = 3):
        """Ajoute les tuile des routes sur la carte."""

        tiles = np.where(self.road_map == REPLACE_VALUE)
        choices = [i for i in range(len(self.asset["pave"]))]

        n = len(tiles[0])
        all_dx = np.random.randint(-1, 2, size=(n, nb_tiles))
        all_dy = np.random.randint(-1, 2, size=(n, nb_tiles))

        for i, (x, y) in enumerate(zip(*tiles)):

            for j in range(nb_tiles):

                dx = all_dx[i][j]
                dy = all_dy[i][j]

                if not self._is_occupied(x, y, dx, dy):

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

    def _load_chunks(self, absolute_position: Tuple[int, int]):
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

    def get_ennemis(self) -> Dict[int, "Ennemi"]:
        return self.ennemis

    def _update_ennemis_solo(self):
        del_key = []
        paths = []

        for key, ennemi in self.ennemis.items():
            paths.append(ennemi.update(self.game.player_controller.hitbox))

            if ennemi.attaque_rect is not None:
                self.game.moteur.apply_attack(
                    ennemi.attaque_rect, self.game.player_controller
                )

            self.game.spawn_death_particles(ennemi)

            if time.time() > ennemi.death_time:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]

        if self.game.player_controller.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.game.moteur.apply_attack(
                    self.game.player_controller.attaque_rect, ennemi
                )

        return paths

    def _update_ennemis_host(self):
        del_key = []
        paths = []

        for key, ennemi in self.ennemis.items():
            paths.append(
                ennemi.update(
                    self.game.player_controller.hitbox,
                    self.game.player_controller.guest.hitbox,
                )
            )

            if ennemi.attaque_rect is not None:
                self.game.moteur.apply_attack(
                    ennemi.attaque_rect, self.game.player_controller
                )
                self.game.moteur.apply_attack(
                    ennemi.attaque_rect, self.game.player_controller.guest
                )

            self.game.spawn_death_particles(ennemi)

            if time.time() > ennemi.death_time:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]

        if self.game.player_controller.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.game.moteur.apply_attack(
                    self.game.player_controller.attaque_rect, ennemi
                )

        if self.game.player_controller.guest.attaque_rect is not None:
            for ennemi in self.ennemis.values():
                self.game.moteur.apply_attack(
                    self.game.player_controller.guest.attaque_rect, ennemi
                )

        return paths

    def _update_ennemis_guest(self):
        """Côté guest : les ennemis sont pilotés par les données réseau."""
        del_key = []

        for key, ennemi in self.ennemis.items():

            self.game.spawn_death_particles(self.ennemis[key])

            if time.time() > ennemi.death_time:
                del_key.append(key)

        for key in del_key:
            del self.ennemis[key]
            if key in self.game.ennemis_id:
                self.game.ennemis_id.remove(key)

        return []

    def _get_update_ennemis(self) -> Callable[[], List[Tuple[int, int]]]:
        if self.game.playing_mode == "solo":
            return self._update_ennemis_solo
        elif self.game.playing_mode == "host":
            return self._update_ennemis_host
        elif self.game.playing_mode == "guest":
            return self._update_ennemis_guest

    def update(self, absolute_position: Tuple[int, int]) -> None:

        self._load_chunks(absolute_position)

        return self.check_action_tiles(absolute_position)

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

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
                if 0 <= int(x_chunk) < int(self.nb_chunks[0]) and 0 <= int(
                    y_chunk
                ) < int(self.nb_chunks[1]):
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

    def _render_full_map(self) -> pygame.Surface:
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


class Hub(BaseMap):
    """Classe dédié à la carte du Hub."""

    def __init__(self, screen: pygame.Surface, game: "Game"):

        self.screen = screen
        self.game = game

        with open(path.join(TILEMAP_DIRECTORY, "tilemap_data.json"), "r") as file:

            data = json.loads(file.read())

            self.tile_size = np.array(TILE_SIZE, dtype=np.int32)
            self.size = np.array(
                (data["hub"]["width"], data["hub"]["height"]), dtype=np.int32
            )
            self.start_position = (self.size // 2).tolist()
            self.size_in_tile = self.size // self.tile_size

            self.collision_tiles = np.zeros(shape=(self.size // self.tile_size))
            rows, cols = zip(*data["hub"]["collision_tiles"])
            self.collision_tiles[rows, cols] = 1

            self.occupied_tiles = np.zeros(shape=(self.size // self.tile_size))
            rows, cols = zip(*data["hub"]["occupied_tiles"])
            self.occupied_tiles[rows, cols] = 1

            self.action_tiles: List[Dict[str, Any]] = data["hub"]["action_tiles"]

        self.image = pygame.image.load(path.join(TILEMAP_DIRECTORY, "hub.png"))

        self._register_actions()

        # -- Ennemis --
        self.ennemis = {}
        self.update_ennemis = self._get_update_ennemis()

    def _create_map(
        screen: pygame.Surface, game: "Game", map_data: Dict[str, Any]
    ) -> "Hub":
        return Hub(screen, game)

    def _change_map(self, **map_name: str):
        return map_name["target"]

    def _get_to_send_data(self) -> Dict[str, Any]:
        return {
            "type": "hub",
        }

    def _register_actions(self):
        self._action_registry = {}
        self.register("change_map", self._change_map)

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        nearby_obstacles = []

        grid_x = hitbox.centerx // self.tile_size[0]
        grid_y = hitbox.centery // self.tile_size[1]

        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):

                if 0 <= x < self.size_in_tile[0] and 0 <= y < self.size_in_tile[1]:
                    if self.collision_tiles[x][y]:
                        # On crée le rectangle de collision pour cette tuile
                        nearby_obstacles.append(pygame.Rect(x * 32, y * 32, 32, 32))

        return nearby_obstacles

    def get_ennemis(self) -> Dict[int, "Ennemi"]:
        return {}

    def _get_update_ennemis(self) -> Callable[[], List[Tuple[int, int]]]:

        return lambda: []

    def update(self, absolute_position: Tuple[int, int]) -> str | None:

        return self.check_action_tiles(absolute_position)

    def display_tiles(self, camera: Camera):

        screen_x = camera.camera.x + camera.offset_x
        screen_y = camera.camera.y + camera.offset_y

        for x in range((self.size // self.tile_size)[0]):
            pygame.draw.line(
                self.screen,
                (255, 0, 0),
                (x * self.tile_size[0] + screen_x, screen_y),
                (x * self.tile_size[0] + screen_x, self.size[1] + screen_y),
            )
        for y in range((self.size // self.tile_size)[1]):
            pygame.draw.line(
                self.screen,
                (255, 0, 0),
                (screen_x, y * self.tile_size[1] + screen_y),
                (self.size[0] + screen_x, y * self.tile_size[1] + screen_y),
            )

    def display(self, camera: Camera):

        screen_x = camera.camera.x + camera.offset_x
        screen_y = camera.camera.y + camera.offset_y

        self.screen.blit(self.image, (screen_x, screen_y))


TYPE_STR: Dict[str, BaseMap] = {
    "map": Map,
    "hub": Hub,
}


class MapManager(BaseMap):
    """
    Gestionnaire des différentes cartes.

    Attributes:
        maps (Dict[str, BaseMap]): un dictionnaire avec toutes les cartes.
        map_name (str): le nom de la carte actuelle.
        map (BaseMap): la carte actuelle.

    Méthode publiques:
        initialize_var(): initialize les différentes valeures lors d'un changement de carte.
        change_map(name): change la map et met à jour le joueur et le game.
    """

    def __init__(self, game: "Game", **kwarg: BaseMap):

        self.maps = kwarg
        if len(self.maps) > 0:
            self.map_name = list(self.maps.keys())[0]
        else:
            self.map_name = None
        self.inizialize_var()

        self.game = game

    def _create_map(
        screen: pygame.Surface, game: "Game", map_data: Dict[str, Any]
    ) -> "MapManager":
        temp = MapManager(game)
        for name, map in map_data.items():
            temp.maps[name] = TYPE_STR[map["type"]]._create_map(screen, game, map)

        if len(temp.maps) > 0:
            temp.map_name = list(temp.maps.keys())[0]
        else:
            temp.map_name = None

        temp.inizialize_var()
        return temp

    def _register_actions(self):
        pass

    def _get_to_send_data(self) -> Dict[str, Any]:
        return {name: map._get_to_send_data() for name, map in self.maps.items()}

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        return self.map.get_nearby_obstacles(hitbox)

    def inizialize_var(self):
        """
        Initialise les différentes variables liée à une carte.
        """

        if self.map_name:
            self.map = self.maps[self.map_name]
            self.size = self.map.size
            self.tile_size = self.map.tile_size
            self.start_position = self.map.start_position
            self.update_ennemis = self._get_update_ennemis()

            # -- Ennemis --
            self.ennemis = self.map.ennemis

    def change_map(self, name: str):
        """
        Change de map en précisant son nom et en vérifant
        que cette carte existe bien.
        """
        if name not in self.maps:
            raise AttributeError(
                f"La map '{name}' n'est pas dans la liste des map : {list(self.maps.keys())}"
            )
        self.map_name = name
        self.inizialize_var()
        self.game._change_map(self.game.player_controller, self.map.start_position)

    def get_ennemis(self) -> Dict[int, "Ennemi"]:
        return self.map.get_ennemis()

    def _get_update_ennemis(self) -> List[Tuple[int, int]]:
        return self.map.update_ennemis

    def update(self, absolute_position: Tuple[int, int]):

        new_map = self.map.update(absolute_position)

        if new_map:
            self.change_map(new_map)

    def display(self, camera: Camera):

        self.map.display(camera)
        if isinstance(self.map, Hub):
            self.map.display_tiles(camera)


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
