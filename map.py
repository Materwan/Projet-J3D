"Module pour la carte"

from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
from collections.abc import Callable
from itertools import combinations
import os
import threading
import time
import math
import json
import heapq
import pytmx

import numpy as np
from utils import resource_path
from perlin_numpy import generate_perlin_noise_2d
from camera_system import Camera
import pygame

if TYPE_CHECKING:
    from ennemis import Ennemi
    from game import Game
    from player import SoloPlayerController, HostController, GuestController

REPLACE_VALUE = 0.3
TILE_SIZE = (32, 32)
TILESET_DIRECTORY = resource_path(r"Ressources\TileSet")
TILEMAP_DIRECTORY = resource_path(r"Ressources\TileMap")
DUNGEON_TILEMAP_DIRECTORY = resource_path(r"Ressources\TileMap")


def get_dungeon_tiles(
    tmx_filepath,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Analyse un fichier .tmx pour détecter les positions des tuiles vides ('0').

    Args:
        tmx_filepath (str): Le chemin complet vers le fichier .tmx à analyser.

    Returns:
        list[tuple]: Une liste de tuples, où chaque tuple représente la
                     position (x, y) d'une tuile vide trouvée.
    """
    if not os.path.exists(tmx_filepath):
        print(f"Erreur : Le fichier spécifié n'existe pas : {tmx_filepath}")
        return []

    empty_tile_positions = []
    occupied_tiles = []

    map = pytmx.load_pygame(tmx_filepath)

    layer: pytmx.TiledTileLayer = map.layers[0]

    for y, row in enumerate(layer.data):
        for x, case in enumerate(row):
            if case == 0:
                empty_tile_positions.append((x, y))
            occupied_tiles.append((x, y))

    return empty_tile_positions, occupied_tiles


def load_dungeons_tilesets(file: str, folder: str):

    with open(file, "r") as f:
        s = f.read()
    dic = json.loads(s)
    for key in dic.keys():
        dic[key]["image"] = pygame.image.load(os.path.join(folder, key + ".png"))
        # dic[key]["image"] = pygame.transform.scale2x(dic[key]["image"])
        dic[key]["collision_tiles"], dic[key]["occupied_tiles"] = get_dungeon_tiles(
            os.path.join(folder, key + ".tmx")
        )
    return dic


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
            directory = os.path.join(asset_folder, value["file"])
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

                if "action_tiles" in value.keys():
                    temp2["action_tiles"] = value["action_tiles"]

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

            if "action_tiles" in value.keys():
                temp["action_tiles"] = value["action_tiles"]

            # Image
            directory = os.path.join(asset_folder, value["file"])
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
    if 0 > np.min(val) > 1 or 0 > np.max(val) > 1:
        raise ValueError("Les valeurs doivent être comprises en 0 et 1")

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
    if minimum == max_value:
        raise ValueError("le minimum est le maximum doivent être différent.")
    if scale[0] >= scale[1]:
        raise ValueError(f"L'interval doit être valide {scale}.")

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


class DungeonRoom:
    """
    Représente une salle placée dans le donjon.

    Attributes:
        position (np.ndarray): position de la salle dans la grille du donjon (en cases, pas en pixels).
        type (str): nom du fichier .png correspondant à ce template de salle.
        size (Tuple[int, int]): taille de la salle en tuiles (width, height), lu depuis dungeon_data.json.
        ios (List[Dict]): liste des IOs (entrées/sorties) de cette salle, chacun sous la forme
            {"x": int, "y": int, "dir": str, "connected": bool}.
            - x, y : position de l'IO dans la grille locale de la salle (en tuiles)
            - dir   : direction de sortie ("n", "s", "e", "w")
            - connected : True si cet IO est déjà relié à une autre salle
        surface (pygame.Surface): l'image de la salle chargée depuis le disque.
    """

    # Directions opposées : pour connecter deux salles, l'IO entrant
    # doit être la direction opposée de l'IO sortant.
    OPPOSITE: Dict[str, str] = {"n": "s", "s": "n", "e": "w", "w": "e"}

    # Décalage en cases de grille pour atteindre la salle voisine selon la direction.
    # Une salle de taille (sw, sh) placée en (gx, gy) expose un IO "e" :
    # la salle suivante devra être placée en (gx + sw, gy) pour que son IO "w" coïncide.
    # Ces deltas sont calculés dynamiquement dans Dungeon.generate_dungeon car ils
    # dépendent de la taille de la salle courante ; DIRECTION_DELTA donne juste le signe.
    DIRECTION_DELTA: Dict[str, Tuple[int, int]] = {
        "n": (0, -1),
        "s": (0, 1),
        "e": (1, 0),
        "w": (-1, 0),
    }

    def __init__(self, position: Tuple[int, int], room_type: str, tile_maps: Dict):
        """
        Args:
            position  : position (col, row) dans la grille du donjon.
            room_type : clé dans tile_maps (= nom du fichier .png).
            tile_maps : le dictionnaire complet chargé depuis dungeon_data.json.
        """
        self.position = np.array(position)  # (col, row) en cases de grille
        self.type = room_type
        self.size: Tuple[int, int] = tuple(
            tile_maps[room_type]["size"]
        )  # (w, h) en tuiles

        # Copie des IOs avec un flag "connected" initialisé à False
        self.ios: List[Dict] = [
            {**io, "connected": False} for io in tile_maps[room_type]["IO"]
        ]

        # Matrices locales de collision et d'occupation (en tuiles, repère local à la salle)
        # Forme : (width, height) pour rester cohérent avec [x][y]
        w, h = self.size
        self.collision_tiles = np.zeros((w, h), dtype=np.uint8)
        self.occupied_tiles = np.zeros((w, h), dtype=np.uint8)

        data = tile_maps[room_type]
        if data.get("collision_tiles"):
            xs, ys = zip(*data["collision_tiles"])
            self.collision_tiles[list(xs), list(ys)] = 1

        if data.get("occupied_tiles"):
            xs, ys = zip(*data["occupied_tiles"])
            self.occupied_tiles[list(xs), list(ys)] = 1

        self.surface: pygame.Surface = data["image"]

    @property
    def free_ios(self) -> List[Dict]:
        """Renvoie les IOs pas encore connectés."""
        return [io for io in self.ios if not io["connected"]]


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
        close_map(): ferme une carte et se processus et la supprime.
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

    def close_map(self):
        """
        Ferme tous les processus d'une carte, et la supprime.
        """
        pass

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
    def get_nearby_action_tiles(self, hitbox: pygame.Rect) -> List[pygame.Rect]:
        """
        Renvoie les tuiles d'actions au alentour du joueur.

        Args:
            hitbox (pygame.Rect): La hitbox du joueur pour calculer sa position sur la grille.
        Returns:
            list[pygame.Rect]: Liste des tuiles d'action à proximité immédiate.
        """
        pass

    @classmethod
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
        load_chunk_running (bool): si le thread de calcul des chunks tourne.
        last_chunk (Tuple[int, int]): le dernier chunk dans lequel était le joueur.
        load_chunk_position (Tuple[int, int]): position du joueur pour le calcul des chunks.
        load_chunk_thread (threading.Thread): le thread de calcul des chunks.
        load_chunk_event (threading.Event): l'event pour le calcul des chunks.

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
        nb_dungeons: int,
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
        self.nb_dungeons = nb_dungeons
        self.dungeons = 0
        self.tile_size = np.array(TILE_SIZE, dtype=np.int32)
        self.start_position = (self.size * self.tile_size // 2).tolist()
        self.chunk_size_pix = self.chunk_size_tile * self.tile_size
        self.action_tiles = []
        self.asset = load_assets(
            os.path.join(TILESET_DIRECTORY, "tile_data.json"),
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
        self.load_chunk_running = True
        self.last_chunk: Tuple[int, int] = (0, 0)
        self.load_chunk_position: Tuple[int, int] = self.start_position
        self.load_chunk_thread = threading.Thread(target=self._load_chunks, daemon=True)
        self.load_chunk_event = threading.Event()

        # -- Ajout éléments --
        self._add_object_pos("place", 128, 128, 3, occupe=True)
        self.structures.append((128, 128))
        self._add_structure("dungeon_entrance", nb=self.nb_dungeons, z=10, distance=5)
        self._add_structure("place", nb=3, z=3, distance=10)
        self._generate_paths(0.3, prop=0.5)
        self._add_road(0, 2)
        self._add_objects("grass", prob=0.1, z=-1, occupe=True)
        self._add_objects("tree", prob=0.01, z=2)
        self._add_objects("bush", prob=0.1, z=0)
        self._add_objects("rock", prob=0.01, z=1)

        self._register_actions()

        # -- Ennemis --
        self.ennemis = {}
        self.update_ennemis = self._get_update_ennemis()

        # -- Charge chunks --
        self.load_chunk_event.set()
        self.load_chunk_thread.start()

    def close_map(self):
        self.load_chunk_running = False
        self.load_chunk_event.clear()

    @staticmethod
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
        self._action_registry = {}
        self.register("change_map", self._change_map)

    def _change_map(self, **map_name: str):
        return map_name["target"]

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

        # Fusione le masque et le bruit de perlin Merge noise with mask
        noise = np.add(
            noise * (1 - mask_weight), mask * mask_weight
        )  # Additione le masque et le bruit de perlin
        noise = normalize(noise, self.map_scale)  # Change l'interval

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

                if "action_tiles" in self.asset[obj_type].keys():
                    if obj_type == "dungeon_entrance":
                        for tile in self.asset[obj_type]["action_tiles"]:
                            self.action_tiles.append(
                                {
                                    "x": int(tile["x"] + tx - 1),
                                    "y": int(tile["y"] + ty - 2),
                                    "action": tile["action"],
                                    "params": {"target": f"dungeon{self.dungeons}"},
                                }
                            )

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
        if nb and prob:
            raise ValueError(f"nb ou prob doit être fourni, nb = {nb}, prob = {prob}.")
        if prob is not None:
            if 0 > prob > 1:
                raise ValueError(
                    f"La probabilité soit être valide, entre 0 et 1, prob = {prob}."
                )
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

            if i > nb * 3:
                i = 0
                xs = np.random.randint(0, self.size[0], size=nb * 3)
                ys = np.random.randint(0, self.size[1], size=nb * 3)

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
                        if obj_type == "dungeon_entrance":
                            self.dungeons += 1
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
        if nb and prop:
            raise ValueError(f"nb ou prob doit être fourni, nb = {nb}, prob = {prop}.")
        nb_struct = len(self.structures)
        if prop is not None:
            if 0 > prop > 1:
                raise ValueError(
                    f"La probabilité soit être valide, entre 0 et 1, prob = {prop}."
                )
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

    def _load_chunks(self):
        """Charge les chunks au alentour d'un joueur, dans un thread parallèle."""
        while self.load_chunk_running:
            if self.load_chunk_event.is_set():
                abs_position = np.array(self.load_chunk_position, dtype=np.int32)
                if not np.less(abs_position, self.size * self.chunk_size_pix).all():
                    raise ValueError(f"La position fourni n'est pas dans la carte,\
                        position = {abs_position},\
                        taille map = {self.size * self.chunk_size_pix}.")

                chunk = abs_position // self.chunk_size_pix

                for x in range(chunk[0] - 2, chunk[0] + 3):
                    for y in range(chunk[1] - 2, chunk[1] + 3):
                        if (
                            0 <= x < self.nb_chunks[0]
                            and 0 <= y < self.nb_chunks[1]
                            and not (x, y) in self.loaded_chunks
                        ):
                            self.loaded_chunks[(x, y)] = self.chunks[(x, y)].render()

                valid = {
                    (x, y)
                    for x in range(chunk[0] - 2, chunk[0] + 3)
                    for y in range(chunk[1] - 2, chunk[1] + 3)
                    if 0 <= x < self.nb_chunks[0] and 0 <= y < self.nb_chunks[1]
                }
                for key in list(self.loaded_chunks):
                    if key not in valid:
                        del self.loaded_chunks[key]

                self.load_chunk_event.clear()
            else:
                time.sleep(0.5)

    def _trigger_load_chunk(self, absolute_position: Tuple[int, int]):
        """Dit au thread de calculer les nouveau chunks."""
        chunk = (
            absolute_position[0] // self.chunk_size_pix[0],
            absolute_position[1] // self.chunk_size_pix[1],
        )
        if chunk != self.last_chunk:
            self.load_chunk_event.set()
            self.load_chunk_position = absolute_position
            self.last_chunk = chunk

    def get_ennemis(self) -> Dict[int, "Ennemi"]:
        return self.ennemis

    def _update_ennemis_solo(self):
        del_key = []
        paths = []

        for key, ennemi in self.ennemis.items():
            paths.append(ennemi.update(self.game.player_controller))

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

        self._trigger_load_chunk(absolute_position)

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

    def get_nearby_action_tiles(self, hitbox):
        nearby_action_tiles = []

        # Trouver la position du joueur dans la grille
        tile_x = hitbox.centerx // self.tile_size[0]
        tile_y = hitbox.centery // self.tile_size[1]

        for tile in self.action_tiles:
            if (
                tile_x - 1 <= tile["x"] <= tile_x + 1
                and tile_y - 1 <= tile["y"] <= tile_y + 1
            ):
                nearby_action_tiles.append(
                    pygame.Rect(tile["x"] * 32, tile["y"] * 32, 32, 32)
                )

        return nearby_action_tiles

    def display(self, camera: Camera):

        L = list(self.loaded_chunks.keys())
        L.sort(key=lambda p: p[1] * 10 + p[0], reverse=True)

        for x, y in L:

            chunk_world_x = x * self.chunk_size_pix[0]
            chunk_world_y = y * self.chunk_size_pix[1]

            screen_x = chunk_world_x + camera.camera.x + camera.offset_x
            screen_y = chunk_world_y + camera.camera.y + camera.offset_y

            if (
                screen_x + self.chunk_size_pix[0] < 0
                or screen_x > camera.width
                or screen_y + self.chunk_size_pix[1] < 0
                or screen_y > camera.height
            ):
                continue

            self.screen.blit(self.loaded_chunks[(x, y)], (screen_x, screen_y))

        self._display_chunks(camera)

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

        import matplotlib.pyplot as plt

        plt.subplot(221)
        plt.imshow(self.map.T)
        plt.colorbar()

        plt.subplot(222)
        plt.imshow(self.road_map.T)
        plt.colorbar()

        plt.show()

    def _display_chunks(self, camera: Camera):
        screen_x = camera.camera.x + camera.offset_x
        screen_y = camera.camera.y + camera.offset_y

        for x in range(int(self.nb_chunks[0])):
            pygame.draw.line(
                self.screen,
                (0, 255, 0),
                (x * self.chunk_size_pix[0] + screen_x, screen_y),
                (
                    x * self.chunk_size_pix[0] + screen_x,
                    self.size[1] * self.tile_size[1] + screen_y,
                ),
                2,
            )
        for y in range(int(self.nb_chunks[1])):
            pygame.draw.line(
                self.screen,
                (0, 255, 0),
                (screen_x, y * self.chunk_size_pix[1] + screen_y),
                (
                    self.size[0] * self.tile_size[0] + screen_x,
                    y * self.chunk_size_pix[1] + screen_y,
                ),
                2,
            )


class Hub(BaseMap):
    """Classe dédié à la carte du Hub."""

    def __init__(self, screen: pygame.Surface, game: "Game"):

        self.screen = screen
        self.game = game

        with open(os.path.join(TILEMAP_DIRECTORY, "tilemap_data.json"), "r") as file:

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

        self.image = pygame.image.load(os.path.join(TILEMAP_DIRECTORY, "hub.png"))

        self._register_actions()

        # -- Ennemis --
        self.ennemis = {}
        self.update_ennemis = self._get_update_ennemis()

    @staticmethod
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

    def get_nearby_action_tiles(self, hitbox):
        nearby_action_tiles = []

        # Trouver la position du joueur dans la grille
        tile_x = hitbox.centerx // self.tile_size[0]
        tile_y = hitbox.centery // self.tile_size[1]

        for tile in self.action_tiles:
            if (
                tile_x - 1 <= tile["x"] <= tile_x + 1
                and tile_y - 1 <= tile["y"] <= tile_y + 1
            ):
                nearby_action_tiles.append(
                    pygame.Rect(tile["x"] * 32, tile["y"] * 32, 32, 32)
                )

        return nearby_action_tiles

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


class Dungeon(BaseMap):

    def __init__(self, game: "Game", screen: pygame.Surface, nb_rooms: int):

        self.game = game
        self.screen = screen
        self.start_position = [0, 0]
        self.action_tiles = []
        self.ennemis = {}

        self.tile_maps = load_dungeons_tilesets(
            os.path.join(DUNGEON_TILEMAP_DIRECTORY, "dungeon_data.json"),
            DUNGEON_TILEMAP_DIRECTORY,
        )

        self.tile_size = np.array(TILE_SIZE)
        self.dungeon_size = 9 * self.tile_size

        self.nb_rooms = nb_rooms
        self.rooms: List[DungeonRoom] = []

        self.generate_dungeon()
        self.update_ennemis = self._get_update_ennemis()
        self._register_actions()

    def _get_to_send_data(self) -> Dict[str, Any]:
        return {
            "type": "dungeon",
            "nb_rooms": self.nb_rooms,
        }

    def close_map(self):

        pass

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        return []

    def _create_map(
        screen: pygame.Surface, game: "Game", map_data: Dict[str, Any]
    ) -> "BaseMap":

        return Dungeon(screen, map_data["nb_rooms"])

    def _register_actions(self):
        self._action_registry = {}
        self.register("boss_fight_start", self._boss_fight_start)

    def _boss_fight_start(self):
        self.game._boss_fight_start()

    def get_ennemis(self) -> Dict[int, "Ennemi"]:

        return self.ennemis

    def _get_update_ennemis(self) -> Callable[[], List[Tuple[int, int]]]:

        return lambda: []

    def update(self, absolute_position: Tuple[int, int]):

        return self.check_action_tiles(absolute_position)

    def _room_grid_rect(self, room: DungeonRoom) -> Tuple[int, int, int, int]:
        """
        Renvoie le rectangle occupé par une salle dans la grille,
        sous la forme (col_min, row_min, col_max_exclu, row_max_exclu).

        La salle de taille (w, h) en tuiles occupe exactement
        ceil(w / CELL) colonnes et ceil(h / CELL) lignes dans la grille,
        où CELL = 9 (taille de la cellule de référence en tuiles).
        """
        cell = self.dungeon_size[0] // self.tile_size[0]  # 9 tuiles par cellule
        cols = math.ceil(room.size[0] / cell)
        rows = math.ceil(room.size[1] / cell)
        col, row = int(room.position[0]), int(room.position[1])
        return col, row, col + cols, row + rows

    def _rooms_overlap(self, a: DungeonRoom, b: DungeonRoom) -> bool:
        """Renvoie True si les deux salles se chevauchent dans la grille."""
        ac0, ar0, ac1, ar1 = self._room_grid_rect(a)
        bc0, br0, bc1, br1 = self._room_grid_rect(b)
        return ac0 < bc1 and ac1 > bc0 and ar0 < br1 and ar1 > br0

    def _position_is_free(self, candidate: DungeonRoom) -> bool:
        """Renvoie True si aucune salle existante n'occupe la même zone de grille."""
        return all(not self._rooms_overlap(candidate, placed) for placed in self.rooms)

    def _compute_neighbor_position(
        self,
        src_room: DungeonRoom,
        src_io: Dict,
        dst_type: str,
        dst_io: Dict,
    ) -> Tuple[int, int]:
        """
        Calcule la position de grille (col, row) que doit avoir la salle
        destination pour que son IO `dst_io` soit aligné avec `src_io` de la
        salle source.

        Principe géométrique
        --------------------
        Chaque salle est exprimée dans un repère de tuiles local (origine = coin
        haut-gauche de la salle).  L'IO est à la position (io_x, io_y) en tuiles.
        La taille d'une cellule de grille est CELL tuiles.

        La position en tuiles du coin haut-gauche de src_room dans la grille
        globale est :  src_origin_tile = src_room.position * CELL

        La position en tuiles de src_io dans la grille globale est donc :
            src_io_tile = src_origin_tile + (src_io["x"], src_io["y"])

        On veut que dst_io soit au même endroit :
            dst_origin_tile + (dst_io["x"], dst_io["y"]) = src_io_tile

        D'où :
            dst_origin_tile = src_io_tile - (dst_io["x"], dst_io["y"])

        Puis on convertit en position de grille :
            dst_position = dst_origin_tile / CELL  (division entière)
        """
        cell = self.dungeon_size[0] // self.tile_size[0]  # 9

        src_origin_tile = src_room.position * cell
        src_io_tile = src_origin_tile + np.array([src_io["x"], src_io["y"]])

        dst_io_tile_local = np.array([dst_io["x"], dst_io["y"]])
        dst_origin_tile = src_io_tile - dst_io_tile_local

        dst_position = dst_origin_tile // cell
        return tuple(dst_position.tolist())

    def _candidates_for_io(
        self, src_room: DungeonRoom, src_io: Dict
    ) -> List[Tuple[str, Dict, Tuple[int, int]]]:
        """
        Construit la liste de tous les (type, io_entrant, position) compatibles
        avec le `src_io` de `src_room`, mélangée aléatoirement.

        Une salle est compatible si elle possède au moins un IO dont la direction
        est l'opposée de `src_io["dir"]`.
        """
        needed_dir = DungeonRoom.OPPOSITE[src_io["dir"]]
        candidates = []

        for room_type, data in self.tile_maps.items():
            for dst_io in data["IO"]:
                if dst_io["dir"] != needed_dir:
                    continue
                # Créer une salle temporaire juste pour calculer la position
                tmp = DungeonRoom((0, 0), room_type, self.tile_maps)
                pos = self._compute_neighbor_position(src_room, src_io, tmp, dst_io)
                candidates.append((room_type, dst_io, pos))

        np.random.shuffle(candidates)
        return candidates

    def generate_dungeon(self):
        """
        Génère un donjon en plaçant `self.nb_rooms` salles connectées.

        Algorithme : expansion BFS avec backtracking local
        --------------------------------------------------
        1. On place une salle de départ aléatoire en (0, 0).
        2. On maintient une file (queue) des IOs libres à traiter.
        3. Pour chaque IO libre, on tente de placer une salle compatible
           (direction opposée, pas de collision avec les salles existantes).
           - Si on trouve une candidate valide → on la place, on marque les
             deux IOs comme connectés, et on ajoute ses nouveaux IOs libres
             à la queue.
           - Si aucune candidate ne convient → on ignore cet IO (dead end).
        4. On s'arrête quand on atteint `nb_rooms` salles ou que la queue
           est vide (plus d'IO à explorer).
        """
        self.rooms = []

        # --- Salle de départ ---
        start_type = np.random.choice(list(self.tile_maps.keys()))
        start_room = DungeonRoom((0, 0), start_type, self.tile_maps)
        self.rooms.append(start_room)

        # Queue : chaque élément = (salle_source, io_source)
        pending: List[Tuple[DungeonRoom, Dict]] = [
            (start_room, io) for io in start_room.ios
        ]
        np.random.shuffle(pending)

        while pending and len(self.rooms) < self.nb_rooms:

            src_room, src_io = pending.pop(0)

            # IO déjà connecté entre-temps (une autre branche a pu le fermer) → skip
            if src_io["connected"]:
                continue

            # Cherche une salle candidate non-collisionnante
            placed = False
            for room_type, dst_io_template, pos in self._candidates_for_io(
                src_room, src_io
            ):

                new_room = DungeonRoom(pos, room_type, self.tile_maps)

                if not self._position_is_free(new_room):
                    continue  # Collision → essaie le prochain candidat

                # Placement valide
                self.rooms.append(new_room)

                # Marque les deux IOs comme connectés
                src_io["connected"] = True
                # Trouve l'IO correspondant dans new_room (même dir que dst_io_template)
                for io in new_room.ios:
                    if io["dir"] == dst_io_template["dir"] and not io["connected"]:
                        io["connected"] = True
                        break

                # Ajoute les IOs libres de la nouvelle salle à la queue
                new_pending = [(new_room, io) for io in new_room.free_ios]
                np.random.shuffle(new_pending)
                pending.extend(new_pending)

                placed = True
                break

            # Si aucun candidat valide → l'IO reste libre (dead end naturel, pas grave)

        # --- Normalisation : décale toutes les salles pour que le coin
        # haut-gauche du donjon soit à (0, 0) dans la grille.
        # Nécessaire car la caméra ne gère que les coordonnées positives.
        if self.rooms:
            min_col = min(int(r.position[0]) for r in self.rooms)
            min_row = min(int(r.position[1]) for r in self.rooms)
            offset = np.array([min_col, min_row])
            for room in self.rooms:
                room.position -= offset
            self.start_position = (
                -offset * self.tile_size * 9 + self.tile_size * 4.5
            ).tolist()

        # --- Construction des matrices globales de tuiles ---
        self._build_tile_grids()

        # --- Action tiles : une entrée "boss_fight_start" sur chaque IO
        # de la dernière salle placée (= la salle boss).
        # Les IOs sont en coordonnées locales (tuiles) ; on les convertit
        # en coordonnées globales en ajoutant l'origine de la salle.
        self.action_tiles = []
        if self.rooms:
            cell = self.dungeon_size[0] // self.tile_size[0]  # 9
            boss_room = self.rooms[-1]
            origin_x = int(boss_room.position[0]) * cell
            origin_y = int(boss_room.position[1]) * cell
            for io in boss_room.ios:
                self.action_tiles.append(
                    {
                        "x": origin_x + io["x"],
                        "y": origin_y + io["y"],
                        "action": "boss_fight_start",
                        "params": {},
                    }
                )

    def _build_tile_grids(self):
        """
        Construit deux matrices numpy globales (en tuiles) couvrant l'ensemble
        du donjon, en agrégeant les tuiles locales de chaque salle placée.

        Après normalisation, toutes les positions de salle sont >= (0, 0).
        La taille globale est donnée par self.size (propriété).

        Attributs créés :
            collision_tiles (np.ndarray[uint8]) : 1 là où le joueur est bloqué.
            occupied_tiles  (np.ndarray[uint8]) : 1 là où une tuile est déjà occupée.
        """
        cell = self.dungeon_size[0] // self.tile_size[0]  # 9 tuiles par cellule
        total_w, total_h = self.size  # en tuiles (via property)

        self.collision_tiles = np.zeros((total_w, total_h), dtype=np.uint8)
        self.occupied_tiles = np.zeros((total_w, total_h), dtype=np.uint8)

        for room in self.rooms:
            # Origine de la salle dans le repère global en tuiles
            origin_x = int(room.position[0]) * cell
            origin_y = int(room.position[1]) * cell
            w, h = room.size

            self.collision_tiles[
                origin_x : origin_x + w, origin_y : origin_y + h
            ] |= room.collision_tiles
            self.occupied_tiles[
                origin_x : origin_x + w, origin_y : origin_y + h
            ] |= room.occupied_tiles

    def get_nearby_obstacles(self, hitbox: pygame.Rect) -> List[pygame.Rect]:
        """
        Renvoie les pygame.Rect des tuiles de collision dans un voisinage 3×3
        autour de la hitbox fournie — même interface que Hub et Map.

        Args:
            hitbox (pygame.Rect): hitbox de l'entité (joueur, ennemi…).
        Returns:
            List[pygame.Rect]: rectangles de collision à proximité.
        """
        nearby = []

        grid_x = hitbox.centerx // self.tile_size[0]
        grid_y = hitbox.centery // self.tile_size[1]

        total_w, total_h = self.collision_tiles.shape

        for x in range(grid_x - 1, grid_x + 2):
            for y in range(grid_y - 1, grid_y + 2):
                if 0 <= x < total_w and 0 <= y < total_h:
                    if self.collision_tiles[x, y]:
                        nearby.append(
                            pygame.Rect(
                                x * self.tile_size[0],
                                y * self.tile_size[1],
                                self.tile_size[0],
                                self.tile_size[1],
                            )
                        )

        return nearby

    def get_nearby_action_tiles(self, hitbox):
        nearby_action_tiles = []

        # Trouver la position du joueur dans la grille
        tile_x = hitbox.centerx // self.tile_size[0]
        tile_y = hitbox.centery // self.tile_size[1]

        for tile in self.action_tiles:
            if (
                tile_x - 1 <= tile["x"] <= tile_x + 1
                and tile_y - 1 <= tile["y"] <= tile_y + 1
            ):
                nearby_action_tiles.append(
                    pygame.Rect(tile["x"] * 32, tile["y"] * 32, 32, 32)
                )

        return nearby_action_tiles

    def is_tile_occupied(self, tile_x: int, tile_y: int) -> bool:
        """
        Indique si une tuile globale (en coordonnées de tuiles) est occupée.

        Args:
            tile_x, tile_y : coordonnées globales de la tuile.
        Returns:
            bool : True si la tuile est hors-limites ou marquée comme occupée.
        """
        total_w, total_h = self.occupied_tiles.shape
        if not (0 <= tile_x < total_w and 0 <= tile_y < total_h):
            return True  # hors-limites = occupé par convention
        return bool(self.occupied_tiles[tile_x, tile_y])

    @property
    def size(self) -> np.ndarray:
        """Taille totale du donjon en tuiles (bounding box de toutes les salles)."""
        if not self.rooms:
            return np.array([0, 0])
        cell = self.dungeon_size[0] // self.tile_size[0]  # 9 tuiles par cellule
        max_col = max(int(r.position[0]) * cell + r.size[0] for r in self.rooms)
        max_row = max(int(r.position[1]) * cell + r.size[1] for r in self.rooms)
        min_col = min(int(r.position[0]) * cell for r in self.rooms)
        min_row = min(int(r.position[1]) * cell for r in self.rooms)
        return np.array([max_col - min_col, max_row - min_row])

    def display(self, camera: Camera):
        """
        Affiche toutes les salles du donjon en tenant compte de la caméra.

        Chaque salle est placée dans l'espace monde à partir de sa position de
        grille (col, row) multipliée par dungeon_size (taille d'une cellule en
        pixels). L'offset caméra est ensuite appliqué pour obtenir la position
        écran, exactement comme dans Hub.display().

        Args:
            camera (Camera): la caméra du jeu (gère position + tremblement).
        """
        offset_x = camera.camera.x + camera.offset_x
        offset_y = camera.camera.y + camera.offset_y

        for room in self.rooms:
            # Position monde du coin haut-gauche de la salle (en pixels)
            world_x = int(room.position[0]) * self.dungeon_size[0]
            world_y = int(room.position[1]) * self.dungeon_size[1]

            # Position écran
            screen_x = world_x + offset_x
            screen_y = world_y + offset_y

            self.screen.blit(room.surface, (screen_x, screen_y))


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

    def __init__(
        self,
        screen: pygame.Surface,
        game: "Game",
        nb_dungeons,
        nb_chunks: Tuple[int, int],
        chunk_size: Tuple[int, int],
        octaves: Tuple[int, int],
        seed: int,
    ):

        self.maps: Dict[str, BaseMap] = {
            "hub": Hub(screen, game),
            "principal_map": Map(
                game, nb_chunks, chunk_size, octaves, nb_dungeons, screen, seed
            ),
        }
        for i in range(nb_dungeons):
            self.maps[f"dungeon{i}"] = Dungeon(game, screen, 20)
        if len(self.maps) > 0:
            self.map_name = list(self.maps.keys())[0]
        else:
            self.map_name = None
        self.initialize_var()

        self.game = game

    def __getitem__(self, key):
        return self.maps[key]

    @staticmethod
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

        temp.initialize_var()
        return temp

    def close_map(self):
        for map in self.maps.values():
            map.close_map()

    def _register_actions(self):
        pass

    def _get_to_send_data(self) -> Dict[str, Any]:
        return {name: map._get_to_send_data() for name, map in self.maps.items()}

    def get_nearby_obstacles(self, hitbox: pygame.Rect):

        return self.map.get_nearby_obstacles(hitbox)

    def get_nearby_action_tiles(self, hitbox):
        return self.map.get_nearby_action_tiles(hitbox)

    def initialize_var(self):
        """
        Initialise les différentes variables liée à une carte.
        """

        if self.map_name:
            self.map = self.maps[self.map_name]
            self.size = self.map.size
            self.tile_size = self.map.tile_size
            self.start_position = self.map.start_position
            self.action_tiles = self.map.action_tiles
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
        self.initialize_var()
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


if __name__ == "__main__":

    asset = load_assets(
        os.path.join(TILESET_DIRECTORY, "tile_data.json"),
        TILESET_DIRECTORY,
        [32, 32],
    )
    print(asset)

    pygame.init()

    screen = pygame.display.set_mode((800, 800))

    class Loop:

        def __init__(self, screen: pygame.Surface):
            self.running = True
            self.screen = screen
            self.screen_size = pygame.Vector2(self.screen.get_size())
            self.clock = pygame.time.Clock()
            self.t = Dungeon(screen, 50)
            self.t.generate_dungeon()
            print(len(self.t.rooms))

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        self.t = Dungeon(screen, np.random.randint(1, 50))
                        self.t.generate_dungeon()

        def update(self):

            pass

        def display(self):

            self.screen.fill((0, 0, 0))

            self.t.display()
            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    loop = Loop(screen)

    loop.run()

    pygame.quit()
