from typing import Tuple, List
from collections.abc import Callable
import numpy as np
from perlin_numpy import generate_perlin_noise_2d
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import math
import pygame


def invert(val: np.ndarray) -> np.ndarray:
    """Renvoie l'inverse d'une matrice de valeur entre 0 et 1. (0 -> 1, 1 -> 0)"""
    assert (
        0 <= np.min(val) <= 1 and 0 <= np.max(val) <= 1
    )  # Vérifie que les valeurs sont entre 0 et 1

    return np.abs(val - 1)


def normalize(
    val: np.ndarray,
    scale: Tuple[float, float] | None = (0, 1),
    minimum: float | None = None,
) -> np.ndarray:
    """Normalise toutes les valeurs d'une matrice dans un interval."""

    # Si aucun minimum n'est donné, on prend la valeur minimale de la matrice
    if minimum is None:
        minimum = np.min(val)

    assert minimum != np.max(val)  # Vérifie que le minimum est différent du max
    assert scale[0] < scale[1]  # Vérifie si l'interval est valide

    normalize_0_1 = (val - np.min(val)) / (
        np.max(val) - np.min(val)
    )  # Normalise entre 0 et 1
    return scale[0] + normalize_0_1 * (scale[1] - scale[0])  # Normalise sur l'interval


def scale(
    val: np.ndarray, pad_val: float, func: Callable[[float], float]
) -> np.ndarray:
    """Applique une fonction func sur toutes les valeur + pad_val d'une matrice."""

    # Applique la fonction
    vectorized_func = np.vectorize(func)
    return vectorized_func(val + pad_val)


def calc_distance(
    points: Tuple[int, int] | Tuple[np.ndarray, np.ndarray], center: Tuple[int, int]
) -> float | np.ndarray:
    """Renvoie une matrice de distance entre le centre les autres valeurs."""

    return ((points[0] - center[0]) ** 2 + (points[1] - center[1]) ** 2) ** 0.5


def mask_distance(val: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Créer une matrice où la valeur à la i-ème ligne et j-ème colonne
    est la distance entre la i-ème ligne j-ème colonne et le centre de la matrice."""

    center = (size[0] // 2, size[1] // 2)

    points = np.ogrid[
        : size[0], : size[1]
    ]  # Récupère les positions de tous les d'une matrice

    return calc_distance(points, center)


def get_min_val_circle(val: np.ndarray, distance: int, size: Tuple[int, int]):
    """Récupère la valeur minimale d'une matrice excepté les valeur
    trop proches du centre."""

    center = (size[0] // 2, size[1] // 2)

    cp = np.copy(val)
    mask = np.zeros(shape=size, dtype=bool)

    points = np.ogrid[
        : size[0], : size[1]
    ]  # Récupère les positions de tous les d'une matrice

    dist = calc_distance(points, center)  # Récupère le matrice de distance au centre

    mask |= (
        dist >= distance
    )  # Récupère une matrice de booléen : Vrai si distance du centre > distance
    cp[mask] = 1  # Suprime les valeurs qui sont trop proches du centre

    return np.min(cp)  # Récupère la valeur minimale


class Map:

    def __init__(
        self,
        size: Tuple[int, int],
        octaves: Tuple[int, int],
        tile_size: Tuple[int, int],
        chunk_size: Tuple[int, int],
        seed: int,
        screen: pygame.Surface,
    ):
        self.size = np.array(size, dtype=np.int32)
        self.tile_size = np.array(tile_size, dtype=np.int32)
        self.chunk_size_tile = np.array(chunk_size, dtype=np.int32)
        self.chunk_size_pix = self.chunk_size_tile * self.tile_size
        self.chunks = self.size // self.tile_size
        if seed is None:  # Si aucune graine n'est donnée, prend en une au hasard
            self.seed = np.random.randint(0, 999999999)
        else:
            self.seed = seed
        self.map_scale = (0, 1)
        self.map = self.create_map(octaves)
        self.loaded_chunks = {}
        self.grass_tile = pygame.image.load(
            r"Ressources\Pixel Art Top Down - Basic v1.2.3\Texture\Grass.png"
        ).convert()
        self.screen = screen

    def create_map(
        self,
        octaves: Tuple[int, int],
        mask_weight: float | None = 0.5,
        mask_func: Callable[[float], float] | str | None = math.log,
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

        print(np.min(mask), np.max(mask))
        print(np.min(noise), np.max(noise))

        # Fusione le masque et le bruit de perlin Merge noise with mask
        noise = np.add(
            noise * (1 - mask_weight), mask * mask_weight
        )  # Additione le masque et le bruit de perlin
        noise = normalize(noise, self.map_scale)  # Change l'interval

        print("\n", np.min(noise), np.max(noise))

        return noise

    def load_chunks(self, absolute_position: Tuple[int, int]):
        """Prend la position du joueur sur la map, et charge les chunks atours"""
        abs_position = np.array(absolute_position, dtype=np.int32)
        assert np.less(abs_position, self.size * self.chunk_size_pix).all()

        chunk = abs_position // self.chunk_size_pix

        for x in range(int(chunk[0] - 1), chunk[0] + 2):
            for y in range(chunk[1] - 1, chunk[1] + 2):
                if (
                    0 <= x <= self.chunks[0]
                    and 0 <= y <= self.chunks[1]
                    and not (x, y) in self.chunks
                ):
                    self.loaded_chunks[(x, y)] = self.render_chunk((x, y))

        del_keys = []
        for x, y in self.loaded_chunks.keys():
            if not (
                chunk[0] - 1 <= x <= chunk[0] + 1 and chunk[1] - 1 <= y <= chunk[1] + 1
            ):
                del_keys.append((x, y))

        for key in del_keys:
            del self.loaded_chunks[key]

    def render_chunk(self, position: Tuple[int, int]) -> pygame.Surface:
        """Prend une matrice de float [0, 1], ainsi qu'une position de chunk : couple d'entier,
        et créer une surface de 32 par 32 tuiles correspondant au chunk à la position donnée
        """
        pos = np.array(position, dtype=np.int32)
        assert np.less_equal(pos, self.size // 32).all()

        sur = pygame.Surface(self.chunk_size_pix)

        start = pos * 32

        for x in range(32):
            for y in range(32):

                rel = np.array([x, y], dtype=np.int32)
                abs = start + rel

                if self.map[abs[0]][abs[1]] >= 0.5:
                    sur.blit(self.grass_tile, rel * self.tile_size)

        return sur

    def add_structure(
        map: np.ndarray,
        size: Tuple[int, int],
        n: int,
        space_between: float,
        min_height: float | None = 0,
    ) -> List[Tuple[int, int]]:
        """Trouver des points sur la map où :
        - size est la taille de la map
        - map est la map sur laquel on veut trouver ces points
        - n es le nombre de points à trouver
        - space_between est l'espace minimum entre 2 points
        - min_height est la hauteur maximale sur laquel placer un point

        La fonction renvoie une liste de coordonnées
        mais créera une erreure si il ne peut pas placer les points"""

        cp = np.copy(map)  # Créer une copie de la map
        maxi = np.unravel_index(
            np.argmax(cp), size
        )  # Trouve la position de la valeur maximale
        points = [maxi]  # Ajoute cette coordonnée dans la liste

        while len(points) < n:

            if (
                map[maxi[0]][maxi[1]] < min_height
            ):  # Vérifie si le dernier point est au dessus du seuil
                raise ValueError(
                    "Some point are under min_height :"
                    "decrease space_between, nb or min_height"
                )

            mask = np.zeros(size, dtype=bool)  # Créer une matrice de booléen
            positions = np.ogrid[
                : size[0], : size[1]
            ]  # Prend toutes les position sur la map copié
            dist2 = calc_distance(
                positions, points[-1]
            )  # Calcule toutes les distances au dernier point
            mask |= (
                dist2 <= space_between
            )  # Créer une matrice de Vrai ou Faux si la distance au centre > seuil
            cp[mask] = 0  # Enlève les valeur où distance centre > seuil

            maxi = np.unravel_index(
                np.argmax(cp), size
            )  # Trouve la position de la valeur maximale

            points.append(maxi)  # Ajoute la coordonnée dans la liste

        return points

    def colorize(points, size):

        mat = np.zeros(size, dtype=int)

        d = 10
        yy, xx = np.ogrid[: size[0], : size[1]]

        mask = np.zeros((size), dtype=bool)

        for i, j in points:
            dist2 = (yy - i) ** 2 + (xx - j) ** 2
            mask |= dist2 <= d**2

        mat[mask] = 1

        return mat

    def display(self, absolute_position: Tuple[int, int]):
        """Affiche les chunks les plus proches"""
        abs_pos = np.array(absolute_position, dtype=np.int32)
        for x, y in self.loaded_chunks.keys():
            self.screen.blit(
                self.loaded_chunks[(x, y)],
                (
                    x * self.chunk_size_pix[0] - abs_pos[0],
                    y * self.chunk_size_pix[1] - abs_pos[1],
                ),
            )

    def _display(self):

        # Display raw map (grayscale)
        plt.subplot(2, 2, 1)
        plt.imshow(self.map, cmap="gray")
        plt.colorbar()

        # Display the map with in blue values < 0.5 and red > 0.5
        plt.subplot(2, 2, 2)

        mask = (self.map > 0.5).astype(int)
        cmap = ListedColormap(["blue", "green"])

        plt.imshow(mask, cmap=cmap)
        plt.colorbar(ticks=[0, 0.5, 1])

        # Display zone (in black) where values > 0.7
        plt.subplot(2, 2, 3)

        mask = (self.map > 0.7).astype(int)
        cmap = ListedColormap(["blue", "black"])

        plt.imshow(mask, cmap=cmap)
        plt.colorbar(ticks=[0, 0.9, 1])

        plt.show()


if __name__ == "__main__":

    pygame.init()

    class Loop:

        def __init__(self, screen: pygame.Surface):
            self.running = True
            self.screen = screen
            self.screen_size = pygame.Vector2(self.screen.get_size())
            self.abs_pos = pygame.Vector2([0, 0])
            self.clock = pygame.time.Clock()
            self.map = Map(
                (256, 256),
                (8, 8),
                (32, 32),
                (32, 32),
                0,
                self.screen,
            )

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        self.abs_pos[1] += 100
                    elif event.key == pygame.K_UP:
                        self.abs_pos[1] -= 100
                    elif event.key == pygame.K_RIGHT:
                        self.abs_pos[0] += 100
                    elif event.key == pygame.K_LEFT:
                        self.abs_pos[0] -= 100

                if event.type == pygame.QUIT:
                    self.running = False

        def update(self):

            self.map.load_chunks(self.abs_pos)

        def display(self):

            self.screen.fill((0, 0, 0))

            self.map.display(self.abs_pos)

            for x in range(self.map.chunks[0]):
                pygame.draw.line(
                    self.screen,
                    (255, 0, 0),
                    (x * 32 * 32 - self.abs_pos[0], 0 - self.abs_pos[1]),
                    (
                        x * 32 * 32 - self.abs_pos[0],
                        self.map.chunks[1] * 32 * 32 - self.abs_pos[1],
                    ),
                )
            for y in range(self.map.chunks[1]):
                pygame.draw.line(
                    self.screen,
                    (255, 0, 0),
                    (0 - self.abs_pos[0], y * 32 * 32 - self.abs_pos[1]),
                    (
                        self.map.chunks[0] * 32 * 32 - self.abs_pos[0],
                        y * 32 * 32 - self.abs_pos[1],
                    ),
                )
            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    screen = pygame.display.set_mode((500, 500))

    loop = Loop(screen)

    loop.map._display()

    loop.run()

    pygame.quit()
