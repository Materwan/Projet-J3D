import pygame
from player import SoloPlayerController, HostController, GuestController
from moteur import Moteur
from map import Map
import time
from camera_system import Camera
from inventory import Item, Inventaire, InventaireUI, DragManager


class Game:
    """Classe de gestion du jeu : joueur et carte."""

    def __init__(self, screen: pygame.Surface, manager):
        self.screen = screen
        self.manager = manager
        self.playing_mode = None
        self.player_controller = None
        self.keybinds = {
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
        }

        # on initialise la camera à 0 pour pas que ça plante
        width, height = self.screen.get_size()
        self.camera = Camera(width, height, 0, 0)

        self.map = None
        self.map: Map
        self.address = "0.0.0.0"
        self.port = 8888

        # INVENTAIRE ! : touche I pour ouvrir et fermer inventaire
        largeur, hauteur = self.screen.get_size()
        self.inv_joueur = Inventaire(rows=4, cols=8)
        self.ui_joueur = InventaireUI(
            self.screen,
            name="Sac du joueur",
            inv=self.inv_joueur,
            pos=((largeur - 486) // 2, hauteur - 293),
            image_path="Ressources/inv_assets/chest.png",
            slot_size=52,
            slot_margin=4,
            padding=21,
            title_height=11,
            visible=False,
        )
        self.drag_mgr = DragManager(self.screen, [self.ui_joueur])

        # Items de départ :
        self.inv_joueur.add_item(Item.create("Potion Rouge", 3))

    def _on_use(self, item: Item, slot, ui: InventaireUI):
        """Appelé au clic droit sur un Consommable."""
        if item.item_type == "Consommable" and item.effect is not None:
            ui.inv.remove_item(slot[0], slot[1], 1)
            print(f"You've suck dry your potion : {item.effect:+d} PV")
            # self.player_controller.player.hp += item.effect par exemple

    def initialize(self):
        """Initialise le moteur, le controlleur à utiliser, les keybinds et la camera"""
        self.moteur = Moteur()

        if self.playing_mode == "guest":
            self.player_controller = GuestController(
                self.screen, self.moteur, self.map, self.address, self.port
            )
            while not self.player_controller.loaded:
                time.sleep(0.2)
            self.map = self.player_controller.map  # recupere la map de client
            self.moteur.map = self.map  # donner à moteur pour Client-side prediction
        else:
            self.map = Map(
                (8, 8),
                (32, 32),
                (8, 8),
                (32, 32),
                r"Ressources\Pixel Art Top Down - Basic v1.2.3",
                self.screen,
                1,
            )
            if self.playing_mode == "solo":
                self.player_controller = SoloPlayerController(
                    self.screen, self.moteur, self.map, (4096, 4096)
                )
            elif self.playing_mode == "host":
                self.player_controller = HostController(
                    self.screen, self.moteur, self.map, (4000, 4096)
                )

        self.player_controller.keybinds = self.keybinds
        self.camera.map_width = self.map.size[0] * self.map.tile_size[0]
        self.camera.map_height = self.map.size[1] * self.map.tile_size[1]
        self.player_controller.set_camera(self.camera)

    def event(self, events: list[pygame.event.Event]) -> bool:
        """Gére les entré de l'utilisateur."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.ui_joueur.visible:  # ferme l'inventaire
                        self.ui_joueur.visible = False
                    else:
                        pygame.mixer.music.play(-1)
                        self.manager.states["MENU_PAUSE"].surface_copie = (
                            self.screen.copy()
                        )
                        self.manager.change_state("MENU_PAUSE")
                elif event.key == pygame.K_SPACE:
                    self.player_controller.attaque = True
                elif event.key == pygame.K_F2:
                    self.player_controller.toggle_hitbox()
                elif event.key == pygame.K_i:
                    self.ui_joueur.visible = not self.ui_joueur.visible

            self.drag_mgr.handle_event(event, mouse_pos, on_use=self._on_use)

        self.player_controller.event(pygame.key.get_pressed())

    def update(self):
        """Met à jour le jeu."""
        self.player_controller.update()
        self.camera.update(self.player_controller.hitbox)

        if self.player_controller.close:
            self.manager.running = False

    def display(self):
        """Affiche tout les éléments."""
        self.screen.fill((100, 100, 100))
        self.camera.display_map(self.map)
        self.player_controller.display()
        # affiche l'inventaire
        self.drag_mgr.draw(pygame.mouse.get_pos())
