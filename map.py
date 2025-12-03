from typing import Tuple, List
from collections.abc import Callable
import numpy as np
from perlin_numpy import generate_perlin_noise_2d
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import math
import pygame


def invert(val: np.ndarray) -> np.ndarray:
    """Return the inverse of an array of values between 0 and 1. (0 -> 1, 1 -> 0)"""
    assert (
        0 <= np.min(val) <= 1 and 0 <= np.max(val) <= 1
    )  # verif values between 0 and 1

    return np.abs(val - 1)


def normalize(
    val: np.ndarray,
    scale: Tuple[float, float] | None = (0, 1),
    minimum: float | None = None,
) -> np.ndarray:
    """Normalize all the values of val array between the two values of scale"""

    if minimum is None:
        minimum = np.min(val)  # If no minimum is provided, get it

    assert minimum != np.max(val)  # Verify minimum different max of array
    assert scale[0] < scale[1]  # Verify scale is valable

    normalize_0_1 = (val - np.min(val)) / (
        np.max(val) - np.min(val)
    )  # Normalize between 0 and 1
    return scale[0] + normalize_0_1 * (scale[1] - scale[0])  # Normalize in scale


def scale(
    val: np.ndarray, pad_val: float, func: Callable[[float], float]
) -> np.ndarray:
    """Apply the function func on all the values of val + pad_val"""

    # Apply the function to all values of an array
    vectorized_func = np.vectorize(func)
    return vectorized_func(val + pad_val)


def calc_distance(
    points: Tuple[int, int] | Tuple[np.ndarray, np.ndarray], center: Tuple[int, int]
) -> float | np.ndarray:
    """Return the matrice of distance between center and points /
    the distance between 2 points"""

    return ((points[0] - center[0]) ** 2 + (points[1] - center[1]) ** 2) ** 0.5


def mask_distance(val: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Create an array where the value in i row and j column
    is the distance between the i row j column from the center af the array"""

    center = (size[0] // 2, size[1] // 2)

    points = np.ogrid[
        : size[0], : size[1]
    ]  # Get the positions of all the points on the array

    return calc_distance(points, center)


def get_min_val_circle(val: np.ndarray, distance: int, size: Tuple[int, int]):
    """Get the minimum value of an array exept values
    with a distance from center above distance"""

    center = (size[0] // 2, size[1] // 2)

    cp = np.copy(val)
    mask = np.zeros(shape=size, dtype=bool)

    points = np.ogrid[
        : size[0], : size[1]
    ]  # Get the positions of all the points on the array

    dist = calc_distance(points, center)  # Get map of distance from center

    mask |= dist >= distance  # Get map of bool if distance from center > distance
    cp[mask] = 1  # Remove values where distance from center > distance

    return np.min(cp)  # Return minimum


def create_map(
    size: Tuple[int, int],
    octaves: Tuple[int, int],
    map_scale: Tuple[int, int],
    seed: int | None = None,
    mask_weight: float | None = 0.5,
    mask_func: Callable[[float], float] | str | None = "log",
    mask_pad_value: float | int | None = 0,
    mask_scale: Tuple[float, float] | None = (0, 1),
) -> np.ndarray:
    """Create a random map where :
    - size is the size of the map
    - octave is the distance between each vector during creation of perlin noise
    - map_scale is the scale of values of the returned map
    - seed is the seed used to create the perlin noise
    - mask_weight is the importance of the mask (between 0 and 1)
    - mask_func is the function used to create mask
    - mask_pad_value is the value add to mask before apply function
    - mask_scale is the scale for the mask"""

    # Generate perlin noise
    if seed is None:  # If no seed is provided, generate random
        seed = np.random.randint(0, 999999999)
    np.random.seed(seed)  # Give seed to numpy
    noise = generate_perlin_noise_2d(size, octaves)  # Get perlin noise map
    noise = normalize(noise, (0, 1))  # Normalize values to (0, 1) range

    # Create basic mask
    mask = np.zeros(size, dtype=np.float32)  # Create matrix of zeros
    mask = mask_distance(mask, size=size)  # Replace with the distances from the center
    minimum = get_min_val_circle(
        mask, 500, size
    )  # Get minimal values exept center values
    mask = normalize(
        mask, minimum=minimum
    )  # Normalize to (0, 1) but with values to far is 1
    mask = invert(mask)  # Invert values

    # Apply mask function and normalize mask
    if mask_func == "log":

        mask = scale(mask, math.e, math.log)  # Apply ln function to all values
        mask = normalize(mask, scale=mask_scale)  # Change range

    else:

        mask = scale(mask, mask_pad_value, mask_func)  # Apply function to all values
        mask = normalize(mask, mask_scale)  # Change range

    print(np.min(mask), np.max(mask))
    print(np.min(noise), np.max(noise))

    # Merge noise with mask
    noise = np.add(
        noise * (1 - mask_weight), mask * mask_weight
    )  # Merge noise with mask, with mask_weight
    noise = normalize(noise, map_scale)  # Change range

    print("\n", np.min(noise), np.max(noise))

    return noise


def add_structure(
    map: np.ndarray,
    size: Tuple[int, int],
    n: int,
    space_between: float,
    min_height: float | None = 0,
) -> List[Tuple[int, int]]:
    """Find points where :
    - size is the size of the map
    - map is the map on which find the points
    - n is the number of points to find
    - space_between is the minimum space between one points and each other
    - min_height is the minimum value on which place a point

    The function would return a list of coordinates
    but it will raise an error if he can't place the points"""

    cp = np.copy(map)  # Create a real copy of the map
    maxi = np.unravel_index(np.argmax(cp), size)  # Get position of the maximum value
    points = [maxi]  # Add position to a list of points positions

    while len(points) < n:

        if map[maxi[0]][maxi[1]] < min_height:  # Verify points are above sill
            raise ValueError(
                "Some point are under min_height :"
                "decrease space_between, nb or min_height"
            )

        mask = np.zeros(size, dtype=bool)  # Create a mtrix of False
        positions = np.ogrid[: size[0], : size[1]]  # Get all positions in the map copy
        dist2 = calc_distance(positions, points[-1])  # Calculate all the distances
        mask |= (
            dist2 <= space_between
        )  # Create a map of True False if distance from center > sill
        cp[mask] = 0  # Remove values where distance > sill

        maxi = np.unravel_index(
            np.argmax(cp), size
        )  # Get positons of last maximum value

        points.append(maxi)  # Add the positions to the list

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


def to_surface(
    map: np.ndarray, size: Tuple[int, int], tile_size: int
) -> pygame.surface.Surface:
    """Create a surface in witch values < 0.5 are water tiles,
    and values >= 0.5 are grass tiles"""

    size_surface = (size[0] * tile_size, size[1] * tile_size)
    map_surface = pygame.surface.Surface(size_surface)

    water_tile = pygame.image.load("tiles/water.png")
    grass_tile = pygame.image.load("tiles/grass.png")

    for x in range(size[0]):
        for y in range(size[1]):
            if map[x][y] < 0.5:
                map_surface.blit(water_tile, (x * tile_size, y * tile_size))
            else:
                map_surface.blit(grass_tile, (x * tile_size, y * tile_size))

    return map_surface


if __name__ == "__main__":

    map_size = (512, 512)

    map = create_map(
        size=map_size,
        octaves=(8, 8),
        seed=0,
        map_scale=(0, 1),
        mask_weight=0.75,
        mask_scale=(0.25, 0.75),
    )  # Create the map

    map_surface = to_surface(map, map_size, 16)

    # Display raw map (grayscale)
    plt.subplot(2, 2, 1)
    plt.imshow(map, cmap="gray")
    plt.colorbar()

    # Display the map with in blue values < 0.5 and red > 0.5
    plt.subplot(2, 2, 2)

    mask = (map > 0.5).astype(int)
    cmap = ListedColormap(["blue", "green"])

    plt.imshow(mask, cmap=cmap)
    plt.colorbar(ticks=[0, 0.5, 1])

    # Display zone (in black) where values > 0.7
    plt.subplot(2, 2, 3)

    mask = (map > 0.7).astype(int)
    cmap = ListedColormap(["blue", "black"])

    plt.imshow(mask, cmap=cmap)
    plt.colorbar(ticks=[0, 0.9, 1])

    plt.show()

    # Show the map on pygame
    pygame.init()

    screen = pygame.display.set_mode((0, 0))

    class Loop:

        def __init__(self, screen):
            self.running = True
            self.screen = screen
            self.pos = [0, 0]
            self.clock = pygame.time.Clock()

        def event(self):

            for event in pygame.event.get():

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        self.pos[1] -= 100
                    elif event.key == pygame.K_UP:
                        self.pos[1] += 100
                    elif event.key == pygame.K_RIGHT:
                        self.pos[0] -= 100
                    elif event.key == pygame.K_LEFT:
                        self.pos[0] += 100

        def update(self):

            print(self.pos)

        def display(self):

            self.screen.fill((0, 0, 0))
            self.screen.blit(map_surface, self.pos)
            pygame.display.flip()

        def run(self):

            while self.running:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    Loop(screen).run()

    pygame.quit()
