"""Module pour les animations et boutons."""

from typing import Tuple, List, Callable, Any
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


def display_directory(directory: str, indent: int | None = 0):
    """Affiche la structure d'un dossier avec fichiers et sous-dossiers."""

    for dirs in os.listdir(directory):
        print("| " * indent, dirs, sep="")
        if os.path.isdir(os.path.join(directory, dirs)):
            display_directory(os.path.join(directory, dirs), indent + 1)


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


class Text:

    def __init__(
        self,
        to_display_text: str,
        screen: pygame.Surface,
        position: Tuple[int, int],
        font_name: str | None = "Impact",
        font_size: int | None = 30,
        font_color: Tuple[int, int, int] | str | None = (0, 0, 0),
        antialias: bool = False,
    ):
        self.screen = screen
        self.to_display_text = to_display_text
        self.center_position = position
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.antialias = antialias
        print(self.font_name, self.font_size)
        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.rendered = self.font.render(
            self.to_display_text, self.antialias, self.font_color
        )

        self.text_size = self.rendered.get_size()
        self.display_position = (
            self.center_position[0] - self.text_size[0] // 2,
            self.center_position[1] - self.text_size[1] // 2,
        )

    def update(
        self,
        text: str | None = None,
        position: Tuple[int, int] | None = None,
        font: str | None = None,
        size: int | None = None,
        color: Tuple[int, int, int] | str | None = None,
        antialias: bool = False,
    ):
        self.to_display_text = text if text else self.to_display_text
        self.center_position = position if position else self.center_position
        self.font_name = font if font else self.font_name
        self.font_size = size if size else self.font_size
        self.font_color = color if color else self.font_color
        self.antialias = antialias if antialias else self.antialias

        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.rendered = self.font.render(
            self.to_display_text, self.antialias, self.font_color
        )

        self.text_size = self.rendered.get_size()
        self.display_position = (
            self.center_position[0] - self.text_size[0] // 2,
            self.center_position[1] - self.text_size[1] // 2,
        )

    def draw_text(self):
        """Affiche le texte sur la surface screen."""
        self.screen.blit(self.rendered, self.display_position)


class Button:
    """Classe pour la gestion de boutons."""

    def __init__(
        self,
        path: str,
        screen: pygame.Surface,
        position: Tuple | List,
        function: Callable,
        *,
        text: str | None = None,
        text_position: Tuple[int, int] | None = None,
        text_font: str | None = "Impact",
        text_size: int | None = 30,
        text_color: Tuple[int, int, int] | str | None = (0, 0, 0),
        text_antialias: bool = False,
        button_size: Tuple | List | None = None,
        button_scale: int | None = 1,
    ):
        """Charge et créer les images pour le bouton, ainsi que le texte si besoin

        La taille de l'image sera celle de l'originale si size est None, size et scale ne peuvent pas
        être définit en même temps.

        par défaut, si text_position est None, le text sera placé au centre du bouton.
        """
        assert not (button_scale != 1 and button_size is not None)
        assert len(position) == 2  # Verify that position is valid
        assert (text and text_font and text_size and text_color) or not text

        # Load image
        self.path = path
        self.screen = screen
        self.hover = False
        self.clicked = False
        self.image = pygame.image.load(self.path).convert_alpha()

        # Modify size if necessary
        if button_size is not None:
            assert len(button_size) == 2
            self.image = pygame.transform.scale(self.image, button_size)
        else:
            button_size = self.image.get_size()
        if button_scale != 1:
            button_size = (button_size[0] * button_scale, button_size[1] * button_scale)
            self.image = pygame.transform.scale(self.image, button_size)
        self.rec = pygame.Rect(
            position[0] - button_size[0] // 2,
            position[1] - button_size[1] // 2,
            button_size[0],
            button_size[1],
        )

        # Create darker image for hover button
        self.dark_image = self.image.copy()
        self.dark_image.fill((200, 200, 200, 255), special_flags=pygame.BLEND_RGBA_MULT)

        # Create a smaller image for clicked button
        self.clicked_image = self.dark_image.copy()
        self.clicked_image = pygame.transform.scale_by(self.clicked_image, 0.95)

        # Get or set size
        button_size = self.image.get_size() if button_size is None else button_size

        # Set display position
        self.display_pos = (
            position[0] - (button_size[0] // 2),
            position[1] - (button_size[1] // 2),
        )

        # Set display position for clicked image
        clicked_size = self.clicked_image.get_size()
        self.clicked_display_pos = (
            position[0] - (clicked_size[0] // 2),
            position[1] - (clicked_size[1] // 2),
        )

        # Set the function to execute in the event
        self.clicked_function = function

        # Create text
        if not text_position:
            text_position = (button_size[0] // 2, button_size[1] // 2)
        if text:
            self.text = Text(
                text,
                self.screen,
                (
                    self.display_pos[0] + text_position[0],
                    self.display_pos[1] + text_position[1],
                ),
                text_font,
                text_size,
                text_color,
                text_antialias,
            )
        else:
            self.text = None

    def event(
        self,
        events: List[pygame.event.Event],
        mouse_pos: Tuple[int, int],
        *func_args: Any,
    ):
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
        self.clicked_function(*func_args) if self.clicked else None

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
        if self.text:
            self.text.draw_text()


if __name__ == "__main__":

    screen = pygame.display.set_mode((500, 500))
    pygame.font.init()

    MENU_ASSET_DIRECTORY = "Ressources/UI_&_élements_graphiques/"
    BACKGROUND = MENU_ASSET_DIRECTORY + "fond ecran menu.png"
    PLAY_BUTTON = MENU_ASSET_DIRECTORY + "PLAY.png"
    SETTING_BUTTON = MENU_ASSET_DIRECTORY + "SETTINGS.png"
    EXIT_BUTTON = MENU_ASSET_DIRECTORY + "EXIT.png"
    EMPTY_BUTTON = MENU_ASSET_DIRECTORY + "EMPTY.png"
    TITLE = MENU_ASSET_DIRECTORY + "logo.png"

    def t():
        pass

    class Game:

        def __init__(self):
            self.running = True
            self.clock = pygame.time.Clock()
            self.screen = pygame.display.set_mode((600, 600))
            self.button = Button(
                EMPTY_BUTTON,
                self.screen,
                (250, 250),
                t,
                text="test",
                text_font="Impact",
                text_size=28,
                text_color=(255, 255, 255),
            )

        def event(self):
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.button.event(events, pygame.mouse.get_pos())

        def update(self):
            pass

        def display(self):
            self.screen.fill((0, 0, 0))
            self.button.display()
            pygame.display.flip()

        def run(self):

            while self.running == True:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    objet = Game()

    Game().run()

    pygame.quit()
