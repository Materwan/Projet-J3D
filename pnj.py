import pygame
from sound import EFFECT
from inventory import Item, Inventaire, InventaireUI, InventaireManager
import math

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
    # PNJ SURFACE — MAP PRINCIPALE
    # =========================================================================
    "René le Sage": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Tu veux affronter les corbeaux ? Sois prudent, ils sont plus dangereux que tu ne le crois.",
            "Depuis que le chef corbeau a tué les dieux, le soleil ne s'est plus jamais levé...",
            "Nous les taupes, on s'est réfugiés sous terre. Toi tu oses sortir à la surface. Respect.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
    "Vieille Taupière": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Mon fils est parti chasser du corbeau il y a trois lunes... il n'est pas revenu.",
            "Les étoiles ont disparu le jour où ce maudit chef corbeau a volé les pouvoirs divins.",
            "Je prie encore les anciens dieux même si ça ne sert plus à rien. On n'abandonne pas sa foi comme ça.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
    # =========================================================================
    # MARCHANDS — MAP PRINCIPALE
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
    # DONNEURS DE QUÊTES — MAP PRINCIPALE
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
                "description": "Otto a besoin de 5 Bûches et 3 Charbons pour forger une arme capable de blesser les corbeaux.",
                "objectifs": [
                    {"item": "Bûche", "quantite": 5},
                    {"item": "Charbon", "quantite": 3},
                ],
                "recompense_coins": 150,
                "recompense_items": [{"item": "Bâton de Rubis", "quantite": 1}],
                "dialogue_debut": [
                    "Les corbeaux ont une peau épaisse. Mon acier ordinaire ne suffira pas.",
                    "Rapporte-moi 5 Bûches et 3 Charbons, je te forge quelque chose de spécial.",
                ],
                "dialogue_actif": [
                    "Toujours en quête des matériaux ? 5 Bûches et 3 Charbons, n'oublie pas.",
                ],
                "dialogue_complet": [
                    "Tu les as ! Donne-moi ça, je commence immédiatement.",
                ],
            },
            {
                "titre": "La commande spéciale",
                "description": "Otto a besoin d'une Pioche et d'un Marteau pour agrandir son atelier.",
                "objectifs": [
                    {"item": "Pioche", "quantite": 1},
                    {"item": "Marteau", "quantite": 1},
                ],
                "recompense_coins": 300,
                "recompense_items": [{"item": "Pierre Runique", "quantite": 2}],
                "dialogue_debut": [
                    "Mon atelier est trop petit. J'ai besoin d'agrandir.",
                    "Une Pioche et un Marteau, c'est tout ce qu'il me faut.",
                ],
                "dialogue_actif": [
                    "Une Pioche et un Marteau. Revenez quand vous les aurez.",
                ],
                "dialogue_complet": ["Parfait ! Exactement ce qu'il me faut."],
            },
        ],
    },
    # =========================================================================
    # PNJ BASIQUES — DONJON / MINES
    # =========================================================================
    "Mineur Rescapé": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Attention ! Ce donjon est rempli d'ennemis féroces ! J'ai failli ne pas en sortir.",
            "Les corbeaux ont colonisé les galeries du bas. Ne t'aventure pas trop loin sans te préparer.",
            "J'ai perdu mes outils en fuyant. Mais au moins j'ai la vie sauve.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
    "Explorateur Blessé": {
        "pnj_type": "Basic",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": [
            "Ces mines... elles sont maudites depuis que les corbeaux s'y sont installés.",
            "Je suis entré à cinq. Je suis le seul à ressortir. Ne fais pas la même erreur que nous.",
            "Si tu vois une grande salle tout au fond... fuis. Le chef de cette famille corbeau y trône.",
        ],
        "interaction_radius": 80,
        "stock": None,
        "quests": None,
    },
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
    # PNJ : UPGRADE
    # =========================================================================
    "Archiviste des Ames": {
        "pnj_type": "Upgrade",
        "image_path": "Ressources/Animations/PNJ/PNJ_1/",
        "dialogues": ["L'expérience forge l'âme... Je peux renforcer la vôtre."],
        "interaction_radius": 100,
        "stock": None,
        "quests": None,
    },
}


class PNJ:
    """
    Données et état d'un personnage non joueur.

    Usage :
        pnj = PNJ.create("Marchande Isabelle", pos=(500, 300))
    """

    def __init__(
        self,
        name: str,
        pnj_type: str,
        pos: list,
        frames: list[pygame.Surface],
        dialogues: list[str],
        interaction_radius: int,
        stock: dict | None,
        quests: list[dict] | None,
    ):
        self.name = name
        self.pnj_type = pnj_type
        self.pos = pos
        self.hitbox = pygame.Rect(pos[0], pos[1], 32, 32)
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
        return dx * dx + dy * dy <= self.interaction_radius * self.interaction_radius

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


class PnjPanelUI:
    """Class parent pour MenuInteractionUI, DialogueUI, BoutiqueUI et QueteUI"""

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):
        self.screen = screen
        self.largeur = largeur
        self.hauteur = hauteur

        self.pnj: PNJ | None = None

        self.x = 25
        self.y = self.hauteur - 190
        self.larg = self.largeur - 50
        self.haut = 160

        # police d'écriture
        self.font_titre = pygame.font.SysFont("dejavusans", 18, bold=True)
        self.font_corps = pygame.font.SysFont("dejavusans", 16)
        self.font_sub = pygame.font.SysFont("dejavusans", 14)
        self.font_hint = pygame.font.SysFont("dejavusans", 13)

    def draw_panel(self, rect: pygame.Rect):
        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 10, 22, 200), bg.get_rect(), border_radius=10)
        pygame.draw.rect(
            bg, (75, 75, 120, 255), bg.get_rect(), width=2, border_radius=10
        )
        self.screen.blit(bg, rect.topleft)

    def draw_portrait(self, pnj: "PNJ", panel_rect: pygame.Rect):
        p_rect = pygame.Rect(
            panel_rect.x + 12, panel_rect.y + 12, 90, panel_rect.height - 24
        )
        pygame.draw.rect(self.screen, (22, 22, 40), p_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 70, 110), p_rect, width=2, border_radius=6)
        portrait = pygame.transform.scale(
            pnj.sprite, (p_rect.width - 10, p_rect.height - 10)
        )
        self.screen.blit(portrait, (p_rect.x + 5, p_rect.y + 5))


class MenuInteractionUI(PnjPanelUI):
    """
    Affiche le menu d'interaction (Parler, Optionnel(Quête ou Échanger), Quitter).
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):

        super().__init__(screen, largeur, hauteur)

        self.options = []

    def set_screen(self, screen: pygame.Surface, larg, haut):
        self.screen = screen
        self.largeur, self.hauteur = larg, haut

        self.y = self.hauteur - 190
        self.larg = self.largeur - 50

        self.btn_rects = [
            pygame.Rect(136 + i * 162, self.y + 45, 150, 36)
            for i in range(len(self.options))
        ]

    def open(self, pnj: PNJ):
        self.pnj = pnj
        self.options = ["Parler"]
        if pnj.pnj_type == "Merchant":
            self.options.append("Échanger")
        elif pnj.pnj_type == "Quest" and pnj.quest_etat != "terminee":
            self.options.append("Quête")
        elif pnj.pnj_type == "Upgrade":
            self.options.append("Ameliorer")
        self.options.append("Quitter")

        # crée la liste des rects
        self.btn_rects = [
            pygame.Rect(136 + i * 162, self.y + 45, 150, 36)
            for i in range(len(self.options))
        ]

    def handle_event(self, event: pygame.event.Event, mouse_pos) -> str | None:
        """Renvoie None si rien de nouveau sinon soit Parler, Quête, Échanger ou Quitter"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pnj = None
            return "Quitter"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(self.options)):
                if self.btn_rects[i].collidepoint(mouse_pos):
                    EFFECT["menu"].play()
                    self.pnj = None
                    return self.options[i]
        return None

    def draw(self, mouse_pos):

        # Background
        self.draw_panel(pygame.Rect(self.x, self.y, self.larg, self.haut))

        # Portrait
        self.draw_portrait(self.pnj, pygame.Rect(self.x, self.y, self.larg, self.haut))

        # Le nom du PNJ
        nom_s = self.font_titre.render(self.pnj.name, True, (230, 210, 160))
        self.screen.blit(nom_s, (136, self.y + 14))

        # Les boutons d'interactions
        for i in range(len(self.options)):
            option, btn = self.options[i], self.btn_rects[i]
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

            text = self.font_corps.render(option, True, (240, 240, 255))
            self.screen.blit(
                text,
                (
                    btn.x + (btn.width - text.get_width()) // 2,
                    btn.y + (btn.height - text.get_height()) // 2,
                ),
            )


class DialogueUI(PnjPanelUI):
    """
    Affiche les dialogues d'un PNJ dialogue par dialogue avec effet machine à écrire.
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):

        super().__init__(screen, largeur, hauteur)

        self.list_dialogue: list[str] = []
        self.dialogue = 0
        self.caractere = 0
        self.timer = 0.0
        self.done = False  # True quand le dialogue a été entièrement affichée
        self.char_delay = 28  # le délai en ms entre chaque caractère

    def set_screen(self, screen: pygame.Surface, larg, haut):
        self.screen = screen
        self.largeur, self.hauteur = larg, haut

        self.y = self.hauteur - 190
        self.larg = self.largeur - 50

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
            EFFECT["menu"].play()
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
        self.draw_panel(pygame.Rect(self.x, self.y, self.larg, self.haut))

        # Portrait
        self.draw_portrait(self.pnj, pygame.Rect(self.x, self.y, self.larg, self.haut))

        # Le nom du PNJ
        nom_s = self.font_titre.render(self.pnj.name, True, (230, 210, 160))
        self.screen.blit(nom_s, (136, self.y + 14))

        # Le texte
        y_offset = self.y + 42
        for elt in wrap_text(
            self.list_dialogue[self.dialogue][: self.caractere],
            self.font_corps,
            self.larg - 102,
        ):
            surf = self.font_corps.render(elt, True, (210, 210, 222))
            self.screen.blit(surf, (137, y_offset))
            y_offset += surf.get_height() + 2

        # Numéro de dialogue
        dialogue_s = self.font_corps.render(
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

            hs = self.font_corps.render(hint, True, (130, 200, 130))
            self.screen.blit(
                hs,
                (
                    self.x + self.larg - hs.get_width() - dialogue_s.get_width() - 26,
                    self.y + self.haut - hs.get_height() - 8,
                ),
            )


class BoutiqueUI(PnjPanelUI):
    """
    Affiche la boutique d'échange du jeu.
    """

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):

        super().__init__(screen, largeur, hauteur)

        self.inv_joueur: Inventaire | None = None
        self.money = 0

        self.ui_stock: InventaireUI | None = None
        self.ui_joueur: InventaireUI | None = None

        self.msg_text = ""
        self.msg_color = (130, 220, 100)
        self.msg_timer = 0.0
        self.msg_duration = 2500.0

        self.larg_inv = 486  # la largeur en pixels d'une grille d'inventaire complète
        self.rect = pygame.Rect(self.x, self.y - 240, self.larg, 400)
        self.position_inv_x = self.larg // 2 - self.larg_inv + self.x // 2
        self.position_inv_y = self.rect.y + 55

        self.btn_hovered = False
        # rect du bouton fermer de la boutique
        self.btn = pygame.Rect(
            self.rect.x + self.rect.width // 2 - 75,
            self.rect.y + self.rect.height - 44,
            150,
            34,
        )

    def set_screen(self, screen: pygame.Surface, larg, haut):
        self.screen = screen
        self.largeur, self.hauteur = larg, haut

        self.y = self.hauteur - 190
        self.larg = self.largeur - 50

        self.rect = pygame.Rect(self.x, self.y - 240, self.larg, 400)
        self.position_inv_x = self.larg // 2 - self.larg_inv + self.x // 2
        self.position_inv_y = self.rect.y + 55

        self.btn = pygame.Rect(
            self.rect.x + self.rect.width // 2 - 75,
            self.rect.y + self.rect.height - 44,
            150,
            34,
        )

        if self.ui_joueur != None:
            self.ui_joueur.pos = (self.position_inv_x - 10, self.position_inv_y)

        if self.ui_stock != None:
            self.ui_stock.pos = (
                self.position_inv_x + self.larg_inv + 30,
                self.position_inv_y,
            )

    def open(self, pnj: PNJ, inv_joueur: Inventaire, money: int):
        self.pnj = pnj
        self.inv_joueur = inv_joueur
        self.money = money

        self.ui_joueur = InventaireUI(
            self.screen,
            name="Votre sac",
            inv=inv_joueur,
            pos=(self.position_inv_x - 10, self.position_inv_y),
            is_merchant=False,
            is_visible=True,
        )

        self.ui_stock = InventaireUI(
            self.screen,
            name=f"Stock — {pnj.name}",
            inv=pnj.stock,
            pos=(self.position_inv_x + self.larg_inv + 30, self.position_inv_y),
            is_merchant=True,
            is_visible=True,
        )

    def print_temporary_msg(self, text: str, color: tuple = (130, 220, 100)):
        self.msg_text = text
        self.msg_timer = self.msg_duration
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
            EFFECT["menu"].play()
            self.btn_hovered = False
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_hovered:
                EFFECT["menu"].play()
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
        if self.msg_timer > 0:
            self.msg_timer -= dt

    def draw(self, mouse_pos: tuple):

        # Background
        self.draw_panel(pygame.Rect(self.x, self.rect.y, self.larg, self.rect.height))

        # Nom de la boutique en haut à gauche
        self.screen.blit(
            self.font_titre.render(
                f"Boutique — {self.pnj.name}", True, (230, 210, 160)
            ),
            (self.rect.x + 20, self.rect.y + 14),
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
        hint_y = self.rect.y + 37
        self.screen.blit(hint_v, (joueur_center - hint_v.get_width() // 2, hint_y))
        self.screen.blit(hint_a, (stock_center - hint_a.get_width() // 2, hint_y))

        # Ligne séparatrice verticale entre les deux grilles
        sep_x = self.ui_joueur.pos[0] + self.larg_inv + 20 // 2 + 10
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
        coins = self.font_sub.render(f"Mole_Coins : {self.money}", True, (255, 215, 0))
        self.screen.blit(
            coins,
            (
                self.rect.x + self.rect.width // 2 - coins.get_width() // 2,
                self.btn.y - coins.get_height() - 4,
            ),
        )

        # Message temporaire (achat/vente/erreur)
        if self.msg_timer > 0:
            msg = self.font_hint.render(self.msg_text, False, self.msg_color)
            msg.set_alpha(
                int(255 * min(1.0, self.msg_timer / (self.msg_duration * 0.4)))
            )
            self.screen.blit(
                msg,
                (
                    self.rect.x + self.rect.width // 2 - msg.get_width() // 2,
                    self.ui_joueur.pos[1] - msg.get_height() - 22,
                ),
            )


class UpgradeUI(PnjPanelUI):
    """Interface d'amélioration permanente — un seul upgrade, prix croissant."""

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):
        super().__init__(screen, largeur, hauteur)
        self.xp: int = 0
        self.max_pv_bonus: int = 0
        self.msg_text = ""
        self.msg_color = (130, 220, 100)
        self.msg_timer = 0.0
        self.msg_duration = 2500.0
        self.panel_hauteur = 225
        self.build_rects()

    def build_rects(self):
        self.rect = pygame.Rect(
            self.x,
            self.hauteur - self.panel_hauteur - 30,
            self.larg,
            self.panel_hauteur,
        )

        portrait_x = self.x + 10
        portrait_y = self.rect.y + 44 + 4
        portrait_h = self.rect.bottom - portrait_y
        self.portrait_rect = pygame.Rect(portrait_x, portrait_y, 105, portrait_h)

        buy_x = portrait_x + 105 + 10 * 2 + 2
        self.buy_rect = pygame.Rect(
            buy_x,
            self.rect.y + 58,
            self.rect.right - 20 - buy_x,
            68,
        )

        cx = self.rect.x + self.rect.width // 2
        btn_y = self.rect.y + self.panel_hauteur - 48
        self.btn_close = pygame.Rect(cx - 75, btn_y, 150, 34)

    def set_screen(self, screen: pygame.Surface, larg, haut):
        self.screen = screen
        self.largeur, self.hauteur = larg, haut
        self.larg = self.largeur - 50
        self.build_rects()

    def upgrade_cost(self, n):
        """Coût du (n+1)-ième PV Max.
        n=0:10  n=1:50  n=2:120  n=3:220  n=4:350  n=5:510  n=6:700 ..."""
        return 10 + n * 40 + n * (n - 1) * 15

    def open(self, pnj: PNJ, xp: int, max_pv_bonus: int):
        self.pnj = pnj
        self.xp = xp
        self.max_pv_bonus = max_pv_bonus
        self.msg_timer = 0.0

    def print_msg(self, text: str, color=(130, 220, 100)):
        self.msg_text = text
        self.msg_timer = self.msg_duration
        self.msg_color = color

    def buy(self):
        cost = self.upgrade_cost(self.max_pv_bonus)
        if self.xp < cost:
            self.print_msg("Pas assez d'XP !", (220, 80, 80))
            return
        self.xp -= cost
        self.max_pv_bonus += 1
        self.print_msg(
            f"PV Max augmente ! (total : +{self.max_pv_bonus})", (130, 220, 100)
        )

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple) -> bool:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_ESCAPE):
            EFFECT["menu"].play()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.collidepoint(mouse_pos):
                EFFECT["menu"].play()
                return True
            if self.buy_rect.collidepoint(mouse_pos):
                EFFECT["menu"].play()
                self.buy()
        return False

    def update(self, dt: float):
        if self.msg_timer > 0:
            self.msg_timer -= dt

    def draw(self, mouse_pos: tuple):
        cost = self.upgrade_cost(self.max_pv_bonus)
        can_afford = self.xp >= cost
        close_hovered = self.btn_close.collidepoint(mouse_pos)
        row_hovered = self.buy_rect.collidepoint(mouse_pos)

        # Panel
        self.draw_panel(pygame.Rect(self.x, self.rect.y, self.larg, self.rect.height))

        # Portrait PNJ
        if self.pnj:
            self.draw_portrait(self.pnj, self.portrait_rect)

        # Titre
        title = self.font_titre.render(
            "Boutique d'amélioration permanente", True, (230, 210, 160)
        )
        self.screen.blit(title, (self.x + 15, self.rect.y + 12))

        # XP + bonus de PV
        xp_s = self.font_sub.render(f"XP : {self.xp}", True, (255, 215, 0))
        bonus_s = self.font_hint.render(
            f"PV Max bonus : +{self.max_pv_bonus}", True, (100, 220, 100)
        )
        self.screen.blit(xp_s, (self.rect.right - 80, self.rect.y + 8))
        self.screen.blit(
            bonus_s,
            (
                self.rect.right - 135,
                self.rect.y + 25,
            ),
        )

        # Séparateur horizontal
        pygame.draw.line(
            self.screen,
            (55, 55, 95),
            (self.x + 10, self.rect.y + 44),
            (self.rect.right - 20, self.rect.y + 44),
        )

        # Séparateur vertical
        vert_x = self.portrait_rect.right + 10
        pygame.draw.line(
            self.screen,
            (55, 55, 95),
            (vert_x, self.rect.y + 44),
            (vert_x, self.rect.bottom - 10),
        )

        # Ligne d'upgrade cliquable
        r = self.buy_rect
        hov_col_bg = (55, 85, 155, 220) if can_afford else (80, 40, 40, 220)
        hov_col_brd = (120, 150, 225, 255) if can_afford else (160, 80, 80, 255)
        col_bg = hov_col_bg if row_hovered else (22, 22, 44, 180)
        col_brd = hov_col_brd if row_hovered else (50, 50, 90, 200)

        bg = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, col_bg, (0, 0, r.width, r.height), border_radius=7)
        pygame.draw.rect(
            bg, col_brd, (0, 0, r.width, r.height), width=2, border_radius=7
        )
        self.screen.blit(bg, r.topleft)

        label_s = self.font_corps.render("PV Max +1", True, (230, 230, 255))
        next_cost_s = self.font_hint.render(
            f"Prochain achat : {self.upgrade_cost(self.max_pv_bonus + 1)} XP",
            True,
            (130, 130, 170),
        )
        hint_s = self.font_hint.render(
            "Cliquer pour acheter" if can_afford else "Pas assez d'XP",
            True,
            (160, 220, 160) if can_afford else (200, 100, 100),
        )
        self.screen.blit(label_s, (r.x + 12, r.y + 8))
        self.screen.blit(next_cost_s, (r.x + 12, r.y + 30))
        self.screen.blit(
            hint_s,
            (r.x + 12, r.y + 8 + label_s.get_height() + 22),
        )

        cost_col = (255, 215, 0) if can_afford else (180, 80, 80)
        cost_s = self.font_sub.render(f"{cost} XP", True, cost_col)
        self.screen.blit(
            cost_s,
            (
                r.right - cost_s.get_width() - 14,
                r.y + (r.height - 17) // 2,
            ),
        )

        # Bouton Fermer
        btn = self.btn_close
        col_bg = (55, 85, 155, 220) if close_hovered else (28, 28, 50, 200)
        col_brd = (120, 150, 225, 255) if close_hovered else (55, 55, 100, 255)
        bs = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
        pygame.draw.rect(bs, col_bg, (0, 0, btn.width, btn.height), border_radius=7)
        pygame.draw.rect(
            bs, col_brd, (0, 0, btn.width, btn.height), width=2, border_radius=7
        )
        self.screen.blit(bs, btn.topleft)
        ts = self.font_sub.render("Fermer", True, (240, 240, 255))
        self.screen.blit(
            ts,
            (
                btn.x + (btn.width - 52) // 2,
                btn.y + (btn.height - 17) // 2,
            ),
        )

        # Message temporaire
        if self.msg_timer > 0:
            msg = self.font_hint.render(self.msg_text, True, self.msg_color)
            msg.set_alpha(
                int(255 * min(1.0, self.msg_timer / (self.msg_duration * 0.4)))
            )
            self.screen.blit(
                msg,
                (
                    self.rect.x + self.rect.width // 2 - msg.get_width() // 2,
                    self.btn_close.y - msg.get_height() - 6,
                ),
            )


class QueteUI(PnjPanelUI):
    """Affiche la quête courante du PNJ avec ses objectifs et récompenses."""

    def __init__(self, screen: pygame.Surface, largeur: int, hauteur: int):

        super().__init__(screen, largeur, hauteur)

        self.inv_joueur: Inventaire | None = None
        self.money = 0

        self.msg_text = ""
        self.msg_color = (130, 220, 100)
        self.msg_timer = 0.0
        self.msg_duration = 2500.0

        self.msg_statut = {
            "disponible": ("Disponible", (180, 180, 80)),
            "active": ("En cours...", (80, 180, 220)),
            "complete": ("Prêt !", (80, 220, 80)),
            "terminee": ("Terminée !", (130, 130, 130)),
        }

        self.msg_action_btn = {
            "disponible": ("Accepter", True),
            "active": ("En cours...", False),
            "complete": ("Remettre les items !", True),
            "terminee": ("Terminée", False),
        }

        self.rect = pygame.Rect(
            self.x,
            self.y - 160,
            self.larg,
            320,
        )

        self.btn_action_hov = False
        self.btn_action = pygame.Rect(
            self.x + 20, self.rect.y + self.rect.height - 50, 190, 36
        )

        self.btn_fermer_hov = False
        self.btn_fermer = pygame.Rect(
            self.rect.right - 210, self.rect.y + self.rect.height - 50, 190, 36
        )

    def set_screen(self, screen: pygame.Surface, larg, haut):
        self.screen = screen
        self.largeur, self.hauteur = larg, haut

        self.y = self.hauteur - 190
        self.larg = self.largeur - 50

        self.rect = pygame.Rect(
            self.x,
            self.y - 160,
            self.larg,
            320,
        )
        self.btn_action = pygame.Rect(
            self.x + 20, self.rect.y + self.rect.height - 50, 190, 36
        )
        self.btn_fermer = pygame.Rect(
            self.rect.right - 210, self.rect.y + self.rect.height - 50, 190, 36
        )

    def open(self, pnj: PNJ, inv_joueur: Inventaire, money: int):
        self.pnj = pnj
        self.inv_joueur = inv_joueur
        self.money = money

        has_all = inv_joueur.has_items(pnj.quests[pnj.quest_index]["objectifs"])

        if pnj.quest_etat == "active" and has_all:
            pnj.quest_etat = "complete"
        elif pnj.quest_etat == "complete" and not has_all:
            pnj.quest_etat = "active"

    def print_temporary_msg(self, text: str, color: tuple = (130, 220, 100)):
        self.msg_text = text
        self.msg_timer = self.msg_duration
        self.msg_color = color

    def remettre_items(self):
        q = self.pnj.quests[self.pnj.quest_index]

        self.inv_joueur.remove_items(q["objectifs"])

        self.money += q["recompense_coins"]
        for r in q["recompense_items"]:
            self.inv_joueur.add_item(Item.create(r["item"], r["quantite"]))

        self.pnj.quest_etat = "terminee"
        self.print_temporary_msg("Récompense reçue !")

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple) -> bool:
        """Renvoie True si fermeture sinon False."""

        self.btn_action_hov = self.btn_action.collidepoint(mouse_pos)
        self.btn_fermer_hov = self.btn_fermer.collidepoint(mouse_pos)

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_ESCAPE):
            EFFECT["menu"].play()
            self.btn_fermer_hov = False
            self.btn_action_hov = False
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_fermer_hov:
                EFFECT["menu"].play()
                self.btn_fermer_hov = False
                self.btn_action_hov = False
                return True
            if self.btn_action_hov:
                EFFECT["menu"].play()
                if self.pnj.quest_etat == "disponible":
                    self.pnj.quest_etat = "active"
                    self.print_temporary_msg("Quête acceptée !")
                    if self.inv_joueur.has_items(
                        self.pnj.quests[self.pnj.quest_index]["objectifs"]
                    ):
                        self.pnj.quest_etat = "complete"
                elif self.pnj.quest_etat == "complete":
                    self.remettre_items()
        return False

    def update(self, dt: float):
        if self.msg_timer > 0:
            self.msg_timer -= dt

    def draw(self):

        # Background
        self.draw_panel(pygame.Rect(self.x, self.rect.y, self.larg, self.rect.height))

        q = self.pnj.quests[self.pnj.quest_index]

        # Titre centré + séparateur horizontal
        titre = self.font_titre.render(f"Quête — {q['titre']}", True, (230, 210, 160))
        self.screen.blit(
            titre,
            (
                self.rect.x + (self.rect.width - titre.get_width()) // 2,
                self.rect.y + 12,
            ),
        )
        pygame.draw.line(
            self.screen,
            (60, 60, 100),
            (self.rect.x + 20, self.rect.y + 36),
            (self.rect.right - 20, self.rect.y + 36),
        )

        # Numéro de quête en haut à gauche (si plusieurs)
        if len(self.pnj.quests) > 1:
            num_s = self.font_hint.render(
                f"Quête {self.pnj.quest_index + 1} / {len(self.pnj.quests)}",
                True,
                (120, 120, 160),
            )
            self.screen.blit(num_s, (self.rect.x + 20, self.rect.y + 14))

        # Statut en haut à droite
        lbl_etat, col_etat = self.msg_statut[self.pnj.quest_etat]
        etat_s = self.font_hint.render(f"Statut : {lbl_etat}", True, col_etat)
        self.screen.blit(
            etat_s, (self.rect.right - etat_s.get_width() - 14, self.rect.y + 14)
        )

        ty = self.rect.y + 46

        # Description wrappée
        for line in wrap_text(q["description"], self.font_sub, self.larg - 32):
            ls = self.font_sub.render(line, True, (200, 200, 215))
            self.screen.blit(ls, (self.x + 25, ty))
            ty += ls.get_height() + 3
        ty += 8

        # Objectifs
        self.screen.blit(
            self.font_sub.render("Objectifs :", True, (180, 160, 120)),
            (self.x + 25, ty),
        )
        ty += self.font_sub.get_height() + 4
        for obj in q["objectifs"]:
            possede = self.inv_joueur.count_item(obj["item"])
            rempli = possede >= obj["quantite"]
            col = (100, 220, 100) if rempli else (220, 100, 100)
            ls = self.font_sub.render(
                f"  {'   ✓' if rempli else '   ✗'}  {obj['item']} : {possede} / {obj['quantite']}",
                True,
                col,
            )
            self.screen.blit(ls, (self.x + 25, ty))
            ty += ls.get_height() + 3
        ty += 8

        # Récompenses
        self.screen.blit(
            self.font_sub.render("Récompenses :", True, (180, 160, 120)),
            (self.x + 25, ty),
        )
        ty += self.font_sub.get_height() + 4

        if q["recompense_coins"] > 0:
            coins_s = self.font_sub.render(
                f"    +{q['recompense_coins']} Mole_Coins", True, (255, 215, 0)
            )
            self.screen.blit(coins_s, (self.x + 25, ty))
            ty += coins_s.get_height() + 3

        for ri in q["recompense_items"]:
            ri_s = self.font_sub.render(
                f"    {ri['quantite']}× {ri['item']}", True, (160, 220, 160)
            )
            self.screen.blit(ri_s, (self.x + 25, ty))
            ty += ri_s.get_height() + 3

        # Boutons action + fermer
        a_lbl, a_en = self.msg_action_btn[self.pnj.quest_etat]
        for btn, label, enabled, hovered in (
            (self.btn_action, a_lbl, a_en, self.btn_action_hov and a_en),
            (self.btn_fermer, "Fermer", True, self.btn_fermer_hov),
        ):
            col_bg = (60, 90, 160, 220) if hovered else (28, 28, 50, 200)
            col_brd = (130, 160, 230, 255) if hovered else (55, 55, 100, 255)
            col_txt = (240, 240, 255) if enabled else (100, 100, 130)

            bs = pygame.Surface((btn.width, btn.height), pygame.SRCALPHA)
            pygame.draw.rect(bs, col_bg, (0, 0, btn.width, btn.height), border_radius=7)
            pygame.draw.rect(
                bs, col_brd, (0, 0, btn.width, btn.height), width=2, border_radius=7
            )
            self.screen.blit(bs, (btn.x, btn.y))

            ts = self.font_sub.render(label, True, col_txt)
            self.screen.blit(
                ts,
                (
                    btn.x + (btn.width - ts.get_width()) // 2,
                    btn.y + (btn.height - ts.get_height()) // 2,
                ),
            )

        # Message temporaire
        if self.msg_timer > 0:
            msg = self.font_sub.render(self.msg_text, True, self.msg_color)
            msg.set_alpha(
                int(255 * min(1.0, self.msg_timer / (self.msg_duration * 0.4)))
            )
            self.screen.blit(
                msg,
                (
                    self.rect.x + self.rect.width // 2 - msg.get_width() // 2,
                    self.btn_action.y - msg.get_height() - 8,
                ),
            )


class PNJManager:
    """
    La Class PNJManager pour la gestion des PNJ en jeu.
    """

    def __init__(self, screen: pygame.Surface, camera):
        self.screen = screen
        self.largeur, self.hauteur = self.screen.get_size()
        self.camera = camera

        self.pnjs: list[PNJ] = []

        self.menu_ui = MenuInteractionUI(screen, self.largeur, self.hauteur)
        self.dialogue_ui = DialogueUI(screen, self.largeur, self.hauteur)
        self.boutique_ui = BoutiqueUI(screen, self.largeur, self.hauteur)
        self.quete_ui = QueteUI(screen, self.largeur, self.hauteur)
        self.upgrade_ui = UpgradeUI(screen, self.largeur, self.hauteur)

        self.inv_joueur: Inventaire | None = None
        self.money: int = 0

        # Mode courant : None | "menu" | "dialogue" | "boutique" | "quete"
        self.mode: str | None = None
        self.pnj_actif: PNJ | None = None
        self.neary_pnj: PNJ | None = None

        # crée une surface pour mettre sur le screen plus tard : [E]
        self.e_bubble_text = pygame.font.SysFont("trebuchetms", 14, bold=True).render(
            "[E]", True, (240, 220, 170)
        )
        self.surface_bubble = pygame.Surface((25, 25), pygame.SRCALPHA)
        pygame.draw.rect(
            self.surface_bubble, (18, 18, 32, 180), (0, 0, 25, 25), border_radius=5
        )
        pygame.draw.rect(
            self.surface_bubble, (170, 170, 218, 255), (0, 0, 25, 25), 1, 5
        )
        self.surface_bubble.blit(self.e_bubble_text, (3, 3))

        self.permanent_xp: int = 0
        self.permanent_max_pv_bonus: int = 0

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen
        self.largeur, self.hauteur = self.screen.get_size()

        self.menu_ui.set_screen(screen, self.largeur, self.hauteur)

        self.dialogue_ui.set_screen(screen, self.largeur, self.hauteur)

        self.boutique_ui.set_screen(screen, self.largeur, self.hauteur)

        self.quete_ui.set_screen(screen, self.largeur, self.hauteur)

        self.upgrade_ui.set_screen(screen, self.largeur, self.hauteur)

    def set_xp_data(self, permanent_xp: int, permanent_max_pv_bonus: int):
        self.permanent_xp = permanent_xp
        self.permanent_max_pv_bonus = permanent_max_pv_bonus

    def add(self, pnj: PNJ):
        self.pnjs.append(pnj)

    def remove(self, pnj: PNJ):
        self.pnjs.remove(pnj)

    def set_inventaire(self, inv_joueur: Inventaire, money: int):
        """money : int — montant de la monnaie du joueur."""
        self.inv_joueur = inv_joueur
        self.money = money

    def handle_event(self, event: pygame.event.Event, mouse_pos: tuple) -> bool:
        """Retourne True si l'event a été consommé par un UI PNJ."""
        match self.mode:
            case "menu":
                action = self.menu_ui.handle_event(event, mouse_pos)
                if action is None:
                    return True
                if action == "Parler":
                    self.mode = "dialogue"
                    self.dialogue_ui.open(self.pnj_actif)
                elif action == "Échanger":
                    self.mode = "boutique"
                    self.boutique_ui.open(self.pnj_actif, self.inv_joueur, self.money)
                elif action == "Quête":
                    self.mode = "quete"
                    self.quete_ui.open(self.pnj_actif, self.inv_joueur, self.money)
                elif action == "Ameliorer":
                    self.mode = "amelioration"
                    self.upgrade_ui.open(
                        self.pnj_actif, self.permanent_xp, self.permanent_max_pv_bonus
                    )
                else:  # action == "Quitter"
                    self.mode = None
                    self.pnj_actif = None

            case "dialogue":
                if self.dialogue_ui.handle_event(event):
                    self.mode = None
                    self.pnj_actif = None
                return True

            case "boutique":
                if self.boutique_ui.handle_event(event, mouse_pos):
                    self.money = self.boutique_ui.money
                    self.mode = None
                    self.pnj_actif = None
                return True

            case "quete":
                if self.quete_ui.handle_event(event, mouse_pos):
                    self.money = self.quete_ui.money
                    self.mode = None
                    self.pnj_actif = None
                return True

            case "amelioration":
                if self.upgrade_ui.handle_event(event, mouse_pos):
                    self.permanent_xp = self.upgrade_ui.xp
                    self.permanent_max_pv_bonus = self.upgrade_ui.max_pv_bonus
                    self.mode = None
                    self.pnj_actif = None
                return True

        # Aucun UI ouvert : [E] déclenche l'interaction avec le PNJ proche
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e and self.neary_pnj:
            pnj = self.neary_pnj

            # Si la quête précédente est terminée, passe à la suivante
            if pnj.pnj_type == "Quest" and pnj.quest_etat == "terminee":
                if pnj.quest_index + 1 < len(pnj.quests):
                    pnj.quest_index += 1
                    pnj.quest_etat = "disponible"

            self.pnj_actif = pnj
            self.mode = "menu"
            self.menu_ui.open(pnj)

            return True

        return False

    def update(self, player_pos: tuple, dt: float):
        # Mise à jour du timer de l'UI active
        match self.mode:
            case "dialogue":
                self.dialogue_ui.update(dt)
            case "boutique":
                self.boutique_ui.update(dt)
            case "quete":
                self.quete_ui.update(dt)
            case "amelioration":
                self.upgrade_ui.update(dt)

        # Animation de tous les PNJ
        ANIM_RADIUS_SQ = 500**2
        px, py = player_pos
        for pnj in self.pnjs:
            dx = pnj.pos[0] - px
            dy = pnj.pos[1] - py
            if dx * dx + dy * dy <= ANIM_RADIUS_SQ:
                pnj.update()

        # Détecte le PNJ le plus proche
        if self.mode is None:
            self.neary_pnj = next((p for p in self.pnjs if p.is_near(player_pos)), None)

    def draw_pnj(self, pnj):
        """Dessine le PNJ"""
        screen_hitbox = self.camera.apply(pnj.hitbox)
        self.screen.blit(pnj.sprite, (screen_hitbox.centerx - 50, screen_hitbox.y - 50))

    def draw_pnj_bubble(self):
        """Dessine uniquement la bulle [E] au-dessus du PNJ proche."""
        screen_rect = pygame.Rect(0, 0, self.largeur, self.hauteur)
        for pnj in self.pnjs:
            screen_hitbox = self.camera.apply(pnj.hitbox)
            if screen_rect.colliderect(screen_hitbox):
                if pnj is self.neary_pnj and self.mode is None:
                    self.screen.blit(
                        self.surface_bubble,
                        (
                            screen_hitbox.centerx - 13,
                            screen_hitbox.top
                            - 50
                            + math.sin(pygame.time.get_ticks() * 0.005) * 5,
                        ),
                    )

    def draw_ui(self, mouse_pos: tuple):
        """Dessine l'UI PNJ active par-dessus tout le reste."""
        match self.mode:
            case "menu":
                self.menu_ui.draw(mouse_pos)
            case "dialogue":
                self.dialogue_ui.draw()
            case "boutique":
                self.boutique_ui.draw(mouse_pos)
            case "quete":
                self.quete_ui.draw()
            case "amelioration":
                self.upgrade_ui.draw(mouse_pos)


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
