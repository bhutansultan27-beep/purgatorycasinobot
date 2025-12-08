import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime

RANKS = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 0, 'J': 0, 'Q': 0, 'K': 0, 'A': 1
}
SUITS = ['H', 'D', 'C', 'S']
CARD_FACES = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        self.value = RANKS[rank]

    def __str__(self):
        display_rank = '10' if self.rank == 'T' else self.rank
        return f"[{display_rank}{CARD_FACES.get(self.suit, '')}]"

class Deck:
    def __init__(self, num_decks: int = 8):
        self.cards: List[Card] = []
        self._initialize_cards(num_decks)
        self.shuffle()

    def _initialize_cards(self, num_decks: int):
        for _ in range(num_decks):
            for rank in RANKS:
                for suit in SUITS:
                    self.cards.append(Card(rank, suit))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self) -> Card:
        if len(self.cards) < 52:
            self.cards = []
            self._initialize_cards(8)
            self.shuffle()
        return self.cards.pop()

class BaccaratHand:
    def __init__(self):
        self.cards: List[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def get_value(self) -> int:
        total = sum(card.value for card in self.cards)
        return total % 10
    
    def get_cards_str(self) -> str:
        return ' '.join(str(card) for card in self.cards)
    
    def is_natural(self) -> bool:
        return len(self.cards) == 2 and self.get_value() >= 8

class BaccaratGame:
    def __init__(self, bet_amount: float, bet_type: str, deck: Optional[Deck] = None):
        self.deck = deck if deck else Deck()
        self.bet_amount = bet_amount
        self.bet_type = bet_type.lower()
        self.player_hand = BaccaratHand()
        self.banker_hand = BaccaratHand()
        self.game_over = False
        self.result = None
        self.payout = 0.0
        self.created_at = datetime.now()
    
    def play_round(self) -> Dict:
        for _ in range(2):
            self.player_hand.add_card(self.deck.deal_card())
            self.banker_hand.add_card(self.deck.deal_card())
        
        player_value = self.player_hand.get_value()
        banker_value = self.banker_hand.get_value()
        
        player_third_card = None
        
        if not self.player_hand.is_natural() and not self.banker_hand.is_natural():
            if player_value <= 5:
                player_third_card = self.deck.deal_card()
                self.player_hand.add_card(player_third_card)
                player_value = self.player_hand.get_value()
            
            if player_third_card is None:
                if banker_value <= 5:
                    self.banker_hand.add_card(self.deck.deal_card())
            else:
                third_card_value = player_third_card.value
                
                if banker_value <= 2:
                    self.banker_hand.add_card(self.deck.deal_card())
                elif banker_value == 3 and third_card_value != 8:
                    self.banker_hand.add_card(self.deck.deal_card())
                elif banker_value == 4 and third_card_value in [2, 3, 4, 5, 6, 7]:
                    self.banker_hand.add_card(self.deck.deal_card())
                elif banker_value == 5 and third_card_value in [4, 5, 6, 7]:
                    self.banker_hand.add_card(self.deck.deal_card())
                elif banker_value == 6 and third_card_value in [6, 7]:
                    self.banker_hand.add_card(self.deck.deal_card())
        
        player_final = self.player_hand.get_value()
        banker_final = self.banker_hand.get_value()
        
        if player_final > banker_final:
            self.result = 'player'
        elif banker_final > player_final:
            self.result = 'banker'
        else:
            self.result = 'tie'
        
        self._calculate_payout()
        self.game_over = True
        
        return self.get_game_state()
    
    def _calculate_payout(self):
        if self.bet_type == 'player':
            if self.result == 'player':
                self.payout = self.bet_amount * 2
            elif self.result == 'tie':
                self.payout = self.bet_amount
            else:
                self.payout = 0
        
        elif self.bet_type == 'banker':
            if self.result == 'banker':
                self.payout = self.bet_amount * 1.95
            elif self.result == 'tie':
                self.payout = self.bet_amount
            else:
                self.payout = 0
        
        elif self.bet_type == 'tie':
            if self.result == 'tie':
                self.payout = self.bet_amount * 9
            else:
                self.payout = 0
    
    def get_profit(self) -> float:
        return self.payout - self.bet_amount
    
    def get_game_state(self) -> Dict:
        return {
            'game_over': self.game_over,
            'player_hand': {
                'cards': self.player_hand.get_cards_str(),
                'value': self.player_hand.get_value(),
                'is_natural': self.player_hand.is_natural()
            },
            'banker_hand': {
                'cards': self.banker_hand.get_cards_str(),
                'value': self.banker_hand.get_value(),
                'is_natural': self.banker_hand.is_natural()
            },
            'bet_type': self.bet_type,
            'bet_amount': self.bet_amount,
            'result': self.result,
            'payout': self.payout,
            'profit': self.get_profit()
        }
