import random
import hashlib
import math
from typing import Dict, Optional, Tuple
from datetime import datetime

class LimboGame:
    HOUSE_EDGE = 0.03
    MIN_MULTIPLIER = 1.01
    MAX_MULTIPLIER = 1000000.0
    
    def __init__(self, user_id: int, wager: float, target_multiplier: float, seed: Optional[str] = None):
        self.user_id = user_id
        self.wager = wager
        self.target_multiplier = max(self.MIN_MULTIPLIER, min(target_multiplier, self.MAX_MULTIPLIER))
        self.result_multiplier = 0.0
        self.game_over = False
        self.won = False
        self.payout = 0.0
        self.created_at = datetime.now()
        
        if seed:
            self.seed = seed
        else:
            self.seed = hashlib.sha256(f"{user_id}{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:16]
    
    def calculate_win_probability(self, target: float) -> float:
        if target <= 1.0:
            return 1.0
        return (1.0 - self.HOUSE_EDGE) / target
    
    def play(self) -> Dict:
        if self.game_over:
            return self.get_game_state()
        
        random.seed(self.seed)
        raw_result = random.random()
        random.seed()
        
        if raw_result == 0:
            self.result_multiplier = self.MAX_MULTIPLIER
        else:
            self.result_multiplier = (1.0 - self.HOUSE_EDGE) / raw_result
        
        self.result_multiplier = round(min(self.result_multiplier, self.MAX_MULTIPLIER), 2)
        
        self.won = self.result_multiplier >= self.target_multiplier
        
        if self.won:
            self.payout = self.wager * self.target_multiplier
        else:
            self.payout = 0.0
        
        self.game_over = True
        return self.get_game_state()
    
    def get_profit(self) -> float:
        if self.won:
            return self.payout - self.wager
        return -self.wager
    
    def get_game_state(self) -> Dict:
        return {
            'user_id': self.user_id,
            'wager': self.wager,
            'target_multiplier': self.target_multiplier,
            'result_multiplier': self.result_multiplier,
            'game_over': self.game_over,
            'won': self.won,
            'payout': self.payout,
            'profit': self.get_profit() if self.game_over else 0,
            'win_probability': self.calculate_win_probability(self.target_multiplier)
        }
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'wager': self.wager,
            'target_multiplier': self.target_multiplier,
            'result_multiplier': self.result_multiplier,
            'game_over': self.game_over,
            'won': self.won,
            'payout': self.payout,
            'seed': self.seed,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LimboGame':
        game = cls.__new__(cls)
        game.user_id = data['user_id']
        game.wager = data['wager']
        game.target_multiplier = data['target_multiplier']
        game.result_multiplier = data['result_multiplier']
        game.game_over = data['game_over']
        game.won = data['won']
        game.payout = data['payout']
        game.seed = data['seed']
        game.created_at = datetime.fromisoformat(data['created_at'])
        return game


def get_preset_multipliers() -> list:
    return [1.10, 1.25, 1.50, 2.00, 3.00, 5.00, 10.00, 25.00, 50.00, 100.00]
