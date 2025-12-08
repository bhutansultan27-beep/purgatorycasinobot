import random
import hashlib
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime

class KenoGame:
    GRID_SIZE = 8
    TOTAL_NUMBERS = 40
    DRAW_COUNT = 10
    MAX_PICKS = 10
    
    PAYOUTS = {
        1: {1: 3.0},
        2: {2: 9.0},
        3: {2: 2.0, 3: 26.0},
        4: {2: 1.0, 3: 5.0, 4: 80.0},
        5: {3: 2.0, 4: 12.0, 5: 300.0},
        6: {3: 1.0, 4: 5.0, 5: 50.0, 6: 1000.0},
        7: {3: 1.0, 4: 3.0, 5: 15.0, 6: 150.0, 7: 3000.0},
        8: {4: 2.0, 5: 10.0, 6: 50.0, 7: 500.0, 8: 10000.0},
        9: {4: 1.0, 5: 5.0, 6: 25.0, 7: 150.0, 8: 2000.0, 9: 25000.0},
        10: {5: 3.0, 6: 15.0, 7: 75.0, 8: 500.0, 9: 5000.0, 10: 100000.0}
    }
    
    def __init__(self, user_id: int, wager: float, seed: Optional[str] = None):
        self.user_id = user_id
        self.wager = wager
        self.picked_numbers: Set[int] = set()
        self.drawn_numbers: Set[int] = set()
        self.game_started = False
        self.game_over = False
        self.hits = 0
        self.payout = 0.0
        self.created_at = datetime.now()
        
        if seed:
            self.seed = seed
        else:
            self.seed = hashlib.sha256(f"{user_id}{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:16]
    
    def pick_number(self, number: int) -> Tuple[bool, str]:
        if self.game_started:
            return (False, "Game already started")
        
        if number < 1 or number > self.TOTAL_NUMBERS:
            return (False, f"Invalid number. Pick between 1 and {self.TOTAL_NUMBERS}")
        
        if number in self.picked_numbers:
            self.picked_numbers.remove(number)
            return (True, f"Removed {number}")
        
        if len(self.picked_numbers) >= self.MAX_PICKS:
            return (False, f"Maximum {self.MAX_PICKS} picks allowed")
        
        self.picked_numbers.add(number)
        return (True, f"Picked {number}")
    
    def start_draw(self) -> Dict:
        if len(self.picked_numbers) == 0:
            return {'error': 'Pick at least 1 number'}
        
        if self.game_started:
            return {'error': 'Game already started'}
        
        self.game_started = True
        
        random.seed(self.seed)
        all_numbers = list(range(1, self.TOTAL_NUMBERS + 1))
        random.shuffle(all_numbers)
        self.drawn_numbers = set(all_numbers[:self.DRAW_COUNT])
        random.seed()
        
        self.hits = len(self.picked_numbers & self.drawn_numbers)
        self._calculate_payout()
        self.game_over = True
        
        return self.get_game_state()
    
    def _calculate_payout(self):
        num_picks = len(self.picked_numbers)
        if num_picks in self.PAYOUTS:
            payout_table = self.PAYOUTS[num_picks]
            if self.hits in payout_table:
                multiplier = payout_table[self.hits]
                self.payout = self.wager * multiplier
    
    def get_multiplier(self) -> float:
        if self.wager == 0:
            return 0.0
        return self.payout / self.wager
    
    def get_profit(self) -> float:
        return self.payout - self.wager
    
    def get_grid_display(self) -> List[List[Dict]]:
        grid = []
        rows = 5
        cols = 8
        
        for row in range(rows):
            row_data = []
            for col in range(cols):
                num = row * cols + col + 1
                if num > self.TOTAL_NUMBERS:
                    continue
                
                cell = {
                    'number': num,
                    'picked': num in self.picked_numbers,
                    'drawn': num in self.drawn_numbers if self.game_over else False,
                    'hit': num in self.picked_numbers and num in self.drawn_numbers if self.game_over else False
                }
                row_data.append(cell)
            if row_data:
                grid.append(row_data)
        return grid
    
    def get_game_state(self) -> Dict:
        return {
            'user_id': self.user_id,
            'wager': self.wager,
            'picked_numbers': sorted(list(self.picked_numbers)),
            'drawn_numbers': sorted(list(self.drawn_numbers)) if self.game_over else [],
            'num_picks': len(self.picked_numbers),
            'game_started': self.game_started,
            'game_over': self.game_over,
            'hits': self.hits if self.game_over else 0,
            'multiplier': self.get_multiplier() if self.game_over else 0,
            'payout': self.payout,
            'profit': self.get_profit() if self.game_over else 0
        }
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'wager': self.wager,
            'picked_numbers': list(self.picked_numbers),
            'drawn_numbers': list(self.drawn_numbers),
            'game_started': self.game_started,
            'game_over': self.game_over,
            'hits': self.hits,
            'payout': self.payout,
            'seed': self.seed,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KenoGame':
        game = cls.__new__(cls)
        game.user_id = data['user_id']
        game.wager = data['wager']
        game.picked_numbers = set(data['picked_numbers'])
        game.drawn_numbers = set(data['drawn_numbers'])
        game.game_started = data['game_started']
        game.game_over = data['game_over']
        game.hits = data['hits']
        game.payout = data['payout']
        game.seed = data['seed']
        game.created_at = datetime.fromisoformat(data['created_at'])
        return game
