import random
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class MinesGame:
    """Represents a Mines game session."""
    
    GRID_SIZE = 5
    TOTAL_TILES = 25
    
    MULTIPLIERS = {
        1: [1.03, 1.08, 1.12, 1.18, 1.24, 1.30, 1.37, 1.46, 1.55, 1.65, 1.77, 1.90, 2.06, 2.25, 2.47, 2.75, 3.09, 3.54, 4.12, 4.95, 6.19, 8.25, 12.37, 24.75],
        3: [1.09, 1.20, 1.32, 1.46, 1.63, 1.83, 2.07, 2.36, 2.73, 3.20, 3.80, 4.60, 5.69, 7.22, 9.44, 12.82, 18.21, 27.59, 45.99, 87.78, 201.12, 659.06, 4634.34],
        5: [1.18, 1.41, 1.71, 2.09, 2.58, 3.26, 4.18, 5.49, 7.42, 10.35, 15.04, 22.91, 37.08, 64.54, 122.83, 263.21, 657.78, 2017.27, 8441.45, 75973.05],
        10: [1.57, 2.35, 3.60, 5.68, 9.30, 15.89, 28.61, 54.85, 113.85, 260.53, 677.37, 2113.29, 8453.16, 59172.15],
        15: [2.36, 4.95, 10.89, 25.30, 63.25, 174.04, 540.35, 1982.95, 9176.40, 64235.20],
        20: [4.95, 19.80, 89.10, 475.20, 3326.40, 33264.00],
        24: [24.75, 618.75, 24750.00],
    }
    
    def __init__(self, user_id: int, wager: float, num_mines: int, seed: Optional[str] = None):
        self.user_id = user_id
        self.wager = wager
        self.num_mines = num_mines
        self.revealed_tiles: List[int] = []
        self.game_over = False
        self.cashed_out = False
        self.hit_mine = False
        self.current_multiplier = 1.0
        self.created_at = datetime.now()
        
        if seed:
            self.seed = seed
        else:
            self.seed = hashlib.sha256(f"{user_id}{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()[:16]
        
        random.seed(self.seed)
        all_positions = list(range(self.TOTAL_TILES))
        random.shuffle(all_positions)
        self.mine_positions = set(all_positions[:num_mines])
        random.seed()
    
    def get_multiplier_for_reveals(self, num_reveals: int) -> float:
        """Get the multiplier based on number of safe tiles revealed."""
        if num_reveals == 0:
            return 1.0
        
        closest_mines = min(self.MULTIPLIERS.keys(), key=lambda x: abs(x - self.num_mines))
        multipliers = self.MULTIPLIERS[closest_mines]
        
        index = min(num_reveals - 1, len(multipliers) - 1)
        return multipliers[index]
    
    def reveal_tile(self, position: int) -> Tuple[bool, bool, float, bool]:
        """
        Reveal a tile at the given position.
        Returns: (is_safe, game_over, current_multiplier, already_revealed)
        """
        if self.game_over:
            return (False, True, self.current_multiplier, False)
        
        if position in self.revealed_tiles:
            # Already revealed - ignore this click
            return (True, False, self.current_multiplier, True)
        
        is_mine = position in self.mine_positions
        
        if is_mine:
            self.hit_mine = True
            self.game_over = True
            return (False, True, 0.0, False)
        
        self.revealed_tiles.append(position)
        self.current_multiplier = self.get_multiplier_for_reveals(len(self.revealed_tiles))
        
        safe_tiles = self.TOTAL_TILES - self.num_mines
        if len(self.revealed_tiles) >= safe_tiles:
            self.game_over = True
            self.cashed_out = True
        
        return (True, self.game_over, self.current_multiplier, False)
    
    def cash_out(self) -> float:
        """Cash out and end the game. Returns the payout amount."""
        if self.game_over or len(self.revealed_tiles) == 0:
            return 0.0
        
        self.cashed_out = True
        self.game_over = True
        return self.wager * self.current_multiplier
    
    def get_potential_payout(self) -> float:
        """Get the current potential payout if player cashes out now."""
        if len(self.revealed_tiles) == 0:
            return self.wager
        return self.wager * self.current_multiplier
    
    def get_grid_display(self, reveal_all: bool = False) -> List[List[str]]:
        """
        Generate a 5x5 grid for display.
        Returns list of rows, each containing tile symbols.
        """
        grid = []
        for row in range(self.GRID_SIZE):
            row_tiles = []
            for col in range(self.GRID_SIZE):
                pos = row * self.GRID_SIZE + col
                
                if reveal_all and self.game_over:
                    if pos in self.mine_positions:
                        row_tiles.append("💣")
                    elif pos in self.revealed_tiles:
                        row_tiles.append("💎")
                    else:
                        row_tiles.append("⬜")
                elif pos in self.revealed_tiles:
                    row_tiles.append("💎")
                elif self.hit_mine and pos in self.mine_positions:
                    row_tiles.append("💣")
                else:
                    row_tiles.append("❓")
            grid.append(row_tiles)
        return grid
    
    def to_dict(self) -> Dict:
        """Serialize game state for storage."""
        return {
            "user_id": self.user_id,
            "wager": self.wager,
            "num_mines": self.num_mines,
            "revealed_tiles": self.revealed_tiles,
            "mine_positions": list(self.mine_positions),
            "game_over": self.game_over,
            "cashed_out": self.cashed_out,
            "hit_mine": self.hit_mine,
            "current_multiplier": self.current_multiplier,
            "seed": self.seed,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MinesGame':
        """Deserialize game state from storage."""
        game = cls.__new__(cls)
        game.user_id = data["user_id"]
        game.wager = data["wager"]
        game.num_mines = data["num_mines"]
        game.revealed_tiles = data["revealed_tiles"]
        game.mine_positions = set(data["mine_positions"])
        game.game_over = data["game_over"]
        game.cashed_out = data["cashed_out"]
        game.hit_mine = data["hit_mine"]
        game.current_multiplier = data["current_multiplier"]
        game.seed = data["seed"]
        game.created_at = datetime.fromisoformat(data["created_at"])
        return game
