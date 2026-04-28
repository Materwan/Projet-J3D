import pygame
from inventory import Item, Inventaire, InventaireUI, InventaireManager

"""
pnj_dic c'est la base de données des PNJ du jeu
Chaque PNJ a :
  - pnj_type           : "Basic", "Merchant" ou "Quest"
  - image_path         : chemin vers l'image depuis le dossier Ressources
  - dialogues          : liste de dialogues (pas mettre plus de 550 caractères par element)
  - interaction_radius : rayon en pixels pour afficher la touche [E]
  - stock              : dictionnaire du stock : { name_item: quantite } pour pnj_type == "Merchant", None sinon
  - quests             : liste de quêtes pour pnj_type == "Quest", None sinon
"""
pnj_dic: dict[str, dict] = {
    # =========================================================================
    # PNJ : BASIC
    # =========================================================================
    "Vieux Taupier": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Ah, bonjour jeune aventurier ! Les chemins sont dangereux par ici...",
            "On dit que des créatures étranges rôdent dans les tunnels du nord.",
            "Soyez prudent, et revenez me voir si vous avez besoin de conseils.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
    "Garde Roland": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Halte ! ... Ah non, vous pouvez passer.",
            "Je surveille cette porte depuis dix ans. Rien à signaler.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
    # =========================================================================
    # PNJ : MERCHANT
    # =========================================================================
    "Marchande Isabelle": {
        "pnj_type": "Merchant",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Bienvenue dans ma boutique ! J'ai ce qu'il vous faut.",
            "Revenez quand vous voulez, j'ai toujours du stock frais !",
        ],
        "interaction_radius": 80,
        "stock": {
            "Potion Rouge": 10,
            "Grande Potion Rouge": 5,
            "Pain": 8,
            "Fromage": 6,
            "Vin blanc": 3,
            "Champignon": 15,
        },
        "quests": None,
    },
    # =========================================================================
    # PNJ : QUEST
    # =========================================================================
    "Forgeron Otto": {
        "pnj_type": "Quest",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": ["Merci encore pour votre aide, je ne l'oublierai pas."],
        "interaction_radius": 80,
        "stock": None,
        "quests": [
            {
                "titre": "Les matériaux du forgeron",
                "description": "Otto a besoin de 5 Bûches et 3 Charbons pour forger une arme légendaire.",
                "objectifs": [
                    {"item": "Bûche", "quantite": 5},
                    {"item": "Charbon", "quantite": 3},
                ],
                "recompense_coins": 150,
                "recompense_items": [
                    {"item": "Bâton de Rubis", "quantite": 1},
                ],
                "dialogue_debut": [
                    "J'ai besoin de matériaux pour forger mon chef-d'œuvre.",
                    "Sans ces ressources je ne peux rien faire. Pouvez-vous m'aider ?",
                ],
                "dialogue_actif": [
                    "Vous avez accepté de m'aider, j'espère que vous trouverez tout ça.",
                    "Il me faut 5 Bûches et 3 Charbons. Revenez quand vous les aurez.",
                ],
                "dialogue_complet": [
                    "Vous avez tout ce qu'il faut ! Remettez-moi les matériaux.",
                ],
            },
            {
                "titre": "La commande spéciale",
                "description": "Après le succès, Otto a besoin d'une Pioche et d'un Marteau.",
                "objectifs": [
                    {"item": "Pioche", "quantite": 1},
                    {"item": "Marteau", "quantite": 1},
                ],
                "recompense_coins": 300,
                "recompense_items": [
                    {"item": "Pierre Runique", "quantite": 2},
                ],
                "dialogue_debut": [
                    "Excellent travail ! J'ai une nouvelle commande.",
                    "Il me faut une Pioche et un Marteau cette fois.",
                ],
                "dialogue_actif": [
                    "J'ai besoin d'une Pioche et d'un Marteau. Revenez quand vous les aurez.",
                ],
                "dialogue_complet": [
                    "Parfait, vous avez tout ! Donnez-les moi.",
                ],
            },
        ],
    },
    "Vieille Sorcière": {
        "pnj_type": "Quest",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": ["Merci encore pour votre aide, je ne l'oublierai pas."],
        "interaction_radius": 80,
        "stock": None,
        "quests": [
            {
                "titre": "La potion de la sorcière",
                "description": "La sorcière a besoin de 3 Champignons et d'un Cristal pour finir sa potion.",
                "objectifs": [
                    {"item": "Champignon", "quantite": 3},
                    {"item": "Cristal", "quantite": 1},
                ],
                "recompense_coins": 200,
                "recompense_items": [
                    {"item": "Grande Potion Rouge", "quantite": 2},
                ],
                "dialogue_debut": [
                    "Je prépare une potion très rare, mais il me manque des ingrédients.",
                    "Si vous me rapportez ce qu'il faut, je vous récompenserai bien.",
                ],
                "dialogue_actif": [
                    "Vous cherchez encore mes ingrédients ? Dépêchez-vous !",
                ],
                "dialogue_complet": [
                    "Parfait ! Exactement ce qu'il me faut. Prenez votre récompense.",
                ],
            },
        ],
    },
}


class PNJ:
    """
    Données et état d'un personnage non joueur.

    Les frames d'animation sont chargées depuis :
        Ressources/PNJ/<...>/sprite_0, sprite_1, sprite_2 pour idle
        Ressources/PNJ/<...>/sprite_3 sprite_4 pour hello

    Usage :
        pnj = PNJ.create("Marchande Isabelle", pos=(500, 300))
    """

    def __init__(
        self,
        name: str,
        pnj_type: str,
        pos: tuple,
        frames: list[pygame.Surface],
        dialogues: list[str],
        interaction_radius: int,
        stock: dict | None,
        quests: list[dict] | None,
    ):
        self.name = name
        self.pnj_type = pnj_type
        self.pos = list(pos)
        self.frames = frames
        self.sprite = frames[0]
        self.dialogues = dialogues
        self.interaction_radius = interaction_radius

        self.frame_index = 0

        # Stock si Marchand
        if pnj_type == "Merchant" and stock is not None:
            self.stock = Inventaire(rows=4, cols=8)
            for name_item, qty in stock.items():
                self.stock.add_item(Item.create(name_item, qty))
        else:
            self.stock = None

        # Quêtes si donneur de quêtes
        self.quests = quests
        self.quest_index = 0
        if quests is not None:
            self.quest_etat = "disponible"
        else:
            self.quest_etat = None

    def update(self):
        self.frame_index = (self.frame_index + 1) % (len(self.frames) * 10)
        self.sprite = self.frames[self.frame_index // 10]

    def is_near(self, player_pos) -> bool:

        dx = self.pos[0] - player_pos[0]
        dy = self.pos[1] - player_pos[1]
        return (dx * dx + dy * dy) ** 0.5 <= self.interaction_radius

    def get_current_dialogue(self):
        if self.pnj_type == "Quest":
            if self.quest_etat == "disponible":
                return self.quests[self.quest_index]["dialogue_debut"]
            elif self.quest_etat == "active":
                return self.quests[self.quest_index]["dialogue_actif"]
            elif self.quest_etat == "complete":
                return self.quests[self.quest_index]["dialogue_complet"]
        return self.dialogues

    @staticmethod
    def create(name, pos) -> "PNJ":
        """
        - Si le nom est inconnu alors ValueError
        - Si une ou plusieurs images sont introuvable alors texture not_found
        """
        if name not in pnj_dic:
            raise ValueError(f"PNJ inconnu : '{name}'. Vérifier pnj_dic.")

        data = pnj_dic[name]

        try:
            frames = []
            for i in range(3):
                image = pygame.image.load(
                    data["image_path"] + f"sprite_{i}.png"
                ).convert_alpha()
                frames.append(pygame.transform.scale(image, (100, 100)))
        except (FileNotFoundError, pygame.error):
            print(
                f"\nUne ou plusieurs images de '{name}' introuvable : '{data['image_path']}'.\n"
            )
            frames = [
                pygame.image.load(
                    "Ressources/Animations/PNJ/not_found.png"
                ).convert_alpha()
            ]

        return PNJ(
            name=name,
            pnj_type=data["pnj_type"],
            pos=pos,
            frames=frames,
            dialogues=data["dialogues"],
            interaction_radius=data["interaction_radius"],
            stock=data["stock"],
            quests=data["quests"],
        )


class MenuInteractionUI:
    """
    Affiche le menu d'interaction (Parler, Optionnel(Quête ou Échanger), Quitter) en bas d'écran.
    Pour la navigation : souris uniquement + la touche Échap pour quitter.
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):
        self.screen = screen
        self.largeur = largeur
        self.hauteur = hauteur

        self.pnj: PNJ | None = None
        self.options = []

        self.font_nom = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_btn = pygame.font.SysFont("segoeui", 13)
        self.font_hint = pygame.font.SysFont("segoeui", 11)

        self.x = 22
        self.y = self.hauteur - 172
        self.larg = self.largeur - 44
        self.haut = 150

    def open(self, pnj: PNJ):
        self.pnj = pnj
        self.options = ["Parler"]
        if pnj.pnj_type == "Merchant":
            self.options.append("Échanger")
        elif pnj.pnj_type == "Quest" and pnj.quest_etat != "terminee":
            self.options.append("Quête")
        self.options.append("Quitter")

    def handle_event(self, event: pygame.event.Event, mouse_pos) -> str | None:
        """Renvoie None si rien de nouveau sinon soit Parler, Quête, Échanger ou Quitter"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pnj = None
            return "Quitter"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            rects = []
            for i in range(len(self.options)):
                rects.append(pygame.Rect(136 + i * 162, self.y + 45, 150, 36))
            for i in range(len(self.options)):
                if rects[i].collidepoint(mouse_pos):
                    self.pnj = None
                    return self.options[i]
        return None

    def draw(self, mouse_pos):
        # Background
        interface = pygame.Surface((self.larg, self.haut), pygame.SRCALPHA)
        pygame.draw.rect(
            interface, (10, 10, 22, 200), (0, 0, self.larg, self.haut), border_radius=10
        )
        pygame.draw.rect(
            interface,
            (75, 75, 120, 255),
            (0, 0, self.larg, self.haut),
            width=2,
            border_radius=10,
        )
        self.screen.blit(interface, (self.x, self.y))

        # Portrait
        p_rect = pygame.Rect(self.x + 12, self.y + 12, 90, self.haut - 24)
        pygame.draw.rect(self.screen, (22, 22, 40), p_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 70, 110), p_rect, width=2, border_radius=6)
        portrait = pygame.transform.scale(
            self.pnj.sprite, (p_rect.width - 10, p_rect.height - 10)
        )
        self.screen.blit(portrait, (p_rect.x + 5, p_rect.y + 5))

        # Le nom du PNJ
        nom_s = self.font_nom.render(self.pnj.name, True, (230, 210, 160))
        self.screen.blit(nom_s, (136, self.y + 14))

        # Les boutons d'interactions
        for i in range(len(self.options)):
            option = self.options[i]
            btn = pygame.Rect(136 + 162 * i, self.y + 45, 150, 36)
            hovered = btn.collidepoint(mouse_pos)

            if hovered:
                col_bg = (60, 90, 160, 220)
                col_brd = (130, 160, 230, 255)
            else:
                col_bg = (28, 28, 48, 200)
                col_brd = (60, 60, 100, 255)

            bs = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
            pygame.draw.rect(bs, col_bg, (0, 0, btn.width, btn.height), border_radius=7)
            pygame.draw.rect(
                bs, col_brd, (0, 0, btn.width, btn.height), width=2, border_radius=7
            )
            self.screen.blit(bs, (btn.x, btn.y))

            text = self.font_btn.render(option, True, (240, 240, 255))
            self.screen.blit(
                text,
                (
                    btn.x + (btn.width - text.get_width()) // 2,
                    btn.y + (btn.height - text.get_height()) // 2,
                ),
            )


class DialogueUI:
    """
    Affiche les dialogues d'un PNJ dialogue par dialogue avec effet machine à écrire.
    Avancer : [E], [Entrée], [Espace] ou clic gauche.
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):
        self.screen = screen
        self.largeur = largeur
        self.hauteur = hauteur

        self.pnj: PNJ | None = None
        self.list_dialogue: list[str] = []
        self.dialogue = 0
        self.caractere = 0
        self.timer = 0.0
        self.done = False  # True quand le dialogue a été entièrement affichée
        self.char_delay = 28  # le délai en ms entre chaque caractère

        self.font_nom = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_text = pygame.font.SysFont("segoeui", 13)
        self.font_hint = pygame.font.SysFont("segoeui", 11)

        self.x = 22
        self.y = self.hauteur - 172
        self.larg = self.largeur - 44
        self.haut = 150

    def open(self, pnj: PNJ):
        self.pnj = pnj
        self.list_dialogue = pnj.get_current_dialogue()
        self.dialogue = 0
        self.caractere = 0
        self.timer = 0.0
        self.done = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Renvoie True si fin du dialogue sinon False"""
        if (
            event.type == pygame.KEYDOWN
            and event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE)
        ) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):

            # si dialogue finie alors dialogue suivante
            if self.done:

                self.dialogue += 1
                if self.dialogue >= len(self.list_dialogue):
                    self.pnj = None
                    return True

                self.caractere = 0
                self.timer = 0.0
                self.done = False

            else:  # dialogue pas fini alors l'afficher en entier
                self.caractere = len(self.list_dialogue[self.dialogue])
                self.done = True

        return False

    def update(self, dt):
        self.timer += dt
        while self.timer >= self.char_delay:
            self.timer -= self.char_delay
            self.caractere += 1
            if self.caractere >= len(self.list_dialogue[self.dialogue]):
                self.done = True

    def draw(self):
        # Background
        interface = pygame.Surface((self.larg, self.haut), pygame.SRCALPHA)
        pygame.draw.rect(
            interface, (10, 10, 22, 200), (0, 0, self.larg, self.haut), border_radius=10
        )
        pygame.draw.rect(
            interface,
            (75, 75, 120, 255),
            (0, 0, self.larg, self.haut),
            width=2,
            border_radius=10,
        )
        self.screen.blit(interface, (self.x, self.y))

        # Portrait
        p_rect = pygame.Rect(self.x + 12, self.y + 12, 90, self.haut - 24)
        pygame.draw.rect(self.screen, (22, 22, 40), p_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 70, 110), p_rect, width=2, border_radius=6)
        portrait = pygame.transform.scale(
            self.pnj.sprite, (p_rect.width - 10, p_rect.height - 10)
        )
        self.screen.blit(portrait, (p_rect.x + 5, p_rect.y + 5))

        # Le nom du PNJ
        nom_s = self.font_nom.render(self.pnj.name, True, (230, 210, 160))
        self.screen.blit(nom_s, (136, self.y + 14))

        # Texte style machine à écrire
        for elt in wrap_text(
            self.list_dialogue[self.dialogue][: self.caractere],
            self.font_text,
            self.larg - 102,
        ):
            self.screen.blit(
                self.font_text.render(elt, True, (210, 210, 222)), (136, self.y + 39)
            )

        # Numéro de dialogue
        dialogue_s = self.font_hint.render(
            f"{self.dialogue + 1} / {len(self.list_dialogue)}", True, (110, 110, 155)
        )
        self.screen.blit(
            dialogue_s,
            (
                self.x + self.larg - dialogue_s.get_width() - 12,
                self.y + self.haut - dialogue_s.get_height() - 8,
            ),
        )

        # Si dialogue complet alors info pour switch de paragraphe
        if self.done:
            if self.dialogue >= len(self.list_dialogue) - 1:
                hint = "[E] Fermer"
            else:
                hint = "[E] Continuer"

            hs = self.font_hint.render(hint, True, (130, 200, 130))
            self.screen.blit(
                hs,
                (
                    self.x + self.larg - hs.get_width() - dialogue_s.get_width() - 26,
                    self.y + self.haut - hs.get_height() - 8,
                ),
            )


class BoutiqueUI:
    """
    Boutique en bas de l'écran.

    Colonne GAUCHE : inventaire du joueur  → clic = vendre 1 / Shift = tout le stack
    Colonne DROITE : stock du marchand     → clic = acheter 1 / Shift = max affordable
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):
        self.screen = screen
        self.largeur = largeur
        self.hauteur = hauteur

        self.pnj: PNJ | None = None
        self.inv_joueur: Inventaire | None = None
        self.money = 0

        self.ui_stock: InventaireUI | None = None
        self.ui_joueur: InventaireUI | None = None

        self.msg_text = ""
        self.msg_color = (130, 220, 100)
        self.msgtimer: float = 0.0
        self.msg_duration: float = 2200.0

        self.font_nom = pygame.font.SysFont("georgiaui", 16, bold=True)
        self.font_text = pygame.font.SysFont("segoeui", 14)
        self.font_sub = pygame.font.SysFont("segoeui", 13)
        self.font_hint = pygame.font.SysFont("segoeui", 12)

        self.x = 22
        self.y = self.hauteur - 172
        self.larg = self.largeur - 44
        self.haut = 150

        self.larg_inv = 486  # la largeur en pixels d'une grille d'inventaire complète
        self.rect = pygame.Rect(self.x, self.y - 250, self.larg, 400)
        self.position_inv_x = self.larg // 2 - self.larg_inv + self.x // 2
        self.position_inv_y = self.hauteur - 370

        self.btn_hovered = False
        # rect du bouton fermer de la boutique
        self.btn = pygame.Rect(
            self.rect.x + self.rect.width // 2 - 75,
            self.rect.y + self.rect.height - 44,
            150,
            34,
        )

    def open(self, pnj: PNJ, inv_joueur: Inventaire, money: int):
        self.pnj = pnj
        self.inv_joueur = inv_joueur
        self.money = money

        self.ui_joueur = InventaireUI(
            self.screen,
            name="Votre sac",
            inv=inv_joueur,
            pos=(self.position_inv_x, self.position_inv_y),
            is_merchant=False,
            is_visible=True,
        )

        self.ui_stock = InventaireUI(
            self.screen,
            name=f"Stock — {pnj.name}",
            inv=pnj.stock,
            pos=(self.position_inv_x + self.larg_inv + 20, self.position_inv_y),
            is_merchant=True,
            is_visible=True,
        )

    def print_temporary_msg(self, text: str, color: tuple = (130, 220, 100)):
        self.msg_text = text
        self.msgtimer = self.msg_duration
        self.msg_color = color

    def acheter(self, row: int, col: int, is_shift_press: bool, item: Item):
        prix_unit = round(item.price * self.ui_stock.price_multiplier)

        qty = min(item.quantity, self.money // prix_unit) if is_shift_press else 1

        if qty <= 0 or self.money < prix_unit:
            self.print_temporary_msg("Pas assez de Mole_Coins !", (220, 140, 40))
            return

        to_add = item.copy()
        to_add.quantity = qty
        reste = self.inv_joueur.add_item(to_add)
        bought = qty - reste
        if bought == 0:
            self.print_temporary_msg("Inventaire plein !", (220, 140, 40))
            return
        cout = prix_unit * bought
        self.money -= cout
        self.pnj.stock.remove_item(row, col, bought)
        self.print_temporary_msg(
            f"Acheté : {item.name} ×{bought}  −{cout} Mole_Coins", (220, 80, 80)
        )

    def vendre(self, row: int, col: int, is_shift_press: bool, item: Item):
        qty = item.quantity if is_shift_press else 1

        vendu = self.inv_joueur.remove_item(row, col, qty)
        to_stock = vendu.copy()
        to_stock.quantity = qty
        self.pnj.stock.add_item(to_stock)

        prix_vente = item.price * qty
        self.money += prix_vente
        self.print_temporary_msg(
            f"Vendu : {item.name} ×{qty}  +{prix_vente} Mole_Coins", (130, 220, 100)
        )

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple) -> bool:
        """Renvoie True si fermeture boutique."""
        self.btn_hovered = self.btn.collidepoint(mouse_pos)

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_ESCAPE):
            self.btn_hovered = False
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_hovered:
                self.btn_hovered = False
                return True

            is_shift_press = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

            slot = self.ui_joueur.slot_at(mouse_pos)
            if slot is not None:
                item = self.inv_joueur.get(slot[0], slot[1])
                if item is not None:
                    self.vendre(slot[0], slot[1], is_shift_press, item)
                return False

            slot = self.ui_stock.slot_at(mouse_pos)
            if slot is not None:
                item = self.pnj.stock.get(slot[0], slot[1])
                if item is not None:
                    self.acheter(slot[0], slot[1], is_shift_press, item)

        return False

    def update(self, dt: float):
        if self.msgtimer > 0:
            self.msgtimer -= dt

    def draw(self, mouse_pos: tuple):

        # Background
        bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            bg,
            (10, 10, 22, 200),
            (0, 0, self.rect.width, self.rect.height),
            border_radius=10,
        )
        pygame.draw.rect(
            bg,
            (75, 75, 120, 255),
            (0, 0, self.rect.width, self.rect.height),
            width=2,
            border_radius=10,
        )
        self.screen.blit(bg, (self.rect.x, self.rect.y))

        # Nom de la boutique en haut à gauche
        self.screen.blit(
            self.font_nom.render(f"Boutique — {self.pnj.name}", True, (230, 210, 160)),
            (self.rect.x + 14, self.rect.y + 14),
        )

        # Hints d'interaction centrés au-dessus de chaque grille
        hint_v = self.font_hint.render(
            "Clic = vendre 1   Shift+clic = tout vendre", False, (230, 140, 140)
        )
        hint_a = self.font_hint.render(
            "Clic = acheter 1   Shift+clic = acheter max", False, (140, 230, 140)
        )
        joueur_center = self.ui_joueur.pos[0] + self.larg_inv // 2
        stock_center = self.ui_stock.pos[0] + self.larg_inv // 2
        hint_y = self.rect.y + 30
        self.screen.blit(hint_v, (joueur_center - hint_v.get_width() // 2, hint_y))
        self.screen.blit(hint_a, (stock_center - hint_a.get_width() // 2, hint_y))

        # Ligne séparatrice verticale entre les deux grilles
        sep_x = self.ui_joueur.pos[0] + self.larg_inv + 20 // 2
        sep_top = hint_y + hint_v.get_height()
        sep_bot = self.rect.y + 55 + self.ui_joueur.image.get_height()
        pygame.draw.line(
            self.screen, (110, 110, 180), (sep_x, sep_top), (sep_x, sep_bot), 2
        )

        # Grilles inventaire joueur (gauche) et stock marchand (droite)
        self.ui_joueur.draw(mouse_pos)
        self.ui_stock.draw(mouse_pos)

        # Tooltip de l'item survolé (priorité grille joueur, puis stock)
        for ui in (self.ui_joueur, self.ui_stock):
            slot = ui.slot_at(mouse_pos)
            if slot is not None:
                item = ui.inv.get(slot[0], slot[1])
                if item is not None:
                    ui.draw_tooltip(item, mouse_pos)
                break

        # Bouton Fermer centré en bas du panel
        bs = pygame.Surface((self.btn.width, self.btn.height), pygame.SRCALPHA)
        pygame.draw.rect(
            bs,
            (60, 90, 160, 220) if self.btn_hovered else (28, 28, 50, 200),
            (0, 0, self.btn.width, self.btn.height),
            border_radius=7,
        )
        pygame.draw.rect(
            bs,
            (130, 160, 230, 255) if self.btn_hovered else (55, 55, 100, 255),
            (0, 0, self.btn.width, self.btn.height),
            width=2,
            border_radius=7,
        )
        self.screen.blit(bs, (self.btn.x, self.btn.y))
        ts = self.font_sub.render(
            "Fermer", True, (240, 240, 255) if self.btn_hovered else (180, 180, 210)
        )
        self.screen.blit(
            ts,
            (
                self.btn.x + (self.btn.width - ts.get_width()) // 2,
                self.btn.y + (self.btn.height - ts.get_height()) // 2,
            ),
        )

        # Mole_Coins du joueur, centré entre les grilles et le bouton Fermer
        coins = self.font_text.render(f"Mole_Coins : {self.money}", True, (255, 215, 0))
        self.screen.blit(
            coins,
            (
                self.rect.x + self.rect.width // 2 - coins.get_width() // 2,
                self.btn.y - coins.get_height() - 8,
            ),
        )

        # Message de feedback temporaire (achat/vente/erreur), centré au-dessus des grilles
        if self.msgtimer > 0:
            msg = self.font_sub.render(self.msg_text, False, self.msg_color)
            msg.set_alpha(
                int(255 * min(1.0, self.msgtimer / (self.msg_duration * 0.4)))
            )
            self.screen.blit(
                msg,
                (
                    self.rect.x + self.rect.width // 2 - msg.get_width() // 2,
                    self.ui_joueur.pos[1] - msg.get_height() - 15,
                ),
            )


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Découpe le texte en une liste d'element pour que ça tiennent dans max_width pixels."""
    words = text.split(" ")
    liste = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                liste.append(current)
            current = word
    if current:
        liste.append(current)
    return liste
