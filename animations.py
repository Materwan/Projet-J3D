"""Module pour les animations et boutons."""

from typing import Tuple, List, Callable
import os
import pygame


def load_image(
    directory: str, name: str, size: Tuple | List | None = None
) -> pygame.Surface:
    """Load image with good size (normal if None)"""
    path = os.path.join(directory, name)
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)
    return image


def display_directory(directory: str, depth: int, indent: int | None = 0):
    """Affiche la structure d'un dossier avec fichiers et sous-dossiers."""

    if depth > 0:
        for dirs in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, dirs)):
                print("| " * indent, dirs, "\\", sep="")
            else:
                print("| " * indent, dirs, sep="")
            if os.path.isdir(os.path.join(directory, dirs)):
                display_directory(os.path.join(directory, dirs), depth - 1, indent + 1)


def load_animations(directory: str, size: Tuple[int, int] | None = None):
    """Initialise toutes les frames d'une animation."""

    res_dict = {}
    res_list = []

    for dirs in os.listdir(directory):
        new_directory = os.path.join(directory, dirs)
        if os.path.isdir(new_directory):
            res_dict[dirs] = load_animations(new_directory, size)
        else:
            res_list.append(load_image(directory, dirs, size))

    if len(res_dict) > 0 and len(res_list) > 0:
        raise ValueError("Dossier pas au bon format, va voir le drive")
    if len(res_dict) > 0:
        return res_dict
    if len(res_list) > 0:
        return res_list
    raise ValueError("Dossier vide")


def combine_back_front(back_list, front_list, background_opacity: int | None = 128):
    """Combine deux listes de Surfaces (back et front) en une liste de Surfaces."""
    if len(back_list) != len(front_list):
        raise ValueError("back et front n'ont pas le même nombre d'images")

    combined = []
    for back_surf, front_surf in zip(back_list, front_list):
        if back_surf.get_size() != front_surf.get_size():
            raise ValueError("back et front n'ont pas la même taille")

        # On crée une copie de back pour ne pas le modifier in-place
        base = back_surf.copy()
        base.fill((255, 255, 255, background_opacity), None, pygame.BLEND_RGBA_MULT)
        base.blit(front_surf, (0, 0))
        combined.append(base)

    return combined


def apply_back_front_exception(anim_dict, background_opacity: int | None = 128):
    """
    Parcourt récursivement le dict d'animations.
    Si un niveau contient les clés 'back' et 'front',
    on remplace ce dict par la liste des images combinées.
    """
    # Si c'est une liste, rien à faire
    if isinstance(anim_dict, list):
        return anim_dict

    # Sinon c'est un dict
    if not isinstance(anim_dict, dict):
        raise TypeError("Structure inattendue dans le dictionnaire d'animations")

    # Si on a exactement 'back' et 'front'
    keys = set(anim_dict.keys())
    if keys == {"back", "front"}:
        back_val = apply_back_front_exception(anim_dict["back"], background_opacity)
        front_val = apply_back_front_exception(anim_dict["front"], background_opacity)
        # print(back_val, front_val)

        if not isinstance(back_val, list) or not isinstance(front_val, list):
            raise TypeError("'back' et 'front' doivent contenir des listes d'images")

        return combine_back_front(back_val, front_val, background_opacity)

    # Sinon, on descend récursivement dans les sous-dicts
    new_dict = {}
    for key, value in anim_dict.items():
        if isinstance(value, (dict, list)):
            new_dict[key] = apply_back_front_exception(value)
        else:
            new_dict[key] = value

    return new_dict


class AnimationController:
    """Classe pour la gestion d'animations."""

    def __init__(
        self,
        animation_directory: str,
        size: Tuple[int, int] | None,
        screen: pygame.Surface,
    ):
        # Load animations
        self.animations = load_animations(animation_directory, size)
        self.animations = apply_back_front_exception(self.animations)
        self.screen = screen
        self.current_state = "idle"
        self.current_dir = "right"
        self.frame_index = 0
        self.im_size = self.animations[self.current_state][self.current_dir][
            self.frame_index
        ].get_size()
        self.length = len(self.animations[self.current_state][self.current_dir])

    def trigger_attack(self):
        """Déclenche l'animation d'attaque (une seule fois, non interruptible)."""
        if not self.current_state == "attack":
            self.current_state = "attack"
            self.frame_index = 0
            self.length = len(self.animations[self.current_state][self.current_dir])

    def update(self, state: str, direction: str):
        """Change state and direction if neccesary, otherwise, update frame index"""

        if (
            not self.current_state == "attack"
            or self.frame_index + 1 >= self.length * 10
        ):

            if state != self.current_state or direction != self.current_dir:
                # Change state and direction
                self.current_state = state
                self.current_dir = direction
                # Reset frame index and number of images
                self.frame_index = 0
                self.length = len(self.animations[self.current_state][self.current_dir])

        # Update frame index
        self.frame_index = (self.frame_index + 1) % (self.length * 10)

    def display(self, position: Tuple | List | pygame.Vector2):
        """Display animation"""
        self.screen.blit(
            self.animations[self.current_state][self.current_dir][
                self.frame_index // 10 % self.length
            ],
            position,
        )


class Button:
    """Classe pour la gestion de boutons."""

    def __init__(
        self,
        path: str,
        screen: pygame.Surface,
        position: Tuple | List,
        function: Callable,
        *,
        size: Tuple | List | None = None,
        scale: int | None = 1,
    ):
        """Load and create image for the button.\n
        Image size will be original if size is None
        Can set size and scale"""
        assert not (scale != 1 and size is not None)
        assert len(position) == 2  # Verify that position is valid
        # Load image
        self.path = path
        self.screen = screen
        self.hover = False
        self.clicked = False
        self.image = pygame.image.load(self.path).convert_alpha()
        # Modify size if necessary
        if size is not None:
            assert len(size) == 2
            self.image = pygame.transform.scale(self.image, size)
        else:
            size = self.image.get_size()
        if scale != 1:
            size = (size[0] * scale, size[1] * scale)
            self.image = pygame.transform.scale(self.image, size)
        self.rec = pygame.Rect(
            position[0] - size[0] // 2, position[1] - size[1] // 2, size[0], size[1]
        )

        # Create darker image for hover button
        self.dark_image = self.image.copy()
        self.dark_image.fill((200, 200, 200, 255), special_flags=pygame.BLEND_RGBA_MULT)

        # Create a smaller image for clicked button
        self.clicked_image = self.dark_image.copy()
        self.clicked_image = pygame.transform.scale_by(self.clicked_image, 0.95)

        # Get or set size
        size = self.image.get_size() if size is None else size

        # Set display position
        self.display_pos = (position[0] - (size[0] // 2), position[1] - (size[1] // 2))

        # Set display position for clicked image
        clicked_size = self.clicked_image.get_size()
        self.clicked_display_pos = (
            position[0] - (clicked_size[0] // 2),
            position[1] - (clicked_size[1] // 2),
        )

        # Set the function to execute in the event
        self.clicked_function = function

    def event(self, events: List[pygame.event.Event], mouse_pos: Tuple[int, int]):
        self.hover = self.rec.collidepoint(mouse_pos)
        clicked = False
        for event in events:
            if (
                self.hover
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == pygame.BUTTON_LEFT
            ):
                clicked = True
        self.clicked = clicked
        self.clicked_function() if self.clicked else None

    def change_state(self, hover: bool, clicked: bool):
        """Update values for hover and clicked button"""
        self.hover = hover
        self.clicked = clicked

    def display(self):
        """Display the corresponding image
        depending on if the button is hover or clicked or neither"""
        if self.clicked:
            self.screen.blit(self.clicked_image, self.clicked_display_pos)
        elif self.hover:
            self.screen.blit(self.dark_image, self.display_pos)
        else:
            self.screen.blit(self.image, self.display_pos)


if __name__ == "__main__":

    display_directory("Ressources", 4)
