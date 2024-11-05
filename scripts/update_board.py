import sys
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# Constants for game configuration
BOARD_FILE = "board.svg"
GRID_SIZE = 9  # 9x9 board
CELL_SIZE = 50
OFFSET = 25

# Placeholder game state
game_board = defaultdict(lambda: None)  # Maps positions to 'black', 'white', or None

# Function to get board coordinates
def get_coordinates(column, row):
    x = (ord(column.upper()) - ord('A')) * CELL_SIZE + OFFSET
    y = (row - 1) * CELL_SIZE + OFFSET
    return x, y

# Function to add a stone to the SVG
def add_stone(svg_root, x, y, color):
    ET.SubElement(svg_root, 'circle', cx=str(x), cy=str(y), r="20", fill=color)

# Function to check if a position is on the board
def is_on_board(column, row):
    return 'A' <= column.upper() < chr(ord('A') + GRID_SIZE) and 1 <= row <= GRID_SIZE

# Function to validate moves
def is_valid_move(column, row, color):
    if game_board[(column, row)] is not None:
        print(f"Invalid move: Position ({column}, {row}) is already occupied.")
        return False
    return True

# Function to check for captures (simplified logic for this outline)
def check_for_captures():
    # Placeholder for capture logic; would involve checking liberties of stones
    pass

# Function to update the board based on a single move
def update_board(move):
    column, row, color = move
    if is_on_board(column, row) and is_valid_move(column, row, color):
        tree = ET.parse(BOARD_FILE)
        root = tree.getroot()
        
        x, y = get_coordinates(column, row)
        add_stone(root, x, y, color)
        game_board[(column, row)] = color
        check_for_captures()  # Check for any captured stones

        tree.write(BOARD_FILE)
        print(f"Move placed: {color} stone at ({column}, {row})")
    else:
        print("Move is not valid.")

# Main entry point when executed
if __name__ == "__main__":
    # Extract the move from the comment passed by GitHub Action
    comment_text = sys.argv[1]
    move_match = re.match(r"move\s+([A-I])([1-9])", comment_text, re.IGNORECASE)
    
    if move_match:
        column, row = move_match.groups()
        row = int(row)
        
        # Determine player color (alternates with each move)
        last_move_color = 'white' if any(game_board.values()) else 'black'
        color = 'black' if last_move_color == 'white' else 'white'
        
        # Call update_board with the new move
        update_board((column.upper(), row, color))
    else:
        print("No valid move detected in comment.")
