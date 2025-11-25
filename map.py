from typing import Tuple
from collections.abc import Callable
import numpy as np
from perlin_numpy import generate_perlin_noise_2d
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import math


def invert(val: np.ndarray) -> np.ndarray:
    """Return the inverse of an array of values between 0 and 1. (0 -> 1, 1 -> 0)"""

    return np.abs(val - 1)


def normalize(
    val: np.ndarray, scale: Tuple[float, float] | None = (0, 1)
) -> np.ndarray:
    """Normalize all the values of val array between the two values of scale"""

    assert np.min(val) != np.max(val)
    assert scale[0] < scale[1]

    normalize_0_1 = (val - np.min(val)) / (np.max(val) - np.min(val))
    return scale[0] + normalize_0_1 * (scale[1] - scale[0])


def scale(
    val: np.ndarray, pad_val: float, func: Callable[[float], float]
) -> np.ndarray:
    """Apply the function func on all the values of val + pad_val"""

    vectorized_func = np.vectorize(func)
    return vectorized_func(val + pad_val)


def mask_distance(val: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Create an array where the value in i row and j column
    is the distance between the i row j column from the center af the array"""

    center = (size[0] // 2, size[1] // 2)

    for x in range(len(val)):
        for y in range(len(val[x])):
            val[x][y] = ((center[0] - x) ** 2 + (center[1] - y) ** 2) ** 0.5

    return val


def create_map(
    size: Tuple[int, int],
    octaves: Tuple[int, int],
    seed: int,
    mask_weight: float | None = 0.5,
    mask_func: Callable[[float], float] | str | None = "log_center",
    mask_pad_value: float | int | None = 0,
    mask_scale: Tuple[float, float] | None = (0, 1),
) -> np.ndarray:
    """Create a random map where :
    - size is the size of the map
    - octave is the distance between each vector during creation of perlin noise
    - seed is the seed used to create the perlin noise
    - mask_weight is the importance of the mask (between 0 and 1)
    - mask_func is the function used to create mask
    - mask_pad_value is the value add to mask before apply function
    - mask_scale is the scale for the mask"""

    # Generate perlin noise
    np.random.seed(seed)
    noise = generate_perlin_noise_2d(size, octaves)
    noise = normalize(noise, (0, 1))

    # Create basic mask
    mask = np.zeros(size, dtype=np.float32)
    mask = mask_distance(mask, size=size)
    mask = normalize(mask)
    mask = invert(mask)

    # Apply mask function and normalize mask
    if mask_func == "log_center":

        mask = scale(mask, math.e, math.log)
        mask = normalize(mask, scale=mask_scale)

    else:

        mask = scale(mask, mask_pad_value)
        mask = normalize(mask, mask_scale)

    print(np.min(mask), np.max(mask))
    print(np.min(noise), np.max(noise))

    # Merge noise with mask
    noise = np.add(noise * (1 - mask_weight), mask * mask_weight)

    print("\n", np.min(noise), np.max(noise))

    return noise


if __name__ == "__main__":

    map = create_map(
        size=(1024, 1024),
        octaves=(8, 8),
        seed=1,
        mask_weight=0.75,
        mask_scale=(0.25, 0.75),
    )

    plt.subplot(1, 2, 1)
    plt.imshow(map, cmap="gray")
    plt.colorbar()

    plt.subplot(1, 2, 2)

    mask = (map > 0.5).astype(int)
    cmap = ListedColormap(["blue", "green"])

    plt.imshow(mask, cmap=cmap)
    plt.colorbar(ticks=[0, 0.5, 1])

    plt.show()
