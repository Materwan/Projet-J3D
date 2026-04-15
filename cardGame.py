import pygame
from typing import Tuple, List
from menu import Text
from random import shuffle

# Name : (Type, Artwork)
CARD_LIST = {
    "Dmg2": ("Spell", "Ressources/Cartes/PlaceHolderSpell.png"),
    "HpUp3": ("Equip", "Ressources/Cartes/PlaceHolderEquip.png"),
}


class Card:
    def __init__(self, screen: pygame.surface.Surface, name: str):
        self.name = name
        self.screen = screen
        self.scale = (35 * 3.25, 47 * 3.25)
        if name in CARD_LIST:
            self.type = CARD_LIST[name][0]
            self.artwork = pygame.image.load(CARD_LIST[name][1])
        else:
            self.type = "None"
            self.artwork = pygame.image.load("Ressources/Cartes/NoCard.png")

    def __str__(self):
        return f"({self.type} {self.name})"

    def display(self, position):
        self.artwork = pygame.transform.scale(self.artwork, self.scale)
        self.screen.blit(self.artwork, position)


class Hand:
    def __init__(self, screen: pygame.surface.Surface, position: Tuple[int, int]):
        self.screen = screen
        self.position = position
        self.cards: List[Card] | None = []
        self.size = 0
        self.scale = (7 * 35 * 3.25, 47 * 3.25)

    def add2Hand(self, card: Card):
        if card:
            print("add2Hand")
            print(card)
            print(type(card))
            print(self)
            self.cards.append(card)
            self.size += 1
            print(self, "\n")
        else:
            print("No card")

    def rmFromHand(self, index: int):
        if 0 <= index < self.size:
            self.size -= 1
            return self.cards.pop(index)
        return None

    def __str__(self):
        printer = "[ "
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += "]"
        return printer

    def display(self):
        if self.size != 0:
            for cards in self.cards:
                cards.display(self.position)


class Deck:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        position: Tuple[int, int],
        cards: List[Card],
        artworkCard: str | None = "Ressources/Cartes/PlaceHolderDeck.png",
        artworkEmpty: str | None = "Ressources/Cartes/PlaceHolderDeckEmpty.png",
    ):
        self.screen = screen
        self.position = position
        self.cards = cards
        self.size = len(self.cards)
        self.artworkCard = pygame.image.load(artworkCard)
        self.artworkEmpty = pygame.image.load(artworkEmpty)
        self.scale = (35 * 3.25, 47 * 3.25)

    def add2Deck(self, card: Card):
        if card:
            print("add2Deck")
            print(self)
            self.cards.append(card)
            self.size += 1
            print(self, "\n")
        else:
            print("No card")

    def rmFromTopDeck(self):
        if self.size != 0:
            self.size -= 1
            return self.cards.pop()
        return None

    def shuffle(self):
        shuffle(self.cards)

    def __str__(self):
        if not self.cards:
            return "[]"
        printer = "["
        for card in self.cards:
            printer += f"{str(card)}, "
        printer = printer.rstrip(", ") + "]"
        return printer

    def display(self):
        if self.size == 0:
            self.artwork = pygame.transform.scale(self.artworkEmpty, self.scale)
        else:
            self.artwork = pygame.transform.scale(self.artworkCard, self.scale)
        self.screen.blit(self.artwork, self.position)


class DiscardPile:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        position: Tuple[int, int],
        artwork: str | None = "Ressources/Cartes/PlaceHolderDiscard.png",
    ):
        self.screen = screen
        self.position = position
        self.cards: List[Card] | None = []
        self.size = 0
        self.artworkEmpty = pygame.image.load(artwork)
        self.scale = (35 * 3.25, 47 * 3.25)

    def add2Discard(self, card: Card):
        if card:
            self.cards.append(card)
            self.size += 1

    def rmFromDiscard(self, index: int):
        if 0 <= index < self.size:
            self.size -= 1
            return self.cards.pop(index)

    def __str__(self):
        if not self.cards:
            return "[]"
        printer = "["
        for card in self.cards:
            printer += f"{str(card)}, "
        printer = printer.rstrip(", ") + "]"
        return printer

    def display(self):
        if self.size == 0:
            self.artwork = pygame.transform.scale(self.artworkEmpty, self.scale)
        else:
            self.artwork = pygame.transform.scale(self.cards[-1].artwork, self.scale)
        self.screen.blit(self.artwork, self.position)


class SpellZone:
    def __init__(self):
        self.cards = []
        self.size = 0


class EquipZone:
    def __init__(self):
        self.cards = []
        self.size = 0

class PlayerCard:
    def __init__(
        self,
        screen: pygame.surface.Surface,
        position: Tuple[int, int],
        hp=20,
        mp=1,
        ap=1,
        artwork="Ressources/Cartes/PlayerCard.png",
    ):
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.hp = hp
        self.mp = mp  # Mana
        self.ap = ap  # Attaque
        self.maxHp = hp
        self.maxMp = mp
        self.maxAp = ap
        self.position = position
        self.artworkBase = pygame.image.load(artwork)
        self.bigArtWorkBase = pygame.image.load(artwork)
        self.scale = (35 * 3.25, 47 * 3.25)
        self.running = True
        self.hover = False
        self.hoverTime = -1
        self.biggerpicture = False

    def event(self):
        if (
            self.position[0] + self.scale[0]
            > pygame.mouse.get_pos()[0]
            > self.position[0]
            and self.position[1] + self.scale[1]
            > pygame.mouse.get_pos()[1]
            > self.position[1]
        ):
            if self.hoverTime == -1:
                self.hoverTime = pygame.time.get_ticks()
            elif self.hoverTime + 700 < pygame.time.get_ticks():
                self.biggerpicture = True
        else:
            self.hoverTime = -1
            self.biggerpicture = False

    def display(self):
        self.artwork = pygame.transform.scale(self.artworkBase, self.scale)
        self.hpDisplay = Text("Impact", 12, str(self.hp), "#FFFFFF", self.artwork)
        self.mpDisplay = Text("Impact", 12, str(self.mp), "#FFFFFF", self.artwork)
        self.apDisplay = Text("Impact", 12, str(self.ap), "#FFFFFF", self.artwork)
        self.hpDisplay.draw_text((18, 125))
        self.mpDisplay.draw_text((54, 125))
        self.apDisplay.draw_text((86, 125))
        self.screen.blit(self.artwork, self.position)

        if self.biggerpicture == True:
            self.bigArtWork = pygame.transform.scale(
                self.bigArtWorkBase, (self.scale[0] * 3.5, self.scale[1] * 3.5)
            )
            self.hpDisplay = Text(
                "Impact", 55, str(self.hp), "#FFFFFF", self.bigArtWork
            )
            self.mpDisplay = Text(
                "Impact", 55, str(self.mp), "#FFFFFF", self.bigArtWork
            )
            self.apDisplay = Text(
                "Impact", 55, str(self.ap), "#FFFFFF", self.bigArtWork
            )
            self.hpDisplay.draw_text((56, 430))
            self.mpDisplay.draw_text((186, 430))
            self.apDisplay.draw_text((302, 430))
            self.screen.blit(
                self.bigArtWork, (self.screenSize[0] / 1.55, self.screenSize[0] / 8)
            )

class Game:
    def __init__(
        self,
        pCard: PlayerCard,
        pDeck: Deck,
        pDiscard: DiscardPile,
        pHand: Hand,
        bCard: PlayerCard,
        bDeck: Deck,
        bDiscard: DiscardPile,
        bHand: Hand,
    ):
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.artworkBG = pygame.image.load("Ressources/Cartes/ecran_tcg.png")

        self.pCard = pCard
        self.pDeck = pDeck
        self.pDiscard = pDiscard
        self.pHand = pHand

        self.bCard = bCard
        self.bDeck = bDeck
        self.bDiscard = bDiscard
        self.bHand = bHand

        self.running = True
        print(self.pDeck, self.pHand)
    
    def GameStart(self):
        for _ in range(5):
            self.pHand.add2Hand(self.pDeck.rmFromTopDeck())
            self.bHand.add2Hand(self.bDeck.rmFromTopDeck())
    
    def TurnEnd(self):
        self.bCard.hp -= self.pCard.ap
        if (self.bCard.hp > 0):
            self.pCard.hp -= self.bCard.ap
        else:
            self.win()
            return 0
        if (self.pCard.hp > 0):
                self.bCard.mp, self.bCard.ap = self.bCard.maxMp, self.bCard.maxAp
                self.pHand.add2Hand(self.pDeck.rmFromTopDeck())
                self.bHand.add2Hand(self.bDeck.rmFromTopDeck())
        else:
            self.lose()
            return 0
        
    
    def win(self):
        print("You Win !")
        self.running = False
    
    def lose(self):
        print("You Lose !")
        self.running = False

    def display(self):
        self.artworkBG = pygame.transform.scale(self.artworkBG, self.screenSize)
        self.screen.blit(self.artworkBG, (0, 0))
        self.pDeck.display()
        self.pDiscard.display()
        self.pHand.display()
        self.pCard.display()
        self.bDeck.display()
        self.bDiscard.display()
        self.bHand.display()
        self.bCard.display()
        pygame.display.flip()

    def event(self):
        self.pCard.event()
        self.bCard.event()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                self.TurnEnd()
                
    def run(self):
        self.GameStart()
        while self.running:
            self.display()
            self.event()


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((0, 0))
    running = True
    screenSize = screen.get_size()

    player = PlayerCard(
        screen,
        ((screenSize[0] - (35 * 3.25)) / 2, (screenSize[1] - (47 * 3.25)) / 1.25),
    )
    decklistP = [Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3")]
    deckP = Deck(
        screen,
        (
            (screenSize[0] - (35 * 3.25)) * 34 / 35,
            (screenSize[1] - (47 * 3.25)) * 5.1 / 7,
        ),
        decklistP,
    )
    discardP = DiscardPile(
        screen,
        (
            (screenSize[0] - (35 * 3.25)) * 34 / 35,
            (screenSize[1] - (47 * 3.25)) * 6.5 / 7,
        ),
    )
    handP = Hand(
        screen,
        ((screenSize[0] - (35 * 3.25)) * 9 / 35, (screenSize[1] - (47 * 3.25)) * 1 / 7),
    )

    boss = PlayerCard(
        screen,
        ((screenSize[0] - (35 * 3.25)) / 2, (screenSize[1] - (47 * 3.25)) / 3.75),
    )
    decklistB = [Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3")]
    deckB = Deck(
        screen,
        (
            (screenSize[0] - (35 * 3.25)) * 1 / 35,
            (screenSize[1] - (47 * 3.25)) * 1.9 / 7,
        ),
        decklistB,
    )
    discardB = DiscardPile(
        screen,
        (
            (screenSize[0] - (35 * 3.25)) * 1 / 35,
            (screenSize[1] - (47 * 3.25)) * 0.5 / 7,
        ),
    )
    handB = Hand(
        screen,
        ((screenSize[0] - (35 * 3.25)) * 9 / 35, (screenSize[1] - (47 * 3.25)) * 1 / 7),
    )

    test = Game(player, deckP, discardP, handP, boss, deckB, discardB, handB)
    test.run()
