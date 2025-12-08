from typing import Dict, List, Optional, Tuple

class Connect4Game:
    ROWS = 6
    COLS = 7
    EMPTY = 0
    PLAYER1 = 1
    PLAYER2 = 2
    
    PLAYER1_EMOJI = "🔴"
    PLAYER2_EMOJI = "🟡"
    EMPTY_EMOJI = "⚪"
    
    def __init__(self, player1_id: int, player2_id: int, wager: float):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.wager = wager
        self.board: List[List[int]] = [[self.EMPTY for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_player = self.PLAYER1
        self.winner: Optional[int] = None
        self.game_over = False
        self.is_draw = False
        self.player1_roll: Optional[int] = None
        self.player2_roll: Optional[int] = None
        self.first_player_decided = False
    
    def set_dice_rolls(self, player1_roll: int, player2_roll: int):
        self.player1_roll = player1_roll
        self.player2_roll = player2_roll
        if player1_roll >= player2_roll:
            self.current_player = self.PLAYER1
        else:
            self.current_player = self.PLAYER2
        self.first_player_decided = True
    
    def get_current_player_id(self) -> int:
        return self.player1_id if self.current_player == self.PLAYER1 else self.player2_id
    
    def get_opponent_id(self) -> int:
        return self.player2_id if self.current_player == self.PLAYER1 else self.player1_id
    
    def get_player_number(self, user_id: int) -> int:
        if user_id == self.player1_id:
            return self.PLAYER1
        elif user_id == self.player2_id:
            return self.PLAYER2
        return 0
    
    def is_valid_move(self, col: int) -> bool:
        if col < 0 or col >= self.COLS:
            return False
        return self.board[0][col] == self.EMPTY
    
    def get_valid_columns(self) -> List[int]:
        return [col for col in range(self.COLS) if self.is_valid_move(col)]
    
    def drop_piece(self, col: int, player: int) -> Optional[Tuple[int, int]]:
        if not self.is_valid_move(col):
            return None
        
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][col] == self.EMPTY:
                self.board[row][col] = player
                return (row, col)
        return None
    
    def make_move(self, user_id: int, col: int) -> Dict:
        if self.game_over:
            return {'error': 'Game is over'}
        
        if not self.first_player_decided:
            return {'error': 'Dice roll not completed'}
        
        player = self.get_player_number(user_id)
        if player == 0:
            return {'error': 'You are not in this game'}
        
        if player != self.current_player:
            return {'error': 'Not your turn'}
        
        if not self.is_valid_move(col):
            return {'error': 'Invalid column'}
        
        position = self.drop_piece(col, player)
        if not position:
            return {'error': 'Column is full'}
        
        if self._check_win(position[0], position[1], player):
            self.winner = player
            self.game_over = True
            return {
                'success': True,
                'position': position,
                'winner': user_id,
                'game_over': True
            }
        
        if self._check_draw():
            self.is_draw = True
            self.game_over = True
            return {
                'success': True,
                'position': position,
                'draw': True,
                'game_over': True
            }
        
        self.current_player = self.PLAYER2 if self.current_player == self.PLAYER1 else self.PLAYER1
        
        return {
            'success': True,
            'position': position,
            'next_player': self.get_current_player_id(),
            'game_over': False
        }
    
    def _check_win(self, row: int, col: int, player: int) -> bool:
        directions = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1)
        ]
        
        for dr, dc in directions:
            count = 1
            
            r, c = row + dr, col + dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 4:
                return True
        
        return False
    
    def _check_draw(self) -> bool:
        return all(self.board[0][col] != self.EMPTY for col in range(self.COLS))
    
    def render_board(self) -> str:
        lines = []
        for row in self.board:
            line = ""
            for cell in row:
                if cell == self.EMPTY:
                    line += self.EMPTY_EMOJI
                elif cell == self.PLAYER1:
                    line += self.PLAYER1_EMOJI
                else:
                    line += self.PLAYER2_EMOJI
            lines.append(line)
        
        lines.append("1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣")
        return "\n".join(lines)
    
    def get_game_state(self) -> Dict:
        return {
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'wager': self.wager,
            'current_player': self.current_player,
            'current_player_id': self.get_current_player_id() if self.first_player_decided else None,
            'winner': self.winner,
            'winner_id': self.player1_id if self.winner == self.PLAYER1 else (self.player2_id if self.winner == self.PLAYER2 else None),
            'game_over': self.game_over,
            'is_draw': self.is_draw,
            'board': self.render_board(),
            'valid_columns': self.get_valid_columns(),
            'player1_roll': self.player1_roll,
            'player2_roll': self.player2_roll,
            'first_player_decided': self.first_player_decided
        }
    
    def to_dict(self) -> Dict:
        return {
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'wager': self.wager,
            'board': self.board,
            'current_player': self.current_player,
            'winner': self.winner,
            'game_over': self.game_over,
            'is_draw': self.is_draw,
            'player1_roll': self.player1_roll,
            'player2_roll': self.player2_roll,
            'first_player_decided': self.first_player_decided
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Connect4Game':
        game = cls(data['player1_id'], data['player2_id'], data['wager'])
        game.board = data['board']
        game.current_player = data['current_player']
        game.winner = data['winner']
        game.game_over = data['game_over']
        game.is_draw = data['is_draw']
        game.player1_roll = data['player1_roll']
        game.player2_roll = data['player2_roll']
        game.first_player_decided = data['first_player_decided']
        return game
