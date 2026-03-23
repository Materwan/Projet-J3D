import pygame
from inventory import Item, Inventaire, InventaireUI, InventaireManager

"""
pnj_dic c'est la base de données des PNJ du jeu
Chaque PNJ a :
  - pnj_type           : "Basic", "Merchant" ou "Quest"
  - image_path         : chemin vers l'image depuis le dossier Ressources
  - dialogues          : liste de dialogues (affiché quand on clique "Parler" sans quête active)
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
