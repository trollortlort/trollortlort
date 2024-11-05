import sys
import re
import json
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

# Constants for game configuration
BOARD_FILE = "board.svg"
STATE_FILE = "game_state.json"
GRID_SIZE = 9  # 9x9 board
CELL_SIZE = 50
OFFSET = 25

class GoGame:
    def __init__(self):
        self.load_state()
        
    def load_state(self):
        """Load game state from JSON file or initialize new game"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                self.board = defaultdict(lambda: None, state['board'])
                self.current_player = state['current_player']
                self.move_history = state['move_history']
        else:
            self.board = defaultdict(lambda: None)
            self.current_player = 'black'
            self.move_history = []
            
    def save_state(self):
        """Save game state to JSON file"""
        state = {
            'board': dict(self.board),
            'current_player': self.current_player,
            'move_history': self.move_history
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)

    def get_coordinates(self, column, row):
        """Convert board position to SVG coordinates"""
        x = (ord(column.upper()) - ord('A')) * CELL_SIZE + OFFSET
        y = (row - 1) * CELL_SIZE + OFFSET
        return x, y

    def is_on_board(self, column, row):
        """Check if position is within board boundaries"""
        return 'A' <= column.upper() < chr(ord('A') + GRID_SIZE) and 1 <= row <= GRID_SIZE

    def get_neighbors(self, pos):
        """Get all adjacent positions"""
        column, row = pos
        neighbors = []
        for dc, dr in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_col = chr(ord(column) + dc)
            new_row = row + dr
            if self.is_on_board(new_col, new_row):
                neighbors.append((new_col, new_row))
        return neighbors

    def get_group_liberties(self, pos, visited=None):
        """Count liberties of a group of stones"""
        if visited is None:
            visited = set()
            
        column, row = pos
        color = self.board[(column, row)]
        if not color:
            return 0
            
        visited.add(pos)
        liberties = set()
        
        for next_pos in self.get_neighbors(pos):
            if next_pos in visited:
                continue
                
            next_col, next_row = next_pos
            next_color = self.board[(next_col, next_row)]
            
            if next_color is None:
                liberties.add(next_pos)
            elif next_color == color:
                visited.add(next_pos)
                group_liberties = self.get_group_liberties(next_pos, visited)
                liberties.update(group_liberties)
                
        return liberties

    def remove_captured_stones(self, last_move):
        """Remove any stones captured by the last move"""
        captured = []
        last_col, last_row = last_move
        for pos in self.get_neighbors((last_col, last_row)):
            col, row = pos
            if self.board[(col, row)] == ('white' if self.current_player == 'black' else 'black'):
                if not self.get_group_liberties(pos):
                    self.remove_group(pos)
                    captured.append(pos)
        return captured

    def remove_group(self, pos):
        """Remove a group of stones from the board"""
        color = self.board[pos]
        if not color:
            return
            
        self.board[pos] = None
        for next_pos in self.get_neighbors(pos):
            if self.board[next_pos] == color:
                self.remove_group(next_pos)

    def is_valid_move(self, column, row):
        """Check if a move is valid according to Go rules"""
        if self.board[(column, row)] is not None:
            return False
            
        # Temporarily place the stone
        self.board[(column, row)] = self.current_player
        
        # Check for suicide rule
        if not self.get_group_liberties((column, row)):
            # Check if this move captures any opponent stones
            would_capture = False
            for pos in self.get_neighbors((column, row)):
                col, row = pos
                if self.board[(col, row)] == ('white' if self.current_player == 'black' else 'black'):
                    if not self.get_group_liberties(pos):
                        would_capture = True
                        break
            
            # If no captures and no liberties, move is suicide
            if not would_capture:
                self.board[(column, row)] = None
                return False
                
        # Remove temporary stone
        self.board[(column, row)] = None
        return True

    def update_svg(self):
        """Update the SVG board with current game state"""
        tree = ET.parse(BOARD_FILE)
        root = tree.getroot()
        
        # Remove existing stones
        for stone in root.findall('.//circle'):
            root.remove(stone)
            
        # Add current stones
        for (column, row), color in self.board.items():
            if color:
                x, y = self.get_coordinates(column, row)
                ET.SubElement(root, 'circle', {
                    'cx': str(x),
                    'cy': str(y),
                    'r': '20',
                    'fill': color,
                    'stroke': 'black',
                    'stroke-width': '1'
                })
                
        tree.write(BOARD_FILE)

    def make_move(self, column, row):
        """Process a move and update game state"""
        if not self.is_on_board(column, row):
            return False, "Move is outside the board"
            
        if not self.is_valid_move(column, row):
            return False, "Invalid move according to Go rules"
            
        # Place the stone
        self.board[(column, row)] = self.current_player
        
        # Remove any captured stones
        captured = self.remove_captured_stones((column, row))
        
        # Record the move
        self.move_history.append({
            'position': (column, row),
            'color': self.current_player,
            'captured': captured
        })
        
        # Switch players
        self.current_player = 'white' if self.current_player == 'black' else 'black'
        
        # Update the board visualization and save state
        self.update_svg()
        self.save_state()
        
        return True, f"Move placed at {column}{row}"

def main():
    # Extract the move from the comment
    comment_text = sys.argv[1].lower()
    move_match = re.match(r"move\s+([a-i])([1-9])", comment_text)
    
    if not move_match:
        print("Invalid move format. Please use 'move <column><row>' (e.g., 'move C5')")
        return
        
    column, row = move_match.groups()
    row = int(row)
    
    # Initialize game and process move
    game = GoGame()
    success, message = game.make_move(column.upper(), row)
    print(message)

if __name__ == "__main__":
    main()
