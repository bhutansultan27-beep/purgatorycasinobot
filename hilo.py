import random
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class Card:
    SUITS = ['♠', '♥', '♦', '♣']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    RANK_VALUES = {'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                   '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13}
    
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        self.value = self.RANK_VALUES[rank]
    
    def __str__(self) -> str:
        suit_emoji = {'♠': '♠️', '♥': '♥️', '♦': '♦️', '♣': '♣️'}
        return f"{self.rank}{suit_emoji.get(self.suit, self.suit)}"
    
    def to_dict(self) -> Dict:
        return {'rank': self.rank, 'suit': self.suit, 'value': self.value}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Card':
        return cls(data['rank'], data['suit'])


class Deck:
    def __init__(self, seed: Optional[str] = None):
        self.cards: List[Card] = []
        self.seed = seed
        self._build_deck()
        self._shuffle()
    
    def _build_deck(self):
        self.cards = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.cards.append(Card(rank, suit))
    
    def _shuffle(self):
        if self.seed:
            random.seed(self.seed)
        random.shuffle(self.cards)
        if self.seed:
            random.seed()
    
    def draw(self) -> Optional[Card]:
        if len(self.cards) == 0:
            return None
        return self.cards.pop()
    
    def cards_remaining(self) -> int:
        return len(self.cards)
    
    def burn_cards(self, count: int = 3):
        for _ in range(min(count, len(self.cards))):
            self.cards.pop()
    
    def to_dict(self) -> Dict:
        return {
            'cards': [c.to_dict() for c in self.cards],
            'seed': self.seed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Deck':
        deck = cls.__new__(cls)
        deck.cards = [Card.from_dict(c) for c in data['cards']]
        deck.seed = data['seed']
        return deck


class HiLoGame:
    HOUSE_EDGE = 0.02
    
    def __init__(self, user_id: int, wager: float, seed: Optional[str] = None):
        self.user_id = user_id
        self.initial_wager = wager
        self.current_wager = wager
        self.game_over = False
        self.cashed_out = False
        self.won = False
        self.current_multiplier = 1.0
        self.round_number = 0
        self.history: List[Dict] = []
        self.created_at = datetime.now()
        
        if seed:
            self.seed = seed
        else:
            self.seed = hashlib.sha256(f"{user_id}{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:16]
        
        self.deck = Deck(self.seed)
        self.current_card = self.deck.draw()
        self.next_card: Optional[Card] = None
    
    def _calculate_probability(self, prediction: str) -> float:
        if not self.current_card:
            return 0.0
        
        current_value = self.current_card.value
        cards_remaining = self.deck.cards_remaining()
        
        if cards_remaining == 0:
            return 0.0
        
        remaining_values = [c.value for c in self.deck.cards]
        
        if prediction == 'higher':
            winning_cards = sum(1 for v in remaining_values if v > current_value or v == current_value)
            if current_value == 13:
                winning_cards = sum(1 for v in remaining_values if v == 13)
        elif prediction == 'lower':
            winning_cards = sum(1 for v in remaining_values if v < current_value or v == current_value)
            if current_value == 1:
                winning_cards = sum(1 for v in remaining_values if v == 1)
        elif prediction == 'tie':
            winning_cards = sum(1 for v in remaining_values if v == current_value)
        else:
            return 0.0
        
        return winning_cards / cards_remaining
    
    def _calculate_multiplier(self, prediction: str) -> float:
        probability = self._calculate_probability(prediction)
        if probability == 0:
            return 0.0
        
        fair_multiplier = 1.0 / probability
        return round(fair_multiplier * (1.0 - self.HOUSE_EDGE), 2)
    
    def get_odds(self) -> Dict:
        return {
            'higher': {
                'probability': round(self._calculate_probability('higher') * 100, 1),
                'multiplier': self._calculate_multiplier('higher')
            },
            'lower': {
                'probability': round(self._calculate_probability('lower') * 100, 1),
                'multiplier': self._calculate_multiplier('lower')
            },
            'tie': {
                'probability': round(self._calculate_probability('tie') * 100, 1),
                'multiplier': self._calculate_multiplier('tie')
            }
        }
    
    def make_prediction(self, prediction: str) -> Dict:
        if self.game_over:
            return {'error': 'Game is over'}
        
        if not self.current_card:
            return {'error': 'No current card'}
        
        if self.deck.cards_remaining() == 0:
            self.game_over = True
            self.cashed_out = True
            return self.get_game_state()
        
        prediction = prediction.lower()
        if prediction not in ['higher', 'lower', 'tie']:
            return {'error': 'Invalid prediction. Choose higher, lower, or tie'}
        
        prediction_multiplier = self._calculate_multiplier(prediction)
        
        self.next_card = self.deck.draw()
        
        if not self.next_card:
            self.game_over = True
            self.cashed_out = True
            return self.get_game_state()
        
        current_value = self.current_card.value
        next_value = self.next_card.value
        
        is_win = False
        
        if prediction == 'higher':
            if current_value == 13:
                is_win = next_value == 13
            else:
                is_win = next_value >= current_value
        elif prediction == 'lower':
            if current_value == 1:
                is_win = next_value == 1
            else:
                is_win = next_value <= current_value
        elif prediction == 'tie':
            is_win = next_value == current_value
        
        round_result = {
            'round': self.round_number + 1,
            'current_card': str(self.current_card),
            'next_card': str(self.next_card),
            'prediction': prediction,
            'multiplier_offered': prediction_multiplier,
            'won': is_win
        }
        self.history.append(round_result)
        
        if is_win:
            self.current_multiplier *= prediction_multiplier
            self.current_multiplier = round(self.current_multiplier, 2)
            self.round_number += 1
            
            self.current_card = self.next_card
            self.next_card = None
            
            self.deck.burn_cards(3)
            
            if self.deck.cards_remaining() == 0:
                self.game_over = True
                self.cashed_out = True
                self.won = True
        else:
            self.game_over = True
            self.won = False
            self.current_multiplier = 0.0
        
        return self.get_game_state()
    
    def skip_card(self) -> Dict:
        if self.game_over:
            return {'error': 'Game is over'}
        
        if self.deck.cards_remaining() == 0:
            self.game_over = True
            self.cashed_out = True
            return self.get_game_state()
        
        skip_result = {
            'round': self.round_number,
            'skipped_card': str(self.current_card),
            'action': 'skip'
        }
        self.history.append(skip_result)
        
        self.current_card = self.deck.draw()
        self.next_card = None
        
        if self.current_multiplier > 1.0:
            self.current_multiplier *= 0.95
            self.current_multiplier = round(self.current_multiplier, 2)
        
        return self.get_game_state()
    
    def cash_out(self) -> Dict:
        if self.game_over:
            return {'error': 'Game is already over'}
        
        if self.round_number == 0:
            return {'error': 'Must complete at least one round before cashing out'}
        
        self.game_over = True
        self.cashed_out = True
        self.won = True
        
        return self.get_game_state()
    
    def get_payout(self) -> float:
        if not self.game_over:
            return 0.0
        if self.won or self.cashed_out:
            return self.initial_wager * self.current_multiplier
        return 0.0
    
    def get_potential_payout(self) -> float:
        return self.initial_wager * self.current_multiplier
    
    def get_profit(self) -> float:
        return self.get_payout() - self.initial_wager
    
    def get_game_state(self) -> Dict:
        return {
            'user_id': self.user_id,
            'initial_wager': self.initial_wager,
            'current_card': str(self.current_card) if self.current_card else None,
            'current_card_value': self.current_card.value if self.current_card else None,
            'cards_remaining': self.deck.cards_remaining(),
            'round_number': self.round_number,
            'current_multiplier': self.current_multiplier,
            'potential_payout': self.get_potential_payout(),
            'game_over': self.game_over,
            'cashed_out': self.cashed_out,
            'won': self.won,
            'payout': self.get_payout() if self.game_over else 0,
            'profit': self.get_profit() if self.game_over else 0,
            'odds': self.get_odds() if not self.game_over else {},
            'history': self.history[-5:]
        }
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'initial_wager': self.initial_wager,
            'current_wager': self.current_wager,
            'current_card': self.current_card.to_dict() if self.current_card else None,
            'next_card': self.next_card.to_dict() if self.next_card else None,
            'deck': self.deck.to_dict(),
            'game_over': self.game_over,
            'cashed_out': self.cashed_out,
            'won': self.won,
            'current_multiplier': self.current_multiplier,
            'round_number': self.round_number,
            'history': self.history,
            'seed': self.seed,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HiLoGame':
        game = cls.__new__(cls)
        game.user_id = data['user_id']
        game.initial_wager = data['initial_wager']
        game.current_wager = data['current_wager']
        game.current_card = Card.from_dict(data['current_card']) if data['current_card'] else None
        game.next_card = Card.from_dict(data['next_card']) if data['next_card'] else None
        game.deck = Deck.from_dict(data['deck'])
        game.game_over = data['game_over']
        game.cashed_out = data['cashed_out']
        game.won = data['won']
        game.current_multiplier = data['current_multiplier']
        game.round_number = data['round_number']
        game.history = data['history']
        game.seed = data['seed']
        game.created_at = datetime.fromisoformat(data['created_at'])
        return game
