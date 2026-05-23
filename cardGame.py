import pygame
from typing import Tuple, List
from animations import Text
from random import shuffle


# ============================ The Card ============================

class Card:
    """The default cards of the game
        They are divided in two categories : Spells and Equips,
        They can be in the different zones of the game"""
    def __init__(self, screen: pygame.surface.Surface, name: str):
        self.name = name
        self.screen = screen
        self.scale = (35 * 3.25, 47 * 3.25)
        if name in CARD_LIST:
            self.type = CARD_LIST[name]["Type"]
            self.artwork = pygame.image.load(CARD_LIST[name]["Artwork"])
        else:
            self.type = "None"
            self.artwork = pygame.image.load("Ressources/Cartes/NoCard.png")

    def __str__(self):
        return f"({self.type} {self.name})"

    def display_visible(self, position):
        self.artwork = pygame.transform.scale(self.artwork, self.scale)
        self.screen.blit(self.artwork, position) 
    
    def display_invisible(self, position):
        self.artwork = pygame.transform.scale(pygame.image.load("Ressources/Cartes/PlaceHolderDeck.png"), self.scale)
        self.screen.blit(self.artwork, position)


# ============================ The Zones ============================
#Notes :  - Each zone comes are tid to a player, there is not any shared zone between the player
#         - A Zone do not have any card limit (i.e : A player Hand can have 177013 Cards without having to discard any of them at the end of turn)

class Hand:
    """The player's hand
        The player will be able to play the Cards contained in it and play them (they play them by putting them in other zones)
        At the beginning of each game, each player draw 5 cards, and then draw one at the start of each turn (except turn 1)
        A player can only see their own hands (even in multiplayer), but they ar able to see the number of cards in others hand"""
    def __init__(self,
                 screen: pygame.surface.Surface,
                 position: Tuple[int, int],
                 is_visible = True):
        
        self.screen = screen
        self.position = position
        self.cards: List[Card] | None = []
        self.size = 0
        self.scale = (7 * 35 * 3.25, 47 * 3.25)
        self.is_visible = is_visible

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
            spacing = self.scale[0] * 0.1
            total_width = spacing * (self.size - 1) + self.scale[0]
            start_x = self.position[0] - total_width / 2
            y = self.position[1]
            i = 0
            for card in self.cards:
                x = start_x + i * spacing
                if (self.is_visible):
                    card.display_visible((x, y))
                else:
                    card.display_invisible((x, y))
                i += 1


class Deck:
    """Where the Cards are at the beginning
        When the game starts, all the player cards are in the deck
        The cards in the deck is the only zone where the card are hidden from both players at all time
        All player can see the number of remaining cards in each deck"""
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

    def rmFromTop1Deck(self):
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
    """This is where the Cards ends up
        After a Spell Card effect happend, or that any card have been discarded in any way, it will go to the discard pile
        The cards in the discard is visible at all time, and both discards can be check by the player at any time"""
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
    """This is where the Spell Cards are put before being played
        This zone act like a queue, a player can put any number of cards in it (as long as they have the mana to do so) and arrange it in any order they want
        At the end of turn, all the spells will used (and discarded) one after the other
        The order of dequeue is : Player 1 -> Player 2 (if MultiPlayer) -> Boss
        (i.e : p1 SpellZone : FireBall, Heal Potion     Boss SpellZone : Poison, Equip Destroyer, Explosion
            Then in the end of turn, the spells will come in effect in this order : Fireball -> Poison -> Heal Potion -> Equip Destroyer -> Explosion)
        A player can only see his own Spell Zone, but the number of card in it can be seen by any player"""
    def __init__(self):
        self.cards = []
        self.size = 0

    def add2SZ(self, card: Card):
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

    def rmFromSZ(self, index: int):
        if 0 <= index < self.size:
            self.size -= 1
            return self.cards.pop(index)
        return None
    

class EquipZone:
    """This is where the Equip Cards goes when they're played
        When a card comes to this zone, it effect happend immidieately
        Equip Cards are passive effect that buff the player card
        All players can see each other Equip Zone at all time"""
    def __init__(self):
        self.cards = []
        self.size = 0
    
    def add2EZ(self, card: Card):
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

    def rmFromEZ(self, index: int):
        if 0 <= index < self.size:
            self.size -= 1
            return self.cards.pop(index)
        return None


# ============================ The Player Cards ============================
class PlayerCard:
    """This is the Card representing the players and the boss
        It has 3 main values : the Player's Health (HP), the Player's Mana (MP) and the Player's Attack (AP)
        All the values are capped at a maximum value (That can be increased by card effects)"""
    def __init__(
        self,
        screen: pygame.surface.Surface,
        position: Tuple[int, int],
        hp: int,
        mp: int,
        ap: int,
        artwork="Ressources/Cartes/PlayerCard.png",
    ):
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.hp = hp
        self.mp = mp  # Mana
        self.ap = ap  # Attack
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
        self.hpDisplay = Text(str(self.hp), self.artwork ,(18, 125), "Impact", 14, "#FFFFFF")
        self.mpDisplay = Text(str(self.mp), self.artwork ,(54, 125), "Impact", 14, "#FFFFFF")
        self.apDisplay = Text(str(self.ap), self.artwork ,(86, 125), "Impact", 14, "#FFFFFF")
        self.hpDisplay.draw_text()
        self.mpDisplay.draw_text()
        self.apDisplay.draw_text()
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


def dealDamage(receiver : PlayerCard, dmg : int):
    receiver.hp -= dmg

def healDamage(receiver : PlayerCard, heal : int):
    receiver.hp += heal
    if (receiver.hp > receiver.maxHp):
        receiver.hp = receiver.maxHp

def increasemaxHP(receiver : PlayerCard, increase : int):
    receiver.maxHp += increase
    healDamage(receiver, increase)

# Name : (Type, Artwork, Effect, Value)
CARD_LIST = {
    "Dmg2": {"Type" : "Spell", "Artwork" : "Ressources/Cartes/PlaceHolderSpell.png", "Effect" : dealDamage, "Value" : 2},
    "HpUp3": {"Type" : "Equip", "Artwork" : "Ressources/Cartes/PlaceHolderEquip.png", "Effect" : increasemaxHP, "Value" : 3},
}




class Game:
    """This is how the game works"""
    def __init__(
        self,
        p1HP: int,
        p1MP : int,
        p1AP : int,
        p1DL: List[Card],
        bCard: PlayerCard,
        bDeck: Deck,
        is_multiplayer : bool = False,
        p2HP: int | None = None,
        p2MP: int | None = None,
        p2AP: int | None = None,
        p2DL: List[Card] | None = None,
    ):
        
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.artworkBG = pygame.image.load("Ressources/Cartes/ecran_tcg.png")
        self.is_multiplayer = is_multiplayer

        if not self.is_multiplayer:

            self.p1Card = PlayerCard(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) / 2,
                    (screenSize[1] - (47 * 3.25)) / 1.25
                ),
                p1HP,
                p1MP,
                p1AP
            )

            self.p1Deck = Deck(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 34 / 35,
                    (screenSize[1] - (47 * 3.25)) * 5.1 / 7
                ),
                p1DL
            )

            self.p1Discard = DiscardPile(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 34 / 35,
                    (screenSize[1] - (47 * 3.25)) * 6.5 / 7
                )
            )

            self.p1Hand = Hand(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 3 / 4,
                    (screenSize[1] - (47 * 3.25)) * 34 / 35
                )
            )

        else:
            if None in (p2HP, p2MP, p2AP, p2DL):
                raise ValueError("No P2 in Multiplayer mode")
            
            self.p1Card = PlayerCard(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) / 3,
                    (screenSize[1] - (47 * 3.25)) / 1.25
                ),
                p1HP,
                p1MP,
                p1AP
            )

            self.p1Deck = Deck(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 34 / 35,
                    (screenSize[1] - (47 * 3.25)) * 5.1 / 7
                ),
                p1DL
            )

            self.p1Discard = DiscardPile(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 34 / 35,
                    (screenSize[1] - (47 * 3.25)) * 6.5 / 7
                )
            )

            self.p1Hand = Hand(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 3 / 4,
                    (screenSize[1] - (47 * 3.25)) * 34 / 35
                )
            )


            self.p2Card = PlayerCard(
                screen,
                (
                    (screenSize[0] - (35 * 3.25)) * 2 / 3,
                    (screenSize[1] - (47 * 3.25)) / 1.25
                ),
                p2HP,
                p2MP,
                p2AP
            )

        self.bCard = bCard
        self.bDeck = bDeck
        self.bDiscard = DiscardPile(
            screen,
            (
                (screenSize[0] - (35 * 3.25)) * 34 / 35,
                (screenSize[1] - (47 * 3.25)) * 6.5 / 7
            )
        )
        self.bHand = Hand(
            screen,
            (
                (screenSize[0] - (35 * 3.25)) * 3 / 4,
                (screenSize[1] - (47 * 3.25)) * 1 / 35
            ),
            False
        )

        self.running = True
        print(self.p1Deck, self.p1Hand)
    
    def GameStart(self):
        for _ in range(5):
            self.p1Hand.add2Hand(self.p1Deck.rmFromTop1Deck())
            self.bHand.add2Hand(self.bDeck.rmFromTop1Deck())
    
    def TurnEnd(self):
        self.bCard.hp -= self.p1Card.ap
        if (self.bCard.hp > 0):
            self.p1Card.hp -= self.bCard.ap
        else:
            self.win()
            return 0
        if (self.p1Card.hp > 0):
                self.bCard.mp, self.bCard.ap = self.bCard.maxMp, self.bCard.maxAp
                self.p1Hand.add2Hand(self.p1Deck.rmFromTop1Deck())
                self.bHand.add2Hand(self.bDeck.rmFromTop1Deck())
        else:
            self.lose()
            return 0
        
    
    def win(self):
        print("You Win !")
        self.running = False
    
    def lose(self):
        print("You Lose !")
        self.running = False

    def get_to_send_data_host(self):
        return {"host" : {"Card" : self.p1Card
                          },
                "boss" : {""}}

    def display(self):
        self.artworkBG = pygame.transform.scale(self.artworkBG, self.screenSize)
        self.screen.blit(self.artworkBG, (0, 0))
        self.p1Deck.display()
        self.p1Discard.display()
        self.p1Hand.display()
        self.p1Card.display()
        if self.is_multiplayer:
            self.p2Card.display()
        self.bDeck.display()
        self.bDiscard.display()
        self.bHand.display()
        self.bCard.display()
        pygame.display.flip()

    def event(self):
        self.p1Card.event()
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
    
    decklistP = [Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3"), Card(screen, "Dmg2"), Card(screen, "HpUp3")]

    boss = PlayerCard(
        screen,
        ((screenSize[0] - (35 * 3.25)) / 2, (screenSize[1] - (47 * 3.25)) / 3.75),
        20,
        10,
        1
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

    test = Game(20, 10, 1, decklistP, boss, deckB, True, 40, 2, 1, decklistP)
    test.run()
