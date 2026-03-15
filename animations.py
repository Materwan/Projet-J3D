import pygame
from typing import Tuple, List, Dict
import os


def load_image(
    directory: str, name: str, size: Tuple | List | None = None
) -> pygame.surface.Surface:
    """Load image with good size (normal if None)"""
    path = os.path.join(directory, name)
    image = pygame.image.load(path).convert_alpha()
    if size != None:
        image = pygame.transform.scale(image, size)
    return image


def load_run_animation(run_directory: str, size: Tuple | List | None = None) -> Dict:

    animations = {
        "right": [],
        "left": [],
        "up": [],
        "down": [],
    }

    right_path = os.path.join(run_directory, "right")
    for name in os.listdir(right_path):

        right_image = load_image(right_path, name, size)
        animations["right"].append(right_image)
        animations["up"].append(right_image)

    left_path = os.path.join(run_directory, "left")
    for name in os.listdir(left_path):

        left_image = load_image(left_path, name, size)
        animations["left"].append(left_image)
        animations["down"].append(left_image)

    return animations


def load_idle_animation(idle_directory: str, size: Tuple | List | None = None) -> Dict:

    animations = {
        "right": [],
        "left": [],
    }

    right_path = os.path.join(idle_directory, "right")
    for name in os.listdir(right_path):

        right_image = load_image(right_path, name, size)
        animations["right"].append(right_image)

    left_path = os.path.join(idle_directory, "left")
    for name in os.listdir(left_path):

        left_image = load_image(left_path, name, size)
        animations["left"].append(left_image)

    return animations


def load_attack_animation(
    attack_directory: str,
    size: Tuple | List | None = None,
    background_opacity: int | None = 128,
) -> Dict:

    animations = {
        "right": [],
        "left": [],
    }

    player_path = os.path.join(attack_directory, "player")
    back_path = os.path.join(attack_directory, "back")
    for name_play, name_back in zip(os.listdir(player_path), os.listdir(back_path)):

        image = load_image(player_path, name_play, size)
        back = load_image(back_path, name_back, size)
        back.fill((255, 255, 255, background_opacity), None, pygame.BLEND_RGBA_MULT)
        image.blit(back, (0, 0))
        animations["left"].append(image)
        animations["right"].append(pygame.transform.flip(image, 1, 0))

    return animations


def create_player_animation(
    idle_directory: str,
    run_directory: str,
    attack_directory: str,
    size: Tuple | List | None = None,
) -> Dict[str, pygame.surface.Surface]:
    """Retourne un dictionnaire d'animations pour le joueur :
    {
        "run":    { "right": [...], "left": [...], "up": [...], "down": [...] },
        "idle":   { "right": [...], "left": [...] },
        "attack": { "right": [...], "left": [...] }
    }
    Chaque liste contient des Surface pygame. Taille originale si size=None.
    """
    animations = {
        "run": {
            "right": [],
            "left": [],
            "up": [],
            "down": [],
        },
        "idle": {
            "right": [],
            "left": [],
        },
        "attack": {
            "right": [],
            "left": [],
        },
    }

    animations["run"] = load_run_animation(run_directory, size)
    animations["idle"] = load_idle_animation(idle_directory, size)
    animations["attack"] = load_attack_animation(attack_directory, size)

    return animations


class AnimationController:

    def __init__(
        self,
        animations: Dict[str, Dict[str, List[pygame.surface.Surface]]],
        screen: pygame.surface.Surface,
    ):
        # Load animations
        self.animations = animations
        self.screen = screen
        self.current_state = "idle"
        self.current_dir = "right"
        self.frame_index = 0
        print(self.animations[self.current_state][self.current_dir])
        self.im_size = self.animations[self.current_state][self.current_dir][
            self.frame_index
        ].get_size()
        self.length = len(self.animations[self.current_state][self.current_dir])

        self.attacking = False
        self.attack_length = 0

    def trigger_attack(self):
        """Déclenche l'animation d'attaque (une seule fois, non interruptible)."""
        if not self.attacking:
            self.attacking = True
            self.frame_index = 0
            self.attack_length = len(self.animations["attack"][self.current_dir])

    def update(self, running: str, direction: str):
        """Change state and direction if neccesary, otherwise, update frame index"""

        if self.attacking:
            self.frame_index += 1
            # Fin de l'animation d'attaque
            if self.frame_index >= self.attack_length * 10:
                self.attacking = False
                self.frame_index = 0
                self.length = len(self.animations[self.current_state][self.current_dir])
        else:
            new_state = "run" if running else "idle"
            if new_state != self.current_state or direction != self.current_dir:
                # Change state and direction
                self.current_state = new_state
                self.current_dir = direction
                # Reset frame index and number of images
                self.frame_index = 0
                self.length = len(self.animations[self.current_state][self.current_dir])
            else:
                # Update frame index
                self.frame_index = (self.frame_index + 1) % (self.length * 10)

    def display(self, position: Tuple | List | pygame.Vector2):
        """Display animation"""
        if self.attacking:
            self.screen.blit(
                self.animations["attack"][self.current_dir][
                    self.frame_index // 10 % self.attack_length
                ],
                position,
            )
        else:
            self.screen.blit(
                self.animations[self.current_state][self.current_dir][
                    self.frame_index // 10 % self.length
                ],
                position,
            )


class Button:

    def __init__(
        self,
        path: str,
        screen: pygame.surface.Surface,
        position: Tuple | List,
        size: Tuple | List | None = None,
        scale: int | None = 1,
    ):
        """Load and create image for the button.\n
        Image size will be original if size is None
        Can set size and scale"""
        assert not (scale != 1 and size != None)
        assert len(position) == 2  # Verify that position is valid
        # Load image
        self.path = path
        self.screen = screen
        self.hover = False
        self.clicked = False
        self.image = pygame.image.load(self.path).convert_alpha()
        # Modify size if necessary
        if size != None:
            assert len(size) == 2
            self.image = pygame.transform.scale(self.image, size)
        else:
            size = self.image.get_size()
        if scale != 1:
            size = (size[0] * scale, size[1] * scale)
            self.image = pygame.transform.scale(self.image, size)
        self.rec = pygame.rect.Rect(
            position[0] - size[0] // 2, position[1] - size[1] // 2, size[0], size[1]
        )

        # Create darker image for hover button
        self.dark_image = self.image.copy()
        self.dark_image.fill((200, 200, 200, 255), special_flags=pygame.BLEND_RGBA_MULT)

        # Create a smaller image for clicked button
        self.clicked_image = self.dark_image.copy()
        self.clicked_image = pygame.transform.scale_by(self.clicked_image, 0.95)

        # Get or set size
        size = self.image.get_size() if size == None else size

        # Set display position
        self.display_pos = (position[0] - (size[0] // 2), position[1] - (size[1] // 2))

        # Set display position for clicked image
        clicked_size = self.clicked_image.get_size()
        self.clicked_display_pos = (
            position[0] - (clicked_size[0] // 2),
            position[1] - (clicked_size[1] // 2),
        )

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
    pygame.init()

    screen = pygame.display.set_mode((600, 600))

    class Game:

        def __init__(self, screen: pygame.surface.Surface):
            self.running = True
            animations = create_player_animation(
                "Projet-J3D\Animations\Idle_Animations",
                "Projet-J3D\Animations\Run_Animations",
                (100, 100),
            )
            self.animation_controller = AnimationController(animations, screen)
            self.clock = pygame.time.Clock()
            self.button = Button(
                r"Projet-J3D\Animations\UI\PLAY.png", screen, (300, 300), (200, 200)
            )
            self.screen = screen
            self.hover = False
            self.clicked = False
            self.pos = [0, 0]
            self.direction = "right"
            self.dico = {
                (1, 0): "right",
                (-1, 0): "left",
                (0, 1): "down",
                (0, -1): "up",
            }
            self.velocity = [0, 0]

        def event(self):
            hover = False
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                mouse_pos = pygame.mouse.get_pos()
                if 200 < mouse_pos[0] < 400 and 200 < mouse_pos[1] < 400:
                    hover = True
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == pygame.BUTTON_LEFT:
                            clicked = True
                self.button.change_state(hover, clicked)

            keys = pygame.key.get_pressed()
            # gestion de la vélocité en regardant les touches pressées
            self.velocity[0] = int(keys[pygame.K_RIGHT]) - int(
                keys[pygame.K_LEFT]
            )  # vaut soit 0, 1 ou -1 pour la vélocité en x
            self.velocity[1] = int(keys[pygame.K_DOWN]) - int(
                keys[pygame.K_UP]
            )  # vaut soit 0, 1 ou -1 pour la vélocité en y

        def update(self):
            if (self.velocity[0], self.velocity[1]) in self.dico:
                self.direction = self.dico[(self.velocity[0], self.velocity[1])]
            if self.velocity == [0, 0]:
                self.direction = "right" if self.direction == "up" else self.direction
                self.direction = "left" if self.direction == "down" else self.direction
                self.animation_controller.update("idle", self.direction)
            else:
                self.animation_controller.update("run", self.direction)
            self.pos[0] += self.velocity[0] * 2
            self.pos[1] += self.velocity[1] * 2

        def display(self):
            self.screen.fill((255, 255, 255))
            self.animation_controller.display(self.pos)
            self.button.display()
            pygame.display.flip()

        def run(self):

            while self.running == True:

                self.event()
                self.update()
                self.display()

                self.clock.tick(60)

    Game(screen).run()

    pygame.quit()
