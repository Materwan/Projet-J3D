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
        "image_path": "Ressources/pnj/old_mole/",
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
        "image_path": "Ressources/pnj/old_mole/",
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
        "image_path": "Ressources/pnj/old_mole/",
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
        "image_path": "Ressources/pnj/old_mole/",
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
        "image_path": "Ressources/pnj/old_mole/",
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
        Ressources/pnj/<...>/sprite_0, sprite_1, ..., sprite_4

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
            for i in range(5):
                image = pygame.image.load(
                    data["image_path"] + f"sprite_{i}.png"
                ).convert_alpha()
                frames.append(pygame.transform.scale(image, (100, 100)))
        except (FileNotFoundError, pygame.error):
            print(
                f"\nUne ou plusieurs images de '{name}' introuvable : '{data['image_path']}'.\n"
            )
            frames = [pygame.image.load("Ressources/pnj/not_found.png").convert_alpha()]

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

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.pnj: PNJ | None = None
        self.options = []

        self.font_nom = pygame.font.SysFont("segoeui", 14, bold=True)
        self.font_btn = pygame.font.SysFont("segoeui", 13)
        self.font_hint = pygame.font.SysFont("segoeui", 11)

        largeur, hauteur = self.screen.get_size()
        self.x = 22
        self.y = hauteur - 172
        self.larg = largeur - 44
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

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
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

        w, h = self.screen.get_size()
        self.x = 22
        self.y = h - 172
        self.larg = w - 44
        self.haut = 150
        self.larg_max = self.larg - (136 - self.x) - 12

    def open(self, pnj: PNJ):
        self.pnj = pnj
        self.list_dialogue = pnj.get_current_dialogue()
        self.dialogue = 0
        self.caractere = 0
        self.timer = 0.0
        self.done = False

    def update(self, dt):
        self.timer += dt
        while self.timer >= self.char_delay:
            self.timer -= self.char_delay
            self.caractere += 1
            if self.caractere >= len(self.list_dialogue[self.dialogue]):
                self.done = True

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
            self.larg_max,
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
