import pygame
from typing import Tuple, List, Dict
import os

# On trouve le dossier où se trouve ton script actuel (Projet-J3D)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
# On remonte d'un cran pour aller dans "MoleTale", là où est le dossier Ressources
ROOT_PATH = os.path.dirname(BASE_PATH)


def load_image(
    relative_path: str, size: tuple | list | None = None
) -> pygame.surface.Surface:
    # Construction du chemin complet vers l'image demandée
    full_path = os.path.join(ROOT_PATH, relative_path)

    # Chemin vers ta texture de secours
    fallback_path = os.path.join(ROOT_PATH, "Ressources", "inv_assets", "not_found.png")

    if os.path.exists(full_path):
        image = pygame.image.load(full_path).convert_alpha()
    else:
        print(f"Image introuvable: {full_path}. Chargement de not_found.png")
        # Si même not_found.png n'est pas là, on crée un carré rose par défaut
        if os.path.exists(fallback_path):
            image = pygame.image.load(fallback_path).convert_alpha()
        else:
            image = pygame.Surface((32, 32))
            image.fill((255, 0, 255))  # Rose flash

    # Redimensionnement si besoin
    if size is not None:
        image = pygame.transform.scale(image, size)

    return image


class Item:
    """Représente un item avec toutes ses propriétés."""

    def __init__(
        self,
        name: str,
        description: str,
        item_type: str,
        max_stack: int,
        quantity: int,
        icon: pygame.Surface,
    ):
        self.name = name
        self.description = description
        self.item_type = item_type
        self.max_stack = max_stack
        self.quantity = quantity
        self.icon = icon

    def can_stack_with(self, item) -> bool:
        return self.name == item.name and self.quantity < self.max_stack


# --- BASE DE DONNÉES DES ITEMS ---
item_dic: dict[str, dict] = {
    # === ÉQUIPEMENT (Armes, Armures, Outils, Sacs) ===
    "Épée en fer": {
        "description": "Une épée solide forgée dans du bon métal.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Iron Sword.png",
    },
    "Armure en fer": {
        "description": "Une protection lourde et efficace contre les coups.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Iron Armor.png",
    },
    "Bouclier en fer": {
        "description": "Un bouclier robuste arborant une croix gravée.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Iron Shield.png",
    },
    "Casque en fer": {
        "description": "Protège la tête tout en laissant une bonne visibilité.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Iron Helmet.png",
    },
    "Bottes en fer": {
        "description": "Lourdes mais indispensables pour une protection complète.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Iron Boot.png",
    },
    "Armure en cuir": {
        "description": "Légère et souple, idéale pour les rôdeurs.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Leather Armor.png",
    },
    "Chapeau de sorcier": {
        "description": "Un chapeau pointu imprégné d'une légère aura magique.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Wizard Hat.png",
    },
    "Sac": {
        "description": "Un vieux sac en cuir pour transporter plus de butin.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/armor/Bag.png",
    },
    "Hache": {
        "description": "Idéale pour couper du bois ou fendre des crânes.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Axe.png",
    },
    "Arc": {
        "description": "Un arc en bois courbé, fiable à longue distance.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Bow.png",
    },
    "Bâton d'Émeraude": {
        "description": "Un bâton magique canalisant l'énergie de la nature.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Emerald Staff.png",
    },
    "Épée Dorée": {
        "description": "Aussi brillante que fragile, mais très tranchante.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Golden Sword.png",
    },
    "Marteau": {
        "description": "Un lourd marteau de forge ou de combat.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Hammer.png",
    },
    "Couteau": {
        "description": "Petit, discret et mortel.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Knife.png",
    },
    "Baguette Magique": {
        "description": "Une petite baguette pour lancer des sorts mineurs.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Magic Wand.png",
    },
    "Pioche": {
        "description": "L'outil indispensable de tout mineur.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Pickaxe.png",
    },
    "Bâton de Rubis": {
        "description": "Canalise le pouvoir destructeur du feu.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Ruby Staff.png",
    },
    "Bâton de Saphir": {
        "description": "Un bâton imprégné du pouvoir de la glace.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Sapphire Staff.png",
    },
    "Pelle": {
        "description": "Utile pour creuser des trous ou déterrer des trésors.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Shovel.png",
    },
    "Épée en Argent": {
        "description": "Particulièrement efficace contre les créatures de la nuit.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Silver Sword.png",
    },
    "Bâton de Topaze": {
        "description": "Un bâton qui crépite d'énergie électrique.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Topaz Staff.png",
    },
    "Bouclier en Bois": {
        "description": "Léger, mais ne durera pas éternellement.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Wooden Shield.png",
    },
    "Bâton en Bois": {
        "description": "Une branche solide ramassée dans la forêt.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Wooden Staff.png",
    },
    "Épée en Bois": {
        "description": "Une épée d'entraînement pour les débutants.",
        "item_type": "Équipement",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/weapon_tool/Wooden Sword.png",
    },
    # === CONSOMMABLE (Nourriture, Boissons, Potions) ===
    "Pomme": {
        "description": "Une pomme rouge bien sucrée.",
        "item_type": "Consommable",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/food/Apple.png",
    },
    "Bière": {
        "description": "Une chope de bière fraîche avec beaucoup de mousse.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/food/Beer.png",
    },
    "Pain": {
        "description": "Un pain artisanal tout juste sorti du four.",
        "item_type": "Consommable",
        "max_stack": 15,
        "icon": "Ressources/inv_assets/food/Bread.png",
    },
    "Fromage": {
        "description": "Un morceau de fromage qui a du caractère.",
        "item_type": "Consommable",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/food/Cheese.png",
    },
    "Steak de poisson": {
        "description": "Un beau morceau de poisson grillé.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/food/Fish Steak.png",
    },
    "Pomme verte": {
        "description": "Légèrement acide mais très rafraîchissante.",
        "item_type": "Consommable",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/food/Green Apple.png",
    },
    "Jambon": {
        "description": "Un jambon entier bien cuit.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/food/Ham.png",
    },
    "Viande": {
        "description": "Un morceau de viande crue de qualité.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/food/Meat.png",
    },
    "Champignon": {
        "description": "Un petit champignon des bois comestible.",
        "item_type": "Consommable",
        "max_stack": 50,
        "icon": "Ressources/inv_assets/food/Mushroom.png",
    },
    "Vin rouge": {
        "description": "Une bouteille de grand cru.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/food/Wine 2.png",
    },
    "Vin blanc": {
        "description": "Un vin blanc sec et fruité.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/food/Wine.png",
    },
    "Petite Potion Bleue": {
        "description": "Une petite fiole d'énergie magique.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Blue Potion 2.png",
    },
    "Grande Potion Bleue": {
        "description": "Une grande bouteille de mana concentré.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/potion/Blue Potion 3.png",
    },
    "Potion Bleue": {
        "description": "Une potion standard pour restaurer la mana.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Blue Potion.png",
    },
    "Petite Potion Verte": {
        "description": "Une petite décoction aux herbes médicinales.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Green Potion 2.png",
    },
    "Grande Potion Verte": {
        "description": "Un puissant antidote ou tonique vert.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/potion/Green Potion 3.png",
    },
    "Potion Verte": {
        "description": "Une potion verte équilibrée.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Green Potion.png",
    },
    "Petite Potion Rouge": {
        "description": "Une petite fiole qui referme les plaies légères.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Red Potion 2.png",
    },
    "Grande Potion Rouge": {
        "description": "Un flacon de soin majeur, très efficace.",
        "item_type": "Consommable",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/potion/Red Potion 3.png",
    },
    "Potion Rouge": {
        "description": "La potion de soin classique des aventuriers.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/potion/Red Potion.png",
    },
    "Bouteille d'Eau": {
        "description": "De l'eau pure, base de toutes les potions.",
        "item_type": "Consommable",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/potion/Water Bottle.png",
    },
    # === MATÉRIAU (Crafting et Ressources) ===
    "Tissu": {
        "description": "Un rouleau de tissu blanc, utile pour la couture.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Fabric.png",
    },
    "Cuir": {
        "description": "Une peau tannée souple et résistante.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Leather.png",
    },
    "Papier": {
        "description": "Un parchemin vierge prêt à être écrit.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Paper.png",
    },
    "Corde": {
        "description": "Une corde solide faite de fibres tressées.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Rope.png",
    },
    "Ficelle": {
        "description": "Une bobine de fil résistant.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/String.png",
    },
    "Bûche": {
        "description": "Un morceau de bois brut fraîchement coupé.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Wood Log.png",
    },
    "Planche en bois": {
        "description": "Du bois taillé prêt pour la construction.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Wooden Plank.png",
    },
    "Laine": {
        "description": "Une boule de laine douce et chaude.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/material/Wool.png",
    },
    "Charbon": {
        "description": "Un morceau de charbon noir, utile pour le feu.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Coal.png",
    },
    "Lingot de cuivre": {
        "description": "Un lingot de cuivre pur prêt à être forgé.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Copper Ingot.png",
    },
    "Pépite de cuivre": {
        "description": "Un petit éclat de cuivre brut.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Copper Nugget.png",
    },
    "Pépite d'or": {
        "description": "Un petit morceau d'or pur.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Gold Nugget.png",
    },
    "Lingot d'or": {
        "description": "Un lingot d'or massif et brillant.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Golden Ingot.png",
    },
    "Obsidienne": {
        "description": "Une roche volcanique noire et tranchante.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Obsidian.png",
    },
    "Lingot d'argent": {
        "description": "Un lingot d'argent pur au reflet lunaire.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Silver Ingot.png",
    },
    "Pépite d'argent": {
        "description": "Un fragment d'argent brut.",
        "item_type": "Matériau",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Silver Nugget.png",
    },
    "Bouteille Vide": {
        "description": "Une fiole en verre vide, prête à être remplie.",
        "item_type": "Matériau",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/potion/Empty Bottle.png",
    },
    "Engrenage": {
        "description": "Une pièce mécanique complexe.",
        "item_type": "Matériau",
        "max_stack": 50,
        "icon": "Ressources/inv_assets/misc/Gear.png",
    },
    "Flèche": {
        "description": "Une flèche simple avec une pointe en silex.",
        "item_type": "Matériau",
        "max_stack": 50,
        "icon": "Ressources/inv_assets/weapon_tool/Arrow.png",
    },
    # === GEMME (Pierres précieuses) ===
    "Cristal": {
        "description": "Un cristal translucide qui reflète la lumière.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Crystal.png",
    },
    "Émeraude taillée": {
        "description": "Une émeraude d'un vert éclatant, taillée avec soin.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Cut Emerald.png",
    },
    "Rubis taillé": {
        "description": "Un rubis rouge sang parfaitement poli.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Cut Ruby.png",
    },
    "Saphir taillé": {
        "description": "Un saphir d'un bleu profond et pur.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Cut Sapphire.png",
    },
    "Topaze taillée": {
        "description": "Une topaze aux reflets ambrés.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Cut Topaz.png",
    },
    "Diamant": {
        "description": "La plus dure et la plus précieuse des gemmes.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Diamond.png",
    },
    "Émeraude": {
        "description": "Une émeraude brute extraite de la roche.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Emerald.png",
    },
    "Perle": {
        "description": "Une perle nacrée provenant des profondeurs.",
        "item_type": "Gemme",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/ore_gem/Pearl.png",
    },
    # === BUTIN (Pièces de monstres) ===
    "Os": {
        "description": "Un vieil os blanchi par le soleil.",
        "item_type": "Butin",
        "max_stack": 50,
        "icon": "Ressources/inv_assets/monster_part/Bone.png",
    },
    "Œuf": {
        "description": "Un œuf mystérieux, peut-être comestible ?",
        "item_type": "Butin",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/monster_part/Egg.png",
    },
    "Plume": {
        "description": "Une plume légère et résistante.",
        "item_type": "Butin",
        "max_stack": 50,
        "icon": "Ressources/inv_assets/monster_part/Feather.png",
    },
    "Œuf de monstre": {
        "description": "Un œuf orné de motifs étranges, il semble vibrer.",
        "item_type": "Butin",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/monster_part/Monster Egg.png",
    },
    "Œil de monstre": {
        "description": "Une pupille verticale qui semble encore vous fixer.",
        "item_type": "Butin",
        "max_stack": 30,
        "icon": "Ressources/inv_assets/monster_part/Monster Eye.png",
    },
    "Viande de monstre": {
        "description": "De la viande à l'odeur suspecte.",
        "item_type": "Butin",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/monster_part/Monster Meat.png",
    },
    "Crâne": {
        "description": "Un crâne qui pourrait servir de trophée.",
        "item_type": "Butin",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/monster_part/Skull.png",
    },
    "Gel de Slime": {
        "description": "Une substance gluante et verdâtre.",
        "item_type": "Butin",
        "max_stack": 99,
        "icon": "Ressources/inv_assets/monster_part/Slime Gel.png",
    },
    # === DIVERS (Monnaie, Quêtes, Conteneurs) ===
    "Pièce de cuivre": {
        "description": "La monnaie de base du royaume.",
        "item_type": "Divers",
        "max_stack": 999,
        "icon": "Ressources/inv_assets/misc/Copper Coin.png",
    },
    "Pièce d'or": {
        "description": "Une pièce brillante de grande valeur.",
        "item_type": "Divers",
        "max_stack": 999,
        "icon": "Ressources/inv_assets/misc/Golden Coin.png",
    },
    "Livre ancien": {
        "description": "Un livre relié en cuir aux pages jaunies.",
        "item_type": "Divers",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/misc/Book.png",
    },
    "Bougie": {
        "description": "Une simple bougie pour s'éclairer dans le noir.",
        "item_type": "Divers",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/misc/Candle.png",
    },
    "Coffre": {
        "description": "Un petit coffre en bois renforcé.",
        "item_type": "Divers",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/misc/Chest.png",
    },
    "Caisse": {
        "description": "Une caisse de transport en bois.",
        "item_type": "Divers",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/misc/Crate.png",
    },
    "Enveloppe": {
        "description": "Une lettre scellée. Qui en est le destinataire ?",
        "item_type": "Divers",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/misc/Envelop.png",
    },
    "Clé dorée": {
        "description": "Une clé ornée qui semble ouvrir un mécanisme précieux.",
        "item_type": "Divers",
        "max_stack": 1,
        "icon": "Ressources/inv_assets/misc/Golden Key.png",
    },
    "Clé en fer": {
        "description": "Une clé simple mais robuste.",
        "item_type": "Divers",
        "max_stack": 5,
        "icon": "Ressources/inv_assets/misc/Iron Key.png",
    },
    "Torche": {
        "description": "Elle éclaire les endroits les plus sombres.",
        "item_type": "Divers",
        "max_stack": 20,
        "icon": "Ressources/inv_assets/weapon_tool/Torch.png",
    },
    "Cœur": {
        "description": "Un réceptacle de vie qui pulse doucement.",
        "item_type": "Consommable",
        "max_stack": 10,
        "icon": "Ressources/inv_assets/misc/Heart.png",
    },
}


def create_item(name: str, quantity: int = 1) -> Item:
    """
    Crée un Item depuis la base de données.
    - Si le nom n'est pas dans le dictionnaire -> ERREUR (Raise)
    - Si l'image est introuvable -> Texture 'not_found'
    """
    if name not in item_dic:
        raise ValueError(f"Item inconnu : '{name}'. Vérifie item_dic dans ton code.")

    data = item_dic[name]
    qty = min(quantity, data["max_stack"])
    icon_surface = load_image(data["icon"], (32, 32))

    return Item(
        name=name,
        description=data["description"],
        item_type=data["item_type"],
        max_stack=data["max_stack"],
        quantity=qty,
        icon=icon_surface,
    )
