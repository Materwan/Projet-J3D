"""
Module du jeu de cartes — Boss Fight.

Intégration dans le Manager principal :
    - CardGame suit l'interface DefaultManager (event / update / display / set_screen)
    - Le Manager doit contenir l'état "CARD" pointant sur une instance de CardGame
    - Le déclenchement se fait depuis game.py via _boss_fight_start()
    - En fin de partie (victoire/défaite) CardGame appelle manager.end_card_game(result)

Ajouter dans main.py :
    "CARD": CardGame(screen, manager),

Ajouter dans game.py, méthode _boss_fight_start() :
    self.manager.states["CARD"].start(
        playing_mode=self.playing_mode,
        on_victory=self._on_card_victory,
        on_defeat=self._on_card_defeat,
    )
    self.manager.change_state("CARD")

Ajouter dans game.py les callbacks :
    def _on_card_victory(self):
        # Le boss est vaincu — passer au RecapScreen ou autre logique
        self.manager.states["RECAP"].start(self.run_stats)
        self.manager.change_state("RECAP")

    def _on_card_defeat(self):
        # Défaite au jeu de cartes — même logique que mort normale
        self.manager.states["RECAP"].start(self.run_stats)
        self.manager.change_state("RECAP")
"""

from __future__ import annotations

import math
import random
import time
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from main import Manager

# ---------------------------------------------------------------------------
# Constantes visuelles
# ---------------------------------------------------------------------------

CARD_W = 100
CARD_H = 140
CARD_RADIUS = 8

# Palette
COL_BG = (12, 10, 20)
COL_PANEL = (22, 18, 38)
COL_BORDER = (70, 55, 110)
COL_BORDER_HI = (160, 120, 220)
COL_GOLD = (255, 210, 60)
COL_RED = (220, 60, 60)
COL_GREEN = (60, 200, 100)
COL_BLUE = (60, 140, 230)
COL_WHITE = (240, 235, 255)
COL_GREY = (130, 120, 160)
COL_SPELL_BG = (30, 20, 55)
COL_EQUIP_BG = (20, 35, 25)
COL_BOSS_BG = (45, 10, 10)
COL_MANA = (60, 100, 220)
COL_HP_FULL = (60, 200, 100)
COL_HP_LOW = (220, 60, 60)

# ---------------------------------------------------------------------------
# Base de données des cartes
# ---------------------------------------------------------------------------

"""
Chaque entrée du catalogue :
    type     : "spell" | "equip"
    cost     : coût en mana
    desc     : description courte
    effect   : nom de la fonction d'effet (résolu à l'exécution)
    value    : paramètre numérique passé à l'effet
    color    : tuple RGB dominant pour le rendu
"""
CARD_CATALOGUE: Dict[str, Dict] = {
    # ── Sorts ────────────────────────────────────────────────────────────────
    "Boule de Feu": {
        "type": "spell",
        "cost": 2,
        "desc": "Inflige 3 dégâts au boss.",
        "effect": "damage_boss",
        "value": 3,
        "color": (200, 80, 30),
    },
    "Éclair": {
        "type": "spell",
        "cost": 3,
        "desc": "Inflige 5 dégâts au boss.",
        "effect": "damage_boss",
        "value": 5,
        "color": (180, 180, 60),
    },
    "Soin": {
        "type": "spell",
        "cost": 2,
        "desc": "Restaure 3 PV.",
        "effect": "heal_player",
        "value": 3,
        "color": (60, 200, 100),
    },
    "Grande Guérison": {
        "type": "spell",
        "cost": 4,
        "desc": "Restaure 6 PV.",
        "effect": "heal_player",
        "value": 6,
        "color": (60, 200, 100),
    },
    "Poison": {
        "type": "spell",
        "cost": 2,
        "desc": "Inflige 1 dégât/tour pendant 3 tours.",
        "effect": "apply_poison",
        "value": 3,
        "color": (100, 180, 60),
    },
    "Bouclier": {
        "type": "spell",
        "cost": 2,
        "desc": "Bloque les prochains 2 dégâts.",
        "effect": "give_shield",
        "value": 2,
        "color": (100, 140, 220),
    },
    "Double Frappe": {
        "type": "spell",
        "cost": 3,
        "desc": "Inflige 2 fois 2 dégâts.",
        "effect": "double_hit",
        "value": 2,
        "color": (200, 120, 30),
    },
    "Drain": {
        "type": "spell",
        "cost": 3,
        "desc": "Inflige 3 dégâts, soigne 2 PV.",
        "effect": "drain",
        "value": 3,
        "color": (140, 60, 180),
    },
    # ── Équipements ──────────────────────────────────────────────────────────
    "Épée Runique": {
        "type": "equip",
        "cost": 3,
        "desc": "+2 Att. permanents.",
        "effect": "boost_attack",
        "value": 2,
        "color": (180, 160, 60),
    },
    "Amulette de Vie": {
        "type": "equip",
        "cost": 3,
        "desc": "+4 PV max.",
        "effect": "boost_max_hp",
        "value": 4,
        "color": (200, 60, 80),
    },
    "Cristal de Mana": {
        "type": "equip",
        "cost": 2,
        "desc": "+2 Mana max.",
        "effect": "boost_max_mana",
        "value": 2,
        "color": (60, 100, 220),
    },
    "Bouclier de Fer": {
        "type": "equip",
        "cost": 2,
        "desc": "Réduit chaque attaque de 1.",
        "effect": "damage_reduction",
        "value": 1,
        "color": (140, 140, 160),
    },
}

# Deck de départ du joueur
PLAYER_START_DECK = [
    "Boule de Feu",
    "Boule de Feu",
    "Soin",
    "Soin",
    "Éclair",
    "Bouclier",
    "Bouclier",
    "Poison",
    "Double Frappe",
    "Drain",
    "Épée Runique",
    "Amulette de Vie",
]

# Deck du boss
BOSS_DECK = [
    "Boule de Feu",
    "Boule de Feu",
    "Boule de Feu",
    "Éclair",
    "Éclair",
    "Poison",
    "Poison",
    "Double Frappe",
    "Drain",
]

# ---------------------------------------------------------------------------
# Entité PlayerState / BossState
# ---------------------------------------------------------------------------


class CombatantState:
    """État d'un combattant (joueur ou boss)."""

    def __init__(self, hp: int, max_hp: int, mana: int, max_mana: int, attack: int):
        self.hp = hp
        self.max_hp = max_hp
        self.mana = mana
        self.max_mana = max_mana
        self.attack = attack
        # Effets persistants
        self.shield = 0  # points de bouclier absorbés avant les PV
        self.poison_turns = 0  # tours de poison restants
        self.dmg_reduction = 0  # réduction de dégâts par coup (équipement)

    def take_damage(self, amount: int) -> int:
        """Applique des dégâts en tenant compte du bouclier et de la réduction."""
        amount = max(0, amount - self.dmg_reduction)
        absorbed = min(self.shield, amount)
        self.shield -= absorbed
        amount -= absorbed
        self.hp = max(0, self.hp - amount)
        return absorbed + amount  # dégâts réels subis

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def start_turn_effects(self) -> List[str]:
        """Applique les effets de début de tour. Retourne un log."""
        log = []
        if self.poison_turns > 0:
            self.take_damage(1)
            self.poison_turns -= 1
            log.append("☠ Poison : -1 PV")
        return log

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0


# ---------------------------------------------------------------------------
# Carte (objet de jeu)
# ---------------------------------------------------------------------------


class Card:
    """Carte jouable."""

    def __init__(self, name: str):
        if name not in CARD_CATALOGUE:
            raise ValueError(f"Carte inconnue : '{name}'")
        self.name = name
        data = CARD_CATALOGUE[name]
        self.card_type: str = data["type"]  # "spell" | "equip"
        self.cost: int = data["cost"]
        self.desc: str = data["desc"]
        self.effect: str = data["effect"]
        self.value: int = data["value"]
        self.color: Tuple = data["color"]

    def __repr__(self):
        return f"<Card {self.name}>"


# ---------------------------------------------------------------------------
# Logique du combat
# ---------------------------------------------------------------------------


class CardBattle:
    """
    Moteur de jeu de cartes.

    Flux d'un tour :
        1. Le joueur pioche jusqu'à 5 cartes (ou autant que possible).
        2. Le joueur joue des cartes depuis sa main (dépense du mana).
        3. Le joueur termine son tour (end_turn()).
        4. Le boss joue automatiquement.
        5. Les effets de statut sont appliqués.
        6. On vérifie si quelqu'un est mort.
    """

    HAND_SIZE = 5
    PLAYER_HP = 20
    PLAYER_MANA = 3
    PLAYER_ATK = 1
    BOSS_HP = 30
    BOSS_MANA = 4
    BOSS_ATK = 2

    def __init__(self):
        self.player = CombatantState(
            self.PLAYER_HP,
            self.PLAYER_HP,
            self.PLAYER_MANA,
            self.PLAYER_MANA,
            self.PLAYER_ATK,
        )
        self.boss = CombatantState(
            self.BOSS_HP,
            self.BOSS_HP,
            self.BOSS_MANA,
            self.BOSS_MANA,
            self.BOSS_ATK,
        )

        # Decks, mains, défausses
        self.player_deck: List[Card] = [Card(n) for n in PLAYER_START_DECK]
        self.player_hand: List[Card] = []
        self.player_discard: List[Card] = []

        self.boss_deck: List[Card] = [Card(n) for n in BOSS_DECK]
        self.boss_hand: List[Card] = []
        self.boss_discard: List[Card] = []

        # Équipements actifs (slots permanents)
        self.player_equips: List[Card] = []
        self.boss_equips: List[Card] = []

        # Zone de sort du joueur (cartes jouées ce tour, avant résolution)
        self.player_spell_zone: List[Card] = []

        random.shuffle(self.player_deck)
        random.shuffle(self.boss_deck)

        # Log d'événements affiché à l'écran
        self.log: List[str] = []

        # Phase : "player_turn" | "boss_turn" | "victory" | "defeat"
        self.phase = "player_turn"
        self.turn = 1

        # Pioche initiale
        self._draw_player(self.HAND_SIZE)
        self._draw_boss(3)

        self._log(f"Tour 1 — À vous de jouer !")

    # ── Pioche ───────────────────────────────────────────────────────────────

    def _draw_player(self, n: int):
        for _ in range(n):
            if not self.player_deck:
                if not self.player_discard:
                    break
                self.player_deck = self.player_discard[:]
                self.player_discard.clear()
                random.shuffle(self.player_deck)
                self._log("🔄 Deck mélangé depuis la défausse.")
            self.player_hand.append(self.player_deck.pop())

    def _draw_boss(self, n: int):
        for _ in range(n):
            if not self.boss_deck:
                if not self.boss_discard:
                    break
                self.boss_deck = self.boss_discard[:]
                self.boss_discard.clear()
                random.shuffle(self.boss_deck)
            self.boss_hand.append(self.boss_deck.pop())

    # ── Effets des cartes ────────────────────────────────────────────────────

    def _apply_effect(
        self,
        card: Card,
        caster: CombatantState,
        target: CombatantState,
        equip_list: List[Card],
    ) -> str:
        """Résout l'effet d'une carte. Retourne un message de log."""
        e, v = card.effect, card.value

        if e == "damage_boss" or e == "damage_player":
            dmg = v + caster.attack - 1  # l'attaque de base ajoute un bonus
            actual = target.take_damage(dmg)
            return f"⚔ {card.name} → {actual} dégâts"

        elif e == "heal_player" or e == "heal_boss":
            caster.heal(v)
            return f"💚 {card.name} → +{v} PV"

        elif e == "apply_poison":
            target.poison_turns += v
            return f"☠ {card.name} → Poison {v} tours"

        elif e == "give_shield":
            caster.shield += v
            return f"🛡 {card.name} → Bouclier +{v}"

        elif e == "double_hit":
            total = 0
            for _ in range(2):
                total += target.take_damage(v)
            return f"⚔⚔ {card.name} → {total} dégâts"

        elif e == "drain":
            actual = target.take_damage(v)
            heal = max(1, actual - 1)
            caster.heal(heal)
            return f"🩸 {card.name} → {actual} dégâts, +{heal} PV"

        elif e == "boost_attack":
            caster.attack += v
            equip_list.append(card)
            return f"⚔ {card.name} → Att +{v} (permanent)"

        elif e == "boost_max_hp":
            caster.max_hp += v
            caster.hp += v
            equip_list.append(card)
            return f"❤ {card.name} → PV max +{v}"

        elif e == "boost_max_mana":
            caster.max_mana += v
            equip_list.append(card)
            return f"💧 {card.name} → Mana max +{v}"

        elif e == "damage_reduction":
            caster.dmg_reduction += v
            equip_list.append(card)
            return f"🛡 {card.name} → Réduction {v}/coup"

        return f"? {card.name} : effet inconnu"

    # ── Actions joueur ────────────────────────────────────────────────────────

    def can_play(self, card: Card) -> bool:
        return self.phase == "player_turn" and self.player.mana >= card.cost

    def play_card(self, index: int) -> bool:
        """Joue la carte à l'index `index` de la main. Retourne True si réussi."""
        if index < 0 or index >= len(self.player_hand):
            return False
        card = self.player_hand[index]
        if not self.can_play(card):
            return False

        self.player.mana -= card.cost
        self.player_hand.pop(index)

        msg = self._apply_effect(card, self.player, self.boss, self.player_equips)
        self._log(msg)

        # Les sorts vont à la défausse, les équipements restent en zone
        if card.card_type == "spell":
            self.player_discard.append(card)
        # equips : déjà ajoutés dans _apply_effect

        self._check_end()
        return True

    def end_turn(self):
        """Le joueur termine son tour."""
        if self.phase != "player_turn":
            return

        # Défausse la main restante
        self.player_discard.extend(self.player_hand)
        self.player_hand.clear()

        self.phase = "boss_turn"
        self._boss_turn()

    # ── Tour du boss ──────────────────────────────────────────────────────────

    def _boss_turn(self):
        """IA simple du boss."""
        self._log(f"— Tour {self.turn} — Le boss agit…")

        # Effets de statut du boss
        for msg in self.boss.start_turn_effects():
            self._log(msg)
        if self._check_end():
            return

        # Pioche
        nb_draw = min(2, self.HAND_SIZE - len(self.boss_hand))
        self._draw_boss(nb_draw)

        # Restaure le mana du boss
        self.boss.mana = self.boss.max_mana

        # Joue toutes les cartes qu'il peut, en priorisant les dégâts
        playable = sorted(
            [c for c in self.boss_hand if c.cost <= self.boss.mana],
            key=lambda c: -c.value,
        )
        for card in playable:
            if card.cost > self.boss.mana:
                continue
            self.boss.mana -= card.cost
            self.boss_hand.remove(card)
            msg = self._apply_effect(card, self.boss, self.player, self.boss_equips)
            self._log(f"🔴 Boss : {msg}")
            self.boss_discard.append(card)
            if self._check_end():
                return

        # Attaque de base si encore en vie
        if not self.player.is_dead:
            dmg = self.boss.attack
            actual = self.player.take_damage(dmg)
            self._log(f"🔴 Boss attaque : {actual} dégâts")
            if self._check_end():
                return

        # Début du tour suivant
        self.turn += 1

        # Effets de statut du joueur
        for msg in self.player.start_turn_effects():
            self._log(msg)
        if self._check_end():
            return

        # Restaure le mana du joueur
        self.player.mana = self.player.max_mana

        # Pioche pour le joueur
        cards_to_draw = self.HAND_SIZE - len(self.player_hand)
        self._draw_player(cards_to_draw)

        self.phase = "player_turn"
        self._log(f"— Tour {self.turn} — À vous de jouer !")

    # ── Fin de partie ─────────────────────────────────────────────────────────

    def _check_end(self) -> bool:
        if self.boss.is_dead:
            self.phase = "victory"
            self._log("🏆 VICTOIRE ! Le boss est vaincu.")
            return True
        if self.player.is_dead:
            self.phase = "defeat"
            self._log("💀 DÉFAITE. Vous avez succombé.")
            return True
        return False

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _log(self, msg: str):
        self.log.append(msg)
        if len(self.log) > 20:
            self.log.pop(0)


# ---------------------------------------------------------------------------
# Rendu d'une carte (surface pygame)
# ---------------------------------------------------------------------------


def render_card(
    card: Card,
    selected: bool = False,
    playable: bool = True,
    width: int = CARD_W,
    height: int = CARD_H,
) -> pygame.Surface:
    """Génère une surface pygame représentant une carte."""

    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    # Fond
    bg = COL_SPELL_BG if card.card_type == "spell" else COL_EQUIP_BG
    pygame.draw.rect(surf, bg, (0, 0, width, height), border_radius=CARD_RADIUS)

    # Dégradé de couleur dominant en haut
    top_col = card.color
    for y in range(height // 3):
        alpha = int(180 * (1 - y / (height / 3)))
        overlay = pygame.Surface((width, 1), pygame.SRCALPHA)
        overlay.fill((*top_col, alpha))
        surf.blit(overlay, (0, y))

    # Bordure
    border_col = COL_BORDER_HI if selected else (COL_GOLD if playable else COL_BORDER)
    border_w = 3 if selected else 2
    pygame.draw.rect(
        surf,
        border_col,
        (0, 0, width, height),
        width=border_w,
        border_radius=CARD_RADIUS,
    )

    # Icône type (⚡ sort, ⚔ équip)
    icon = "✨" if card.card_type == "spell" else "🔧"

    fnt_small = pygame.font.SysFont("dejavusans", 10, bold=True)
    fnt_name = pygame.font.SysFont("dejavusans", 11, bold=True)
    fnt_cost = pygame.font.SysFont("dejavusans", 14, bold=True)
    fnt_desc = pygame.font.SysFont("dejavusans", 10)

    # Coût (cercle en haut à droite)
    pygame.draw.circle(surf, COL_MANA, (width - 14, 14), 12)
    pygame.draw.circle(surf, COL_WHITE, (width - 14, 14), 12, 1)
    cost_surf = fnt_cost.render(str(card.cost), True, COL_WHITE)
    surf.blit(
        cost_surf,
        (width - 14 - cost_surf.get_width() // 2, 14 - cost_surf.get_height() // 2),
    )

    # Nom
    name_surf = fnt_name.render(card.name, True, COL_WHITE)
    # Tronquer si trop long
    if name_surf.get_width() > width - 8:
        name_surf = pygame.transform.scale(
            name_surf, (width - 8, name_surf.get_height())
        )
    surf.blit(name_surf, (4, 4))

    # Séparateur
    pygame.draw.line(surf, COL_BORDER, (4, 22), (width - 4, 22))

    # Zone artwork (rectangle stylisé)
    art_rect = pygame.Rect(6, 26, width - 12, 56)
    art_surf = pygame.Surface((art_rect.width, art_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(
        art_surf,
        (*top_col, 60),
        (0, 0, art_rect.width, art_rect.height),
        border_radius=4,
    )
    # Motif géométrique décoratif
    cx, cy = art_rect.width // 2, art_rect.height // 2
    for r in range(8, min(cx, cy), 8):
        alpha = max(20, 80 - r * 3)
        pygame.draw.circle(art_surf, (*top_col, alpha), (cx, cy), r, 1)
    surf.blit(art_surf, art_rect.topleft)

    # Type
    type_str = "Sort" if card.card_type == "spell" else "Équip."
    type_surf = fnt_small.render(type_str, True, top_col)
    surf.blit(type_surf, (6, 84))

    # Séparateur
    pygame.draw.line(surf, COL_BORDER, (4, 96), (width - 4, 96))

    # Description (wrap manuel)
    words = card.desc.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if fnt_desc.size(test)[0] <= width - 10:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)

    y_desc = 100
    for l in lines[:3]:
        ls = fnt_desc.render(l, True, COL_GREY)
        surf.blit(ls, (5, y_desc))
        y_desc += ls.get_height() + 1

    # Overlay si non jouable
    if not playable:
        dim = pygame.Surface((width, height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        surf.blit(dim, (0, 0))

    return surf


def render_card_back(width: int = CARD_W, height: int = CARD_H) -> pygame.Surface:
    """Dos de carte."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(
        surf, (30, 20, 50), (0, 0, width, height), border_radius=CARD_RADIUS
    )
    for i in range(0, width, 8):
        pygame.draw.line(surf, (50, 35, 80), (i, 0), (0, i), 1)
    for i in range(0, height, 8):
        pygame.draw.line(surf, (50, 35, 80), (i, height), (width, i), 1)
    pygame.draw.rect(
        surf, COL_BORDER, (0, 0, width, height), width=2, border_radius=CARD_RADIUS
    )
    return surf


# ---------------------------------------------------------------------------
# Barre de vie / mana
# ---------------------------------------------------------------------------


def draw_stat_bar(
    surf: pygame.Surface,
    x: int,
    y: int,
    w: int,
    h: int,
    value: int,
    max_value: int,
    color_full: Tuple,
    color_low: Optional[Tuple] = None,
    label: str = "",
):
    ratio = value / max(1, max_value)
    bar_color = color_full
    if color_low and ratio < 0.35:
        bar_color = color_low

    pygame.draw.rect(surf, (20, 15, 35), (x, y, w, h), border_radius=4)
    fill_w = max(0, int(w * ratio))
    if fill_w:
        pygame.draw.rect(surf, bar_color, (x, y, fill_w, h), border_radius=4)
    pygame.draw.rect(surf, COL_BORDER, (x, y, w, h), width=1, border_radius=4)

    fnt = pygame.font.SysFont("dejavusans", 11, bold=True)
    txt = f"{label}{value}/{max_value}"
    ts = fnt.render(txt, True, COL_WHITE)
    surf.blit(ts, (x + w // 2 - ts.get_width() // 2, y + h // 2 - ts.get_height() // 2))


# ---------------------------------------------------------------------------
# CardGame — DefaultManager
# ---------------------------------------------------------------------------


class CardGame:
    """
    Jeu de cartes intégrable dans le Manager principal de MoleTale.

    Utilisation depuis game.py :
        self.manager.states["CARD"].start(
            playing_mode=self.playing_mode,
            on_victory=self._on_card_victory,
            on_defeat=self._on_card_defeat,
        )
        self.manager.change_state("CARD")
    """

    def __init__(self, screen: pygame.Surface, manager: "Manager"):
        self.screen = screen
        self.manager = manager

        self.larg, self.haut = screen.get_size()

        # Polices
        self._init_fonts()

        # État interne
        self.battle: Optional[CardBattle] = None
        self.playing_mode: str = "solo"
        self.on_victory: Optional[Callable] = None
        self.on_defeat: Optional[Callable] = None

        # UI état
        self.selected_card_idx: int = -1  # index dans player_hand (-1 = aucune)
        self.hovered_card_idx: int = -1
        self.end_btn_hovered: bool = False
        self.end_phase: Optional[str] = None  # "victory" | "defeat" | None
        self.end_timer: float = 0.0
        self.end_alpha: int = 0

        # Cache des surfaces de cartes
        self._card_cache: Dict[str, pygame.Surface] = {}

        # Zones cliquables (calculées dans display)
        self._hand_rects: List[pygame.Rect] = []
        self._end_turn_rect: Optional[pygame.Rect] = None

    # ── Interface DefaultManager ──────────────────────────────────────────────

    def set_screen(self, screen: pygame.Surface):
        self.screen = screen
        self.larg, self.haut = screen.get_size()
        self._init_fonts()

    def start(
        self,
        playing_mode: str = "solo",
        on_victory: Optional[Callable] = None,
        on_defeat: Optional[Callable] = None,
    ):
        """Initialise et démarre un nouveau combat de cartes."""
        self.playing_mode = playing_mode
        self.on_victory = on_victory
        self.on_defeat = on_defeat
        self.battle = CardBattle()
        self.selected_card_idx = -1
        self.hovered_card_idx = -1
        self.end_phase = None
        self.end_timer = 0.0
        self.end_alpha = 0
        self._card_cache.clear()

    def event(self, events: List[pygame.event.Event]):
        if self.battle is None:
            return

        mouse = pygame.mouse.get_pos()
        battle = self.battle

        for event in events:
            if event.type == pygame.QUIT:
                self.manager.running = False

            # Clavier : Entrée = fin de tour, Échap = pause (ignoré ici)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and battle.phase == "player_turn":
                    battle.end_turn()
                    self.selected_card_idx = -1
                    self._check_end_phase()
                elif event.key == pygame.K_ESCAPE:
                    # Retour au jeu sans résolution (abandon temporaire)
                    self.manager.change_state("GAME")

            # Clic
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Fin de partie → clic n'importe où pour continuer
                if self.end_phase is not None and self.end_alpha >= 200:
                    self._resolve_end()
                    continue

                # Cartes en main
                for i, rect in enumerate(self._hand_rects):
                    if rect.collidepoint(mouse):
                        if self.selected_card_idx == i:
                            # Deuxième clic sur la même carte → joue
                            if battle.play_card(i):
                                self.selected_card_idx = -1
                                self._card_cache.clear()
                                self._check_end_phase()
                        else:
                            self.selected_card_idx = i
                        break
                else:
                    self.selected_card_idx = -1

                # Bouton "Fin de tour"
                if (
                    self._end_turn_rect
                    and self._end_turn_rect.collidepoint(mouse)
                    and battle.phase == "player_turn"
                ):
                    battle.end_turn()
                    self.selected_card_idx = -1
                    self._card_cache.clear()
                    self._check_end_phase()

        # Hover
        self.hovered_card_idx = -1
        for i, rect in enumerate(self._hand_rects):
            if rect.collidepoint(mouse):
                self.hovered_card_idx = i
                break
        self.end_btn_hovered = bool(
            self._end_turn_rect and self._end_turn_rect.collidepoint(mouse)
        )

    def update(self):
        if self.end_phase is not None:
            self.end_timer += self.manager.clock.get_time() / 1000.0
            self.end_alpha = min(255, int(self.end_alpha + 8))

    def display(self):
        if self.battle is None:
            self.screen.fill(COL_BG)
            return

        self.screen.fill(COL_BG)
        self._draw_background()
        self._draw_boss_area()
        self._draw_player_area()
        self._draw_hand()
        self._draw_log()
        self._draw_end_turn_button()
        self._draw_equips()
        self._draw_hint()

        if self.end_phase is not None:
            self._draw_end_overlay()

    # ── Dessin ────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.fnt_title = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.fnt_sub = pygame.font.SysFont("dejavusans", 18, bold=True)
        self.fnt_body = pygame.font.SysFont("dejavusans", 14)
        self.fnt_small = pygame.font.SysFont("dejavusans", 12)
        self.fnt_hint = pygame.font.SysFont("dejavusans", 11)

    def _draw_background(self):
        """Fond stylisé avec lignes de grille éthérées."""
        for y in range(0, self.haut, 40):
            pygame.draw.line(self.screen, (25, 18, 45), (0, y), (self.larg, y))
        for x in range(0, self.larg, 40):
            pygame.draw.line(self.screen, (25, 18, 45), (x, 0), (x, self.haut))

        # Halo central
        halo = pygame.Surface((self.larg, self.haut), pygame.SRCALPHA)
        for r in range(200, 0, -10):
            alpha = max(0, 30 - r // 8)
            pygame.draw.circle(
                halo, (80, 40, 130, alpha), (self.larg // 2, self.haut // 2), r * 2
            )
        self.screen.blit(halo, (0, 0))

    def _draw_boss_area(self):
        """Zone du boss en haut de l'écran."""
        b = self.battle.boss
        panel_w, panel_h = 340, 110
        px = self.larg // 2 - panel_w // 2
        py = 14

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(
            surf, (45, 10, 10, 200), (0, 0, panel_w, panel_h), border_radius=10
        )
        pygame.draw.rect(
            surf, COL_BORDER, (0, 0, panel_w, panel_h), width=2, border_radius=10
        )
        self.screen.blit(surf, (px, py))

        title = self.fnt_sub.render("⚔ BOSS", True, COL_RED)
        self.screen.blit(title, (px + 12, py + 10))

        draw_stat_bar(
            self.screen,
            px + 12,
            py + 38,
            panel_w - 24,
            16,
            b.hp,
            b.max_hp,
            COL_RED,
            COL_RED,
            "PV ",
        )
        draw_stat_bar(
            self.screen,
            px + 12,
            py + 60,
            panel_w - 24,
            12,
            b.mana,
            b.max_mana,
            COL_MANA,
            None,
            "💧 ",
        )

        # Statuts
        status_parts = []
        if b.poison_turns:
            status_parts.append(f"☠{b.poison_turns}")
        if b.shield:
            status_parts.append(f"🛡{b.shield}")
        if b.dmg_reduction:
            status_parts.append(f"🔻{b.dmg_reduction}")
        if b.attack != CardBattle.BOSS_ATK:
            status_parts.append(f"⚔{b.attack}")
        if status_parts:
            st = self.fnt_small.render("  ".join(status_parts), True, COL_GOLD)
            self.screen.blit(st, (px + 12, py + 80))

    def _draw_player_area(self):
        """Zone du joueur en bas à gauche."""
        p = self.battle.player
        panel_w, panel_h = 280, 110
        px = 14
        py = self.haut - panel_h - 14

        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(
            surf, (10, 30, 20, 200), (0, 0, panel_w, panel_h), border_radius=10
        )
        pygame.draw.rect(
            surf, COL_BORDER, (0, 0, panel_w, panel_h), width=2, border_radius=10
        )
        self.screen.blit(surf, (px, py))

        title = self.fnt_sub.render("⚔ Vous", True, COL_GREEN)
        self.screen.blit(title, (px + 12, py + 10))

        draw_stat_bar(
            self.screen,
            px + 12,
            py + 38,
            panel_w - 24,
            16,
            p.hp,
            p.max_hp,
            COL_HP_FULL,
            COL_HP_LOW,
            "PV ",
        )
        draw_stat_bar(
            self.screen,
            px + 12,
            py + 60,
            panel_w - 24,
            12,
            p.mana,
            p.max_mana,
            COL_MANA,
            None,
            "💧 ",
        )

        # Tour
        turn_surf = self.fnt_small.render(f"Tour {self.battle.turn}", True, COL_GREY)
        self.screen.blit(
            turn_surf, (px + panel_w - turn_surf.get_width() - 10, py + 10)
        )

        # Statuts joueur
        status_parts = []
        if p.poison_turns:
            status_parts.append(f"☠{p.poison_turns}")
        if p.shield:
            status_parts.append(f"🛡{p.shield}")
        if p.dmg_reduction:
            status_parts.append(f"🔻{p.dmg_reduction}")
        if p.attack != CardBattle.PLAYER_ATK:
            status_parts.append(f"⚔{p.attack}")
        if status_parts:
            st = self.fnt_small.render("  ".join(status_parts), True, COL_GOLD)
            self.screen.blit(st, (px + 12, py + 80))

    def _get_card_surf(
        self, card: Card, selected: bool, playable: bool
    ) -> pygame.Surface:
        key = f"{card.name}_{selected}_{playable}"
        if key not in self._card_cache:
            self._card_cache[key] = render_card(card, selected, playable)
        return self._card_cache[key]

    def _draw_hand(self):
        """Dessine la main du joueur avec un léger arc."""
        if not self.battle:
            return

        hand = self.battle.player_hand
        n = len(hand)
        self._hand_rects = []

        if n == 0:
            return

        spacing = min(CARD_W + 14, (self.larg - 340) // max(n, 1))
        total_w = spacing * (n - 1) + CARD_W
        start_x = self.larg // 2 - total_w // 2
        base_y = self.haut - CARD_H - 130

        for i, card in enumerate(hand):
            selected = i == self.selected_card_idx
            hovered = i == self.hovered_card_idx
            playable = (
                self.battle.player.mana >= card.cost
                and self.battle.phase == "player_turn"
            )

            x = start_x + i * spacing
            # Arc subtil
            arc_offset = int(abs(i - (n - 1) / 2) * 2)
            y = base_y - arc_offset
            if selected:
                y -= 22
            elif hovered:
                y -= 12

            surf = self._get_card_surf(card, selected, playable)
            rect = pygame.Rect(x, y, CARD_W, CARD_H)
            self._hand_rects.append(rect)
            self.screen.blit(surf, (x, y))

            # Indicateur "cliquer pour jouer" si sélectionnée
            if selected:
                hint = self.fnt_hint.render("Cliquer pour jouer", True, COL_GOLD)
                self.screen.blit(
                    hint, (x + CARD_W // 2 - hint.get_width() // 2, y - 16)
                )

        # Compteur de cartes deck / défausse
        dk = self.fnt_small.render(
            f"🂠 Deck : {len(self.battle.player_deck)}   🗑 Défausse : {len(self.battle.player_discard)}",
            True,
            COL_GREY,
        )
        self.screen.blit(dk, (self.larg // 2 - dk.get_width() // 2, self.haut - 28))

    def _draw_log(self):
        """Journal des événements (droite)."""
        log = self.battle.log
        pw, ph = 220, min(len(log) * 18 + 20, self.haut - 160)
        px = self.larg - pw - 10
        py = 140

        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(surf, (15, 12, 28, 200), (0, 0, pw, ph), border_radius=8)
        pygame.draw.rect(surf, COL_BORDER, (0, 0, pw, ph), width=1, border_radius=8)
        self.screen.blit(surf, (px, py))

        title = self.fnt_hint.render("Journal", True, COL_GREY)
        self.screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 4))

        visible = log[-(ph // 18 - 1) :]
        for j, entry in enumerate(visible):
            # Détermine la couleur selon le préfixe
            col = COL_WHITE
            if entry.startswith("🔴"):
                col = COL_RED
            elif entry.startswith("💚") or entry.startswith("❤"):
                col = COL_GREEN
            elif entry.startswith("💀") or entry.startswith("☠"):
                col = (180, 100, 220)
            elif entry.startswith("🏆"):
                col = COL_GOLD
            elif entry.startswith("—"):
                col = COL_GREY
            ls = self.fnt_hint.render(entry, True, col)
            self.screen.blit(ls, (px + 6, py + 18 + j * 17))

    def _draw_end_turn_button(self):
        """Bouton 'Fin de Tour'."""
        bw, bh = 160, 40
        bx = self.larg - bw - 14
        by = self.haut - bh - 14

        phase = self.battle.phase if self.battle else "?"
        enabled = phase == "player_turn"
        hovered = self.end_btn_hovered and enabled

        col_bg = (55, 85, 155, 220) if hovered else (22, 22, 44, 200)
        col_brd = (120, 150, 225, 255) if hovered else (50, 50, 95, 255)
        col_txt = COL_WHITE if enabled else COL_GREY

        surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(surf, col_bg, (0, 0, bw, bh), border_radius=8)
        pygame.draw.rect(surf, col_brd, (0, 0, bw, bh), width=2, border_radius=8)
        self.screen.blit(surf, (bx, by))

        label = "Fin de tour  ↵" if enabled else "Tour du boss…"
        ts = self.fnt_body.render(label, True, col_txt)
        self.screen.blit(
            ts,
            (bx + bw // 2 - ts.get_width() // 2, by + bh // 2 - ts.get_height() // 2),
        )

        self._end_turn_rect = pygame.Rect(bx, by, bw, bh)

    def _draw_equips(self):
        """Affiche les équipements actifs du joueur."""
        equips = self.battle.player_equips
        if not equips:
            return

        title = self.fnt_hint.render("Équipements actifs :", True, COL_GREY)
        self.screen.blit(title, (14, self.haut - CARD_H - 170))

        for i, card in enumerate(equips):
            mini = render_card(card, width=60, height=84)
            self.screen.blit(mini, (14 + i * 66, self.haut - CARD_H - 160))

    def _draw_hint(self):
        """Aide contextuelle en bas au centre."""
        if self.battle.phase == "player_turn":
            hint = "Clic x2 pour jouer — [Entrée] fin de tour"
        elif self.battle.phase == "boss_turn":
            hint = "Le boss réfléchit…"
        else:
            hint = "Clic pour continuer"
        hs = self.fnt_hint.render(hint, True, COL_GREY)
        self.screen.blit(hs, (self.larg // 2 - hs.get_width() // 2, self.haut - 44))

    def _draw_end_overlay(self):
        """Overlay de fin de combat (victoire / défaite)."""
        if self.end_alpha <= 0:
            return

        ov = pygame.Surface((self.larg, self.haut), pygame.SRCALPHA)
        ov.fill((8, 8, 18, min(180, self.end_alpha)))
        self.screen.blit(ov, (0, 0))

        if self.end_alpha < 120:
            return

        is_victory = self.end_phase == "victory"
        big_text = "VICTOIRE !" if is_victory else "DÉFAITE…"
        sub_text = "Le boss est vaincu !" if is_victory else "Vous avez succombé."
        col_big = COL_GOLD if is_victory else COL_RED

        big_surf = self.fnt_title.render(big_text, True, col_big)
        big_surf.set_alpha(self.end_alpha)
        self.screen.blit(
            big_surf, (self.larg // 2 - big_surf.get_width() // 2, self.haut // 2 - 60)
        )

        sub_surf = self.fnt_sub.render(sub_text, True, COL_WHITE)
        sub_surf.set_alpha(self.end_alpha)
        self.screen.blit(
            sub_surf, (self.larg // 2 - sub_surf.get_width() // 2, self.haut // 2)
        )

        if self.end_alpha >= 200:
            cont_surf = self.fnt_body.render("Cliquer pour continuer…", True, COL_GREY)
            self.screen.blit(
                cont_surf,
                (self.larg // 2 - cont_surf.get_width() // 2, self.haut // 2 + 50),
            )

    # ── Logique fin de combat ─────────────────────────────────────────────────

    def _check_end_phase(self):
        if self.battle and self.battle.phase in ("victory", "defeat"):
            self.end_phase = self.battle.phase
            self.end_alpha = 0

    def _resolve_end(self):
        """Appelle le callback approprié et change d'état."""
        if self.end_phase == "victory" and self.on_victory:
            self.on_victory()
        elif self.end_phase == "defeat" and self.on_defeat:
            self.on_defeat()
        else:
            # Fallback : retour au menu principal
            self.manager.change_state("MENU_P")

        self.end_phase = None
        self.battle = None


# ---------------------------------------------------------------------------
# Exécution standalone (test hors jeu principal)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((900, 650))
    pygame.display.set_caption("CardGame — Test standalone")
    clock = pygame.time.Clock()

    # Stub minimal du Manager pour le test
    class _StubManager:
        running = True

        def change_state(self, s):
            print(f"[Manager] change_state → {s}")

        class clock:
            @staticmethod
            def get_time():
                return 16

    manager = _StubManager()
    game = CardGame(screen, manager)

    def on_win():
        print("Victoire ! Retour au jeu.")
        manager.running = False

    def on_lose():
        print("Défaite. Retour au jeu.")
        manager.running = False

    game.start(on_victory=on_win, on_defeat=on_lose)

    while manager.running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                manager.running = False

        game.event(events)
        game.update()
        game.display()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
