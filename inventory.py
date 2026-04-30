import random
import os
import json
import pygame

INVENTORY_ASSET_DIRECTORY = r"Ressources\InventoryAsset"

"""
item_dic c'est la base de données des Items du jeu
Chaque item a :
  - description  : texte affiché dans le tooltip
  - item_type    : "Consommable", "Bric-à-brac", "Curiosités" ou "Légendes"
  - max_stack    : quantité max par case d'inventaire
  - icon_path    : chemin vers l'image depuis le dossier Ressources
  - price        : prix de vente en Mole_Coins
  - effect       : soin ou malus de PV si Consommable, None sinon

Price :
    item_dic stocke le prix de VENTE.
    Le prix d'ACHAT chez un marchand = prix_vente * price_multiplier
    (entre 1.2 et 1.6, tiré aléatoirement pour chaque PNJ marchand).
"""
with open(
    os.path.join(INVENTORY_ASSET_DIRECTORY, "item_data.json"), "r", encoding="utf-8"
) as file:
    data: dict[str, dict] = json.loads(file.read())
    item_dic: dict[str, dict] = {}
    for type in data.keys():
        for item in data[type].keys():
            item_dic[item] = {}
            item_dic[item]["description"] = data[type][item]["description"]
            item_dic[item]["item_type"] = data[type][item]["item_type"]
            item_dic[item]["max_stack"] = data[type][item]["max_stack"]
            item_dic[item]["price"] = data[type][item]["price"]
            item_dic[item]["effect"] = data[type][item]["effect"]
            item_dic[item]["icon_path"] = os.path.join(
                INVENTORY_ASSET_DIRECTORY, type, data[type][item]["file_name"]
            )


class Item:
    """
    Données et état d'un Item du jeu.

    Usage :
        Item.create("Diamant", 1)
    """

    def __init__(
        self,
        name: str,
        description: str,
        item_type: str,
        max_stack: int,
        quantity: int,
        icon: pygame.Surface,
        price: int,
        effect: int | None,
    ):
        self.name = name
        self.description = description
        self.item_type = item_type
        self.max_stack = max_stack
        self.quantity = quantity
        self.icon = icon
        self.price = price
        self.effect = effect

    def can_stack_with(self, item: "Item") -> bool:
        return self.name == item.name and self.quantity < self.max_stack

    def copy(self) -> "Item":
        return Item(
            self.name,
            self.description,
            self.item_type,
            self.max_stack,
            self.quantity,
            self.icon,
            self.price,
            self.effect,
        )

    @staticmethod
    def create(name, quantity) -> "Item":
        """
        - Si le nom est inconnu alors ValueError
        - Si l'image est introuvable alors texture not_found
        """
        if name not in item_dic:
            raise ValueError(f"Item inconnu : '{name}'. Vérifier item_dic.")

        data = item_dic[name]

        try:
            icon_surface = pygame.image.load(data["icon_path"]).convert_alpha()
        except (FileNotFoundError, pygame.error):
            print(f"\nImage de '{name}' introuvable : '{data['icon_path']}'.\n")
            icon_surface = pygame.image.load(
                os.path.join(INVENTORY_ASSET_DIRECTORY, "not_found.png")
            ).convert_alpha()

        icon_surface = pygame.transform.scale(icon_surface, (32, 32))

        return Item(
            name=name,
            description=data["description"],
            item_type=data["item_type"],
            max_stack=data["max_stack"],
            quantity=quantity,
            icon=icon_surface,
            price=data["price"],
            effect=data["effect"],
        )


class Inventaire:
    """
    Grille d'inventaire, logique pure.

    Gère :
        - La logique des items (ajouter, swap, ...)

    Usage :
        inv = Inventaire(rows=4, cols=8)
        inv.add_item(Item.create("Diamant", 1))
    """

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid: list[list[Item | None]] = [
            [None for i in range(cols)] for y in range(rows)
        ]

    def get(self, row, col) -> Item | None:
        """Retourne un (Item ou None) de la position row, col"""
        return self.grid[row][col]

    def set(self, row, col, item: Item | None):
        """Place un (Item ou None) à la position row, col"""
        self.grid[row][col] = item

    def add_item(self, item: Item):
        """
        Empile sur les stacks existants du même item
        puis place le reste dans les cases vides.

        Retourne 0 si tout a été ajouté,
        ou la quantité restante si l'inventaire était plein.
        """
        remaining = item.quantity

        # empiler sur les stacks existants
        for i in range(self.rows):
            for j in range(self.cols):
                slot = self.grid[i][j]
                if slot is not None and slot.can_stack_with(item):
                    ajout = min(slot.max_stack - slot.quantity, remaining)
                    slot.quantity += ajout
                    remaining -= ajout
                    if remaining == 0:
                        return 0

        # placer le reste dans des cases vides
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] is None:
                    new_item = item.copy()
                    new_item.quantity = min(remaining, item.max_stack)
                    remaining -= new_item.quantity
                    self.grid[i][j] = new_item
                    if remaining == 0:
                        return 0

        return remaining

    def remove_item(self, row, col, qty) -> Item | None:
        """
        Retire une quantité : "qty" d'items du slot à la position row, col.
        Retourne une copie de l'item retiré, ou None si la case est vide.
        Supprime le slot si la quantité tombe à 0.
        """
        item = self.grid[row][col]
        if item is None:
            return None
        removed = item.copy()
        removed.quantity = min(qty, item.quantity)
        item.quantity -= removed.quantity
        if item.quantity <= 0:
            self.grid[row][col] = None
        return removed

    def swap(self, row_a, col_a, row_b, col_b):
        """
        Échange deux cases du même inventaire.
        Si l'item est stackable avac l'autre alors on fusionne.
        Sinon échange classique.
        """
        item_a = self.grid[row_a][col_a]
        item_b = self.grid[row_b][col_b]

        if item_a is not None and item_b is not None and item_b.can_stack_with(item_a):
            ajout = min(item_b.max_stack - item_b.quantity, item_a.quantity)
            item_b.quantity += ajout
            item_a.quantity -= ajout
            if item_a.quantity <= 0:
                self.grid[row_a][col_a] = None
        else:
            self.grid[row_a][col_a], self.grid[row_b][col_b] = item_b, item_a

    def transfer(self, row_a, col_a, other_inv: "Inventaire", row_b, col_b):
        """
        Échange deux cases d'inventaire differents.
        Si l'item est stackable avac l'autre alors on fusionne.
        Sinon échange classique.
        """
        item_a = self.grid[row_a][col_a]
        item_b = other_inv.grid[row_b][col_b]

        if item_a is not None and item_b is not None and item_b.can_stack_with(item_a):
            ajout = min(item_b.max_stack - item_b.quantity, item_a.quantity)
            item_b.quantity += ajout
            item_a.quantity -= ajout
            if item_a.quantity <= 0:
                self.grid[row_a][col_a] = None
        else:
            self.grid[row_a][col_a], other_inv.grid[row_b][col_b] = item_b, item_a

    def count_item(self, name: str) -> int:
        """Retourne la quantité totale d'un item d'un iventaire par son nom."""
        return sum(s.quantity for row in self.grid for s in row if s and s.name == name)

    def has_items(self, objectifs: list[dict]) -> bool:
        """Retourne True si la grille contient tous les items requis."""
        for obj in objectifs:
            total = self.count_item(obj["item"])
            if total < obj["quantite"]:
                return False
        return True

    def remove_items(self, objectifs: list[dict]):
        """Retire de la grille les quantités exactes définies dans objectifs."""
        for obj in objectifs:
            reste = obj["quantite"]
            for i in range(self.rows):
                for j in range(self.cols):
                    slot = self.grid[i][j]
                    if slot and slot.name == obj["item"] and reste > 0:
                        retire = min(slot.quantity, reste)
                        self.remove_item(i, j, retire)
                        reste -= retire


class InventaireUI:
    """
    Rendu Pygame d'une grille d'inventaire.

    Gère :
        - L'affichage du panneau (image + titre + icônes + highlight + tooltip)
        - La détection de la case sous la souris
    """

    def __init__(
        self,
        screen,
        name,
        inv: Inventaire,
        pos: tuple,
        is_merchant,
        is_visible,
    ):
        self.screen: pygame.Surface = screen

        self.name = name
        self.inv = inv
        self.pos = pos
        self.is_visible = is_visible
        self.is_merchant = is_merchant
        if is_merchant:
            self.price_multiplier = round(random.uniform(1.2, 1.6), 2)
        else:
            self.price_multiplier = 1.0

        self.slot_size = 52  # taille d'une case en px
        self.slot_margin = 4  # espace entre les cases en px
        self.padding = 21  # bord du panneau en px
        self.title_height = 11  # espace au-dessus pour le titre en px

        self.image = pygame.image.load(
            os.path.join(INVENTORY_ASSET_DIRECTORY, "chest.png")
        ).convert_alpha()
        self.image_largeur = self.image.get_width()

        # Titre panneau
        self.font_title = pygame.font.SysFont("segoeui", 14, bold=True)
        # Compteur stack
        self.font_stack = pygame.font.SysFont("segoeui", 12, bold=True)
        # Nom item tooltip
        self.font_tip_b = pygame.font.SysFont("segoeui", 13, bold=True)
        # Description tooltip
        self.font_tip = pygame.font.SysFont("segoeui", 13)
        # Sous-textes tooltip
        self.font_hint = pygame.font.SysFont("segoeui", 11)

        # Les quatres types d'objet :
        self.type_colors = {
            "Consommable": (130, 220, 90),  # Vert
            "Bric-à-brac": (160, 160, 185),  # Gris
            "Curiosités": (10, 140, 255),  # Bleu
            "Légendes": (255, 100, 40),  # Orange
        }

    def slot_rect(self, row, col) -> pygame.Rect:
        """
        Retourne le pygame.Rect d'une case de la position row, col.
        """
        return pygame.Rect(
            self.pos[0] + self.padding + col * (self.slot_size + self.slot_margin),
            self.pos[1]
            + self.padding
            + self.title_height
            + row * (self.slot_size + self.slot_margin),
            self.slot_size,
            self.slot_size,
        )

    def slot_at(self, mouse_pos) -> tuple[int, int] | None:
        """
        Retourne la position row, col de la case sous la souris, ou None.
        """
        for i in range(self.inv.rows):
            for j in range(self.inv.cols):
                if self.slot_rect(i, j).collidepoint(mouse_pos):
                    return (i, j)
        return None

    def draw(self, mouse_pos, drag_mgr: "InventaireManager | None" = None):
        """
        Dessine le panneau complet dans l'ordre :
        - Image de fond
        - Titre du panneau
        - Highlight de survol
        - Icônes des items
        """
        if not self.is_visible:
            return

        # image de fond
        self.screen.blit(self.image, self.pos)

        # titre centré dans la zone titre
        title_surf = self.font_title.render(self.name, True, (230, 210, 160))
        self.screen.blit(
            title_surf,
            (
                self.pos[0] + (self.image_largeur - title_surf.get_width()) // 2,
                self.pos[1]
                + (self.padding + self.title_height - title_surf.get_height()) // 2
                - 2,
            ),
        )

        # position de la case survolée
        hovered = self.slot_at(mouse_pos)

        # highlight de la case survolée
        if hovered is not None:
            overlay = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 60))
            self.screen.blit(overlay, self.slot_rect(hovered[0], hovered[1]))

        # icônes des items
        for i in range(self.inv.rows):
            for j in range(self.inv.cols):
                item = self.inv.get(i, j)
                rect = self.slot_rect(i, j)

                # La case source du drag paraît vide :
                # l'item "flotte" sous la souris, on ne le dessine pas ici
                is_drag_source = (
                    drag_mgr is not None
                    and drag_mgr.drag_source_ui is self
                    and drag_mgr.drag_source_row == i
                    and drag_mgr.drag_source_col == j
                )

                if item is not None and not is_drag_source:
                    icon_x = rect.x + (self.slot_size - item.icon.get_width()) // 2
                    icon_y = rect.y + (self.slot_size - item.icon.get_height()) // 2
                    self.screen.blit(item.icon, (icon_x, icon_y))

                    # compteur de stack — uniquement si stackable et quantité > 1
                    if item.max_stack > 1 and item.quantity > 1:
                        qty_surf = self.font_stack.render(
                            str(item.quantity), True, (255, 220, 0)
                        )
                        self.screen.blit(
                            qty_surf,
                            (
                                rect.right
                                - qty_surf.get_width()
                                - 3,  # aligné à droite
                                rect.bottom
                                - qty_surf.get_height()
                                - 2,  # aligné en bas
                            ),
                        )

    def draw_tooltip(self, item: Item, mouse_pos):
        """
        Affiche une bulle d'info au survol d'un item :
            - Nom (gras)
            - Type (couleur selon rareté)
            - Séparateur
            - Description
            - Soin/Malus : +-X PV   (Consommable uniquement)
            - Valeur : X Mole_Coins
            - Quantité / max        (si stackable)
            - Hint clic droit       (Consommable uniquement)

        Et se repositionne automatiquement pour ne pas sortir de l'écran !
        """
        type_color = self.type_colors.get(item.item_type, (160, 160, 185))

        lines = [
            (item.name, self.font_tip_b, (235, 235, 245)),
            (item.item_type, self.font_hint, type_color),
            ("", self.font_hint, (160, 160, 185)),  # séparateur
            (item.description, self.font_tip, (210, 210, 220)),
        ]

        # effet de soin/malus pour consommable uniquement
        if item.item_type == "Consommable" and item.effect is not None:
            couleur = (130, 220, 130) if item.effect >= 0 else (220, 80, 80)
            label = "Soin" if item.effect >= 0 else "Malus"
            lines.append(
                (
                    f"{label} : {item.effect:+d} PV",
                    self.font_hint,
                    couleur,
                )
            )

        # prix de vente (ou achat si inventaire de marchand) pour tous les types d'Item
        if self.is_merchant:
            displayed_price = round(item.price * self.price_multiplier)
            lines.append(
                (
                    f"Prix d'achat : {displayed_price} Mole_Coins",
                    self.font_hint,
                    (255, 220, 0),
                )
            )
        else:
            lines.append(
                (
                    f"Valeur de vente : {item.price} Mole_Coins",
                    self.font_hint,
                    (255, 220, 0),
                )
            )

        # quantité si stackable
        if item.max_stack > 1:
            lines.append(
                (
                    f"Quantité : {item.quantity} / {item.max_stack}",
                    self.font_hint,
                    (160, 160, 185),
                )
            )

        # "[Clic droit] Utiliser" pour consommable uniquement
        if item.item_type == "Consommable":
            lines.append(("[Clic droit] Utiliser", self.font_hint, (130, 215, 130)))

        pad = 10  # marge bordure
        gap = 3  # espace entre les infos

        rendered = []
        for text, font, color in lines:
            if text == "":
                rendered.append(None)
            else:
                rendered.append((font.render(text, True, color), color))

        # dimensions du tooltip
        text_surfaces = [r[0] for r in rendered if r is not None]
        w = max((s.get_width() for s in text_surfaces), default=80) + pad * 2
        h = (
            sum(s.get_height() + gap for s in text_surfaces)
            + sum(6 for r in rendered if r is None)
            + pad * 2
        )

        # position : décalé depuis la souris, ajusté pour ne pas sortir de l'écran
        tx, ty = mouse_pos[0] + 18, mouse_pos[1] + 10
        sw, sh = self.screen.get_size()
        if tx + w > sw:
            tx = mouse_pos[0] - w - 8
        if ty + h > sh:
            ty = mouse_pos[1] - h - 8

        # surface du tooltip
        tip_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(tip_surf, (18, 18, 30, 218), (0, 0, w, h), border_radius=7)
        pygame.draw.rect(
            tip_surf, (30, 30, 50, 255), (0, 0, w, h), width=3, border_radius=7
        )
        pygame.draw.rect(
            tip_surf,
            (120, 120, 160, 255),
            (2, 2, w - 4, h - 4),
            width=1,
            border_radius=6,
        )

        # enfin : rendu ligne par ligne
        y = pad
        for r in rendered:
            if r is None:
                pygame.draw.line(
                    tip_surf, (80, 80, 110), (pad, y + 2), (w - pad, y + 2)
                )
                y += 6
            else:
                s, _ = r
                tip_surf.blit(s, (pad, y))
                y += s.get_height() + gap

        self.screen.blit(tip_surf, (tx, ty))


class InventaireManager:
    """
    Gère plusieurs InventaireUI ainsi que le drag & drop.

    Usage :
        drag_mgr = DragManager([ui_joueur, ui_coffre])
        drag_mgr.handle_event(event, mouse_pos, on_use=ma_fonction)
        drag_mgr.draw(screen, mouse_pos)
    """

    def __init__(self, screen, ui_list: list[InventaireUI]):
        self.screen: pygame.Surface = screen
        self.ui_list = ui_list  # Tous les panneaux gérés

        self.drag_item = None  # copie de l'Item drag
        self.drag_source_ui = None  # inventaireUI source
        self.drag_source_row = None  # ligne de la case source
        self.drag_source_col = None  # colonne de la case source

    def add_ui(self, ui: InventaireUI):
        """Ajoute un panneau (Exemple : on ouvre un coffre)."""
        self.ui_list.append(ui)

    def remove_ui(self, ui: InventaireUI):
        """Retire un panneau (Exemple : on ferme un coffre)."""
        self.ui_list.remove(ui)

    def handle_event(
        self,
        event: pygame.event.Event,
        mouse_pos: tuple,
        on_use=None,
    ):
        """
        Traite les événements souris pour tous les panneaux.

        on_use(item, slot, inventaire_ui) — callback clic droit,
        appelé uniquement pour les Consommables.
        """

        # Clic gauche :
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for ui in self.ui_list:
                if not ui.is_visible:
                    continue
                slot = ui.slot_at(mouse_pos)
                if slot is not None:
                    item = ui.inv.get(slot[0], slot[1])
                    if item is not None:

                        # Shift + clic gauche alors transfert instantané vers l'autre inventaire
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            # cherche le premier inventaire visible différent de l'actuel
                            for target_ui in self.ui_list:
                                if target_ui is ui or not target_ui.is_visible:
                                    continue
                                # tente d'ajouter dans l'autre inventaire
                                reste = target_ui.inv.add_item(item)
                                if reste < item.quantity:
                                    # au moins une partie a été transférée
                                    transfere = item.quantity - reste
                                    item.quantity -= transfere
                                    if item.quantity <= 0:
                                        ui.inv.set(slot[0], slot[1], None)
                                break  # on essaie que le premier autre inventaire trouvé

                        # Clic gauche normal alors démarre le drag
                        else:
                            self.drag_item = item.copy()
                            self.drag_source_ui = ui
                            self.drag_source_row = slot[0]
                            self.drag_source_col = slot[1]

                    break

        # Clic droit :
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            for ui in self.ui_list:
                if not ui.is_visible:
                    continue
                slot = ui.slot_at(mouse_pos)
                if slot is not None:
                    item = ui.inv.get(slot[0], slot[1])
                    if item is not None:

                        # Shift + clic droit alors on divise le stack par 2
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            if item.max_stack > 1 and item.quantity > 1:
                                moitie = item.quantity // 2

                                # cherche une case vide uniquement dans le même inventaire
                                placed = False
                                for i in range(ui.inv.rows):
                                    for j in range(ui.inv.cols):
                                        if ui.inv.get(i, j) is None and (i, j) != slot:
                                            new_item = item.copy()
                                            new_item.quantity = moitie
                                            ui.inv.set(i, j, new_item)
                                            item.quantity -= moitie
                                            placed = True
                                            break
                                    if placed:
                                        break
                                # si pas de case vide dans cet inventaire alors on fait rien

                        # Clic droit simple alors utiliser pour "Consommable" uniquement
                        elif on_use is not None and item.item_type == "Consommable":
                            on_use(item, slot, ui)

                    break

        # Relâchement gauche (drop)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_item is None:
                return

            for ui in self.ui_list:
                if not ui.is_visible:
                    continue
                slot = ui.slot_at(mouse_pos)
                if slot is not None:
                    if self.drag_source_ui is ui:
                        # même inventaire alors swap
                        if slot != (self.drag_source_row, self.drag_source_col):
                            ui.inv.swap(
                                self.drag_source_row,
                                self.drag_source_col,
                                *slot,
                            )
                    else:
                        # sinon cross-inventaire alors transfer
                        self.drag_source_ui.inv.transfer(
                            self.drag_source_row,
                            self.drag_source_col,
                            ui.inv,
                            *slot,
                        )
                    break

            # drop réussi ou relâché dans le vide on reset l'état du drag
            self.drag_item = None
            self.drag_source_ui = None
            self.drag_source_row = None
            self.drag_source_col = None

    def draw(self, mouse_pos):
        """
        Dessine tous les panneaux visibles,
        puis la tooltip et enfin
        l'item flottant par-dessus tout.
        """
        for ui in self.ui_list:
            ui.draw(mouse_pos, self)

        # affiche la tooltip
        if self.drag_item is None:
            for ui in self.ui_list:
                if not ui.is_visible:
                    continue
                hovered = ui.slot_at(mouse_pos)
                if hovered is not None:
                    item = ui.inv.get(hovered[0], hovered[1])
                    if item is not None:
                        ui.draw_tooltip(item, mouse_pos)
                    break
        else:
            self.draw_dragged_item(mouse_pos)

    def draw_dragged_item(self, mouse_pos):
        """Dessine l'item (semi-transparent) sous la souris pendant un drag."""
        ghost = self.drag_item.icon.copy()
        ghost.set_alpha(180)

        # Item drag : centré sous la souris
        icon_x = mouse_pos[0] - ghost.get_width() // 2
        icon_y = mouse_pos[1] - ghost.get_height() // 2
        self.screen.blit(ghost, (icon_x, icon_y))


# TOUCHE I ET E POUR TESTER
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))

    inv_joueur = Inventaire(rows=4, cols=8)
    inv_joueur.add_item(Item.create("Potion Rouge", 5))
    inv_joueur.add_item(Item.create("Grande Potion Rouge", 2))
    inv_joueur.add_item(Item.create("Pain", 4))
    inv_joueur.add_item(Item.create("Champignon", 10))
    inv_joueur.add_item(Item.create("Pièce de cuivre", 120))
    inv_joueur.add_item(Item.create("Os", 80))
    inv_joueur.add_item(Item.create("Engrenage", 3))
    inv_joueur.add_item(Item.create("Cristal", 5))
    inv_joueur.add_item(Item.create("Crâne", 1))
    inv_joueur.add_item(Item.create("Diamant", 1))
    inv_joueur.add_item(Item.create("Bâton de Rubis", 1))

    inv_coffre = Inventaire(rows=4, cols=8)
    inv_coffre.add_item(Item.create("Petite Potion Rouge", 8))
    inv_coffre.add_item(Item.create("Fromage", 6))
    inv_coffre.add_item(Item.create("Pièce d'or", 50))
    inv_coffre.add_item(Item.create("Carte Ancienne", 1))
    inv_coffre.add_item(Item.create("Viande de monstre", 1))

    ui_joueur = InventaireUI(
        screen,
        name="Sac du joueur",
        inv=inv_joueur,
        pos=(400, 80),
        is_merchant=False,
        is_visible=True,
    )
    ui_coffre = InventaireUI(
        screen,
        name="Marchant de drogue",
        inv=inv_coffre,
        pos=(30, 400),
        is_merchant=True,
        is_visible=True,
    )

    drag_mgr = InventaireManager(screen, [ui_joueur, ui_coffre])

    def on_use(item: Item, slot: tuple, ui: InventaireUI):
        """Consomme 1 unité de l'item utilisé."""
        ui.inv.remove_item(*slot, 1)
        print(f"Vous vous soigner de {item.effect} HP")
        # self.player.hp += item.effect par exemple

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_i:
                    ui_joueur.is_visible = not ui_joueur.is_visible
                if event.key == pygame.K_e:
                    ui_coffre.is_visible = not ui_coffre.is_visible

            drag_mgr.handle_event(event, mouse_pos, on_use=on_use)

        # affichage
        screen.fill((20, 20, 30))
        drag_mgr.draw(mouse_pos)
        pygame.display.flip()

    pygame.quit()
