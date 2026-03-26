import pygame
from typing import Tuple
from menu import Text
from random import shuffle

#Name : (Type, Artwork)
CARD_LIST = {"Dmg2" : ("Spell", "Ressources/Cartes/PlaceHolderSpell.png"),
             "HpUp3" : ("Equip", "Ressources/Cartes/PlaceHolderEquip.png")}

class Card:
    def __init__(self, name: str):
        self.name = name
        if name in CARD_LIST:
            self.type = CARD_LIST[name][0]
            self.artwork = pygame.image.load(CARD_LIST[name][1])
        else:
            self.type = "None"
            self.artwork = pygame.image.load("Ressources/Cartes/NoCard.png")
    
    def __str__(self):
        return f"({self.type} {self.name})"
    
    def display(self):
        self.artwork = pygame.transform.scale(self.artwork, self.scale)
        self.screen.blit(self.artwork, self.position)
      
class Hand:
    def __init__(self):
        self.cards = []
        self.size = 0

    def add2Hand(self, card: Card):
        self.cards.append(card)
        self.size += 1

    def rmFromHand(self, index: int):
        if 0 < index < self.size:
            self.size =-1
            return self.card.pop[index]
    
    def __str__(self):
        printer = "[ "
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += "]"
        return printer
    
    def display(self):
        for cards in self.cards:
            cards.display()

class Deck:
    def __init__(self, screen: pygame.surface.Surface, position: Tuple[int,int], cards: list[Card],  artworkCard = "Ressources/Cartes/PlaceHolderDeck.png", artworkEmpty = "Ressources/Cartes/PlaceHolderDeckEmpty.png"):
        self.screen = screen
        self.position = (position)
        self.cards = cards
        self.size = len(self.cards)
        self.artworkCard = pygame.image.load(artworkCard)
        self.artworkEmpty = pygame.image.load(artworkEmpty)
        self.scale = (35*5, 47*5)
          
    def add2Deck(self, cards: Card):
        self.cards.append(cards)
        self.size += 1
    
    def rmFromTopDeck(self):
        if(self.size != 0):
            self.size -=1
            return self.cards.pop()
    
    def shuffle(self):
        shuffle(self.cards)

    def __str__(self):
        printer = "["
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += f"{str(self.cards[-1])}]"
        return printer
    
    def display(self):
        if (self.size == 0):
            self.artwork = pygame.transform.scale(self.artworkEmpty, self.scale)
        else:
            self.artwork = pygame.transform.scale(self.artworkCard, self.scale)
        self.screen.blit(self.artwork, self.position)

class DiscardPile:
    def __init__(self, screen: pygame.surface.Surface, position: Tuple[int,int],  artwork = "Ressources/Cartes/PlaceHolderDiscard.png"):
        self.screen = screen
        self.position = (position)
        self.cards = []
        self.size = 0
        self.artworkEmpty = pygame.image.load(artwork)
        self.scale = (35*5, 47*5)

    def add2Discard(self, card: Card):
        if card:
            self.cards.append(card)
            self.size += 1

    def rmFromDiscard(self, index: int):
        if 0 <= index < self.size:
            self.size -= 1
            return self.cards.pop(index)
    
    def __str__(self):
        printer = "[ "
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += "]"
        return printer
    
    def display(self):
        if self.size == 0:
            self.artwork = pygame.transform.scale(self.artworkEmpty, self.scale)
        else:
            self.artwork = pygame.transform.scale(self.cards[-1].artwork, self.scale)
        self.screen.blit(self.artwork, self.position)
            
class PlayerCard:
    def __init__(self, screen: pygame.surface.Surface, position: Tuple[int,int], hp = 20, mp = 1, ap = 1, artwork = "Ressources/Cartes/PlayerCard.png"):
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.hp = hp
        self.mp = mp
        self.ap = ap
        self.maxHp = hp
        self.maxMp = mp
        self.maxAp = ap
        self.position = (position)
        self.artwork = pygame.image.load(artwork)
        self.scale = (35*5, 47*5)
        self.running = True
        self.hover = False
        self.hoverTime = -1
        self.biggerpicture = False
        

    def event(self):
        if self.position[0]+self.scale[0] > pygame.mouse.get_pos()[0] > self.position[0] and self.position[1]+self.scale[1] > pygame.mouse.get_pos()[1] > self.position[1]:
            if self.hoverTime == -1:
               self.hoverTime = pygame.time.get_ticks()
            elif self.hoverTime + 700 < pygame.time.get_ticks():
                self.biggerpicture = True
        else:
            self.hoverTime = -1
            self.biggerpicture = False
    
    def display(self):
        self.artwork = pygame.transform.scale(self.artwork, self.scale)
        self.screen.blit(self.artwork, self.position)
        self.hpDisplay = Text("Impact", 19, str(self.hp), "#FFFFFF", self.artwork)
        self.mpDisplay = Text("Impact", 19, str(self.mp), "#FFFFFF", self.artwork)
        self.apDisplay = Text("Impact", 19, str(self.ap), "#FFFFFF", self.artwork)
        self.hpDisplay.draw_text((30, 190))
        self.mpDisplay.draw_text((83, 190))
        self.apDisplay.draw_text((130, 190))
        
        if self.biggerpicture == True:
            self.bigArtWork = pygame.transform.scale(self.artwork, (self.scale[0]*2.5, self.scale[1]*2.5))
            self.screen.blit(self.bigArtWork, (self.screenSize[0]/1.55, self.screenSize[0]/8))

class Game:
    def __init__(self, pCard: PlayerCard, deck: Deck, discard: DiscardPile):
        self.screen = screen
        self.screenSize = self.screen.get_size()
        self.pCard = pCard
        self.deck = deck
        self.discard = discard
        self.running = True

    def display(self):
        self.screen.fill('#603B2A')
        self.deck.display()
        self.discard.display()
        self.pCard.display()
        pygame.display.flip()
    
    def event(self):
        self.pCard.event()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                discard.add2Discard(deck.rmFromTopDeck())
            if event.type == pygame.KEYUP:
                deck.add2Deck(discard.rmFromDiscard(discard.size-1))
                deck.shuffle()
                print(deck)
    
    def run(self):
        while self.running:
            self.display()
            self.event()

if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((1920, 1080))
    running = True
    screenSize = screen.get_size()

    player = PlayerCard(screen, ((screenSize[0] - (35*5))/2, (screenSize[1] - (47*5))/2))

    deck = Deck(screen, ((screenSize[0] - (35*5))*6/7, (screenSize[1] - (47*5))*6/7), [Card("Dmg2"), Card("HpUp3")])
    
    discard = DiscardPile(screen, ((screenSize[0] - (35*5))*26/35,(screenSize[1] - (47*5))*6/7))   
    
    hand = Hand()

    test = Game(player, deck, discard)
    test.run()