import pygame
from typing import Tuple
from menu import Text
from random import shuffle

CARD_TYPES = {0 : "Player", 1 : "Ally", 2 : "Spell", 3 : "Equip"}

class Card:
    def __init__(self, type: int, name: str):
        self.type = type
        self.name = name
    
    def __str__(self):
        return f"({CARD_TYPES[self.type]}) {self.name}"
      

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


class Deck:
    def __init__(self, cards: list[Card]):
        self.cards = cards
        self.size = len(self.cards)
        self. artwork
          
    def add2Deck(self, cards: Card):
        self.cards.append(cards)
        self.size += 1
    
    def rmFromTopDeck(self):
        self.size -=1
        return self.cards.pop()
    
    def shuffle(self):
        shuffle(self.cards)

    def __str__(self):
        printer = "[ "
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += "]"
        return printer
    
    def display(self):
        self.artwork = 


class DiscardPile:
    def __init__(self):
        self.cards = []
        self.size = 0

    def add2Discard(self, card: Card):
        self.cards.append(card)
        self.size += 1

    def rmFromDiscard(self, index: int):
        if 0 < index < self.size:
            self.size =-1
            return self.card.pop[index]
    
    def __str__(self):
        printer = "[ "
        for i in range(self.size):
            printer += f"{str(self.cards[i])}, "
        printer += "]"
        return printer




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


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
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
    def display(self):
        self.screen.fill('#603B2A')
        
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.event()
            self.display()
   


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((1920, 1080))
    running = True
    screenSize = screen.get_size()
    x_pos = (screenSize[0] - (35*5))/ 2
    y_pos = (screenSize[1] - (47*5))/ 2
    test = PlayerCard(screen, (x_pos, y_pos))
    deck = Deck([Card(2, "Fireball"), Card(3, "Scythe"), Card(2, "Heal"), Card(2, "tornado"), Card(3, "A WII FUCKING GUN"), Card(3, "brick"), Card(3, "Mana Crown")])
    hand = Hand()
    deck.shuffle()
    hand.add2Hand(deck.rmFromTopDeck())
    print(hand)
    print(deck)
    test.run()