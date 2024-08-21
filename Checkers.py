import copy
import pygame
import math
import random
import time

# Define colors
COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "green": (0, 255, 0),
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "trans": (1, 2, 3)
}

# Game Constants
BOARD_WIDTH = 600
BOARD_HEIGHT = 600
GRID_ROWS = 8
GRID_COLS = 8
TOKEN_RADIUS = BOARD_WIDTH // GRID_ROWS // 2

class CheckersGame:
    """Handles the game state and logic for Checkers."""

    def __init__(self):
        """
        Initialize the game, setting up the board and determining the starting player.
        """
        self.status = 'ongoing'
        self.current_turn = 0 # Can be randomized with random.randrange(2)
        self.players = ['r', 'b']
        self.tokens_remaining = [12, 12]
        self.king_count = [0, 0]
        self.selected_piece = None
        self.is_jumping = False
        pygame.display.set_caption(f"{self.players[self.current_turn % 2]}'s turn")
        self.board = [
            ['r', '-', 'r', '-', 'r', '-', 'r', '-'],
            ['-', 'r', '-', 'r', '-', 'r', '-', 'r'],
            ['r', '-', 'r', '-', 'r', '-', 'r', '-'],
            ['-', '-', '-', '-', '-', '-', '-', '-'],
            ['-', '-', '-', '-', '-', '-', '-', '-'],
            ['-', 'b', '-', 'b', '-', 'b', '-', 'b'],
            ['b', '-', 'b', '-', 'b', '-', 'b', '-'],
            ['-', 'b', '-', 'b', '-', 'b', '-', 'b']
        ]

    def handle_click(self, mouse_pos):
        """
        Respond to a mouse click during the game: either select a piece or move it.
        """
        if self.status == 'ongoing':
            clicked_square = self.get_row_col_from_click(mouse_pos)
            current_player = self.players[self.current_turn % 2]

            if self.selected_piece:
                move_possible, jumped_piece = self.is_move_valid(current_player, self.selected_piece, clicked_square)
                if move_possible:
                    winner = self.move_piece(current_player, self.selected_piece, clicked_square, jumped_piece)
                    self.update_caption(winner)
                elif clicked_square == self.selected_piece:
                    self.deselect_piece()
                else:
                    print('Invalid move')
            else:
                if self.board[clicked_square[0]][clicked_square[1]].lower() == current_player:
                    self.selected_piece = clicked_square
        elif self.status == 'over':
            self.reset_game()

    def is_move_valid(self, player, from_square, to_square):
        """
        Determine if a move from one square to another is allowed for the current player.
        """
        from_row, from_col = from_square
        to_row, to_col = to_square
        piece = self.board[from_row][from_col]
        if self.board[to_row][to_col] != '-':
            return False, None

        if self.is_regular_move(player, from_row, to_row, from_col, to_col, piece):
            return True, None

        if self.is_jump_move(player, from_row, to_row, from_col, to_col, piece):
            jumped_row = (to_row + from_row) // 2
            jumped_col = (to_col + from_col) // 2
            if self.is_opponent_piece(player, jumped_row, jumped_col):
                return True, [jumped_row, jumped_col]

        return False, None

    def is_regular_move(self, player, from_row, to_row, from_col, to_col, piece):
        return (
            abs(from_row - to_row) == 1 and
            abs(from_col - to_col) == 1 and
            (piece.isupper() or (player == 'r' and to_row > from_row) or (player == 'b' and to_row < from_row)) and
            not self.is_jumping
        )

    def is_jump_move(self, player, from_row, to_row, from_col, to_col, piece):
        return (
            abs(from_row - to_row) == 2 and
            abs(from_col - to_col) == 2 and
            (piece.isupper() or (player == 'r' and to_row > from_row) or (player == 'b' and to_row < from_row))
        )

    def is_opponent_piece(self, player, row, col):
        return self.board[row][col].lower() not in [player, '-']

    def get_all_player_pieces(self, player):
        pieces = []
        for row_index, row in enumerate(self.board):
            for col_index, piece in enumerate(row):
                if piece.lower() == player:
                    pieces.append((row_index, col_index))
        return pieces

    def get_valid_moves_for_player(self, player):
        moves = []
        for piece_pos in self.get_all_player_pieces(player):
            moves.extend(self.get_valid_moves_for_piece(player, piece_pos))
        return moves

    def get_valid_moves_for_piece(self, player, piece_pos):
        moves = []
        piece_row, piece_col = piece_pos
        for row_offset, col_offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
            target_square = (piece_row + row_offset, piece_col + col_offset)
            if self.is_square_on_board(target_square):
                move_possible, jumped_pieces = self.is_move_valid(player, piece_pos, target_square)
                if move_possible:
                    moves.append([piece_pos, target_square, jumped_pieces])

        return moves

    def is_square_on_board(self, square):
        return 0 <= square[0] < GRID_ROWS and 0 <= square[1] < GRID_COLS

    def move_piece(self, player, from_square, to_square, jumped_square, is_auto=False):
        """
        Move a selected piece to a new square and check if the game has been won.
        """
        from_row, from_col = from_square
        to_row, to_col = to_square
        piece = self.board[from_row][from_col]
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = '-'

        if self.promote_to_king(player, to_row):
            self.board[to_row][to_col] = piece.upper()
            self.king_count[player == 'b'] += 1

        if is_auto:
            self.handle_auto_move(jumped_square, player)
        elif jumped_square:
            self.handle_jump_move(jumped_square, player, to_row, to_col)
        else:
            self.end_turn()

        return self.check_for_winner()

    def promote_to_king(self, player, row):
        return (player == 'r' and row == GRID_ROWS - 1) or (player == 'b' and row == 0)

    def handle_auto_move(self, jumped_square, player):
        if jumped_square:
            for square in jumped_square:
                self.board[square[0]][square[1]] = '-'
                self.tokens_remaining[player == self.players[0]] -= 1
        self.end_turn()

    def handle_jump_move(self, jumped_square, player, to_row, to_col):
        self.board[jumped_square[0]][jumped_square[1]] = '-'
        self.selected_piece = (to_row, to_col)
        self.is_jumping = True
        self.tokens_remaining[player == self.players[0]] -= 1

    def deselect_piece(self):
        self.selected_piece = None
        if self.is_jumping:
            self.is_jumping = False
            self.end_turn()

    def end_turn(self):
        self.current_turn += 1
        pygame.display.set_caption(f"{self.players[self.current_turn % 2]}'s turn")

    def check_for_winner(self):
        """
        Check if the game is over due to one player having no valid moves or no pieces left.
        """
        if not self.get_valid_moves_for_player(self.players[self.current_turn % 2]):
            return self.players[(self.current_turn + 1) % 2]
        if self.tokens_remaining[0] == 0:
            return self.players[1]
        if self.tokens_remaining[1] == 0:
            return self.players[0]
        if self.tokens_remaining[0] == 1 and self.tokens_remaining[1] == 1:
            return 'draw'
        return None

    def draw_board(self):
        """
        Render the game board and the pieces on it.
        """
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if (row + col) % 2 == 1:
                    pygame.draw.rect(screen, COLORS['white'], (col * BOARD_WIDTH / GRID_COLS, row * BOARD_HEIGHT / GRID_ROWS, BOARD_WIDTH / GRID_COLS, BOARD_HEIGHT / GRID_ROWS))

        for row, row_data in enumerate(self.board):
            for col, cell in enumerate(row_data):
                if cell != '-':
                    self.draw_piece(row, col, cell)

    def draw_piece(self, row, col, piece):
        color = COLORS['red'] if piece.lower() == 'r' else COLORS['blue']
        pygame.draw.circle(screen, color, (int(col * BOARD_WIDTH / GRID_COLS + BOARD_WIDTH / GRID_COLS / 2), int(row * BOARD_HEIGHT / GRID_ROWS + BOARD_HEIGHT / GRID_ROWS / 2)), TOKEN_RADIUS)
        if piece.isupper():
            pygame.draw.circle(screen, COLORS['yellow'], (int(col * BOARD_WIDTH / GRID_COLS + BOARD_WIDTH / GRID_COLS / 2), int(row * BOARD_HEIGHT / GRID_ROWS + BOARD_HEIGHT / GRID_ROWS / 2)), TOKEN_RADIUS // 2)

    def get_row_col_from_click(self, pos):
        return int(pos[1] // (BOARD_HEIGHT / GRID_ROWS)), int(pos[0] // (BOARD_WIDTH / GRID_COLS))

    def reset_game(self):
        """Reset the game to the initial state."""
        self.__init__()

    def update_caption(self, winner):
        if winner:
            self.status = 'over'
            pygame.display.set_caption(f"{winner} wins")
        else:
            self.end_turn()

# Initialize pygame and set up the display
pygame.init()
screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))

# Main game loop
game = CheckersGame()
running = True

while running:
    game.draw_board()
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            game.handle_click(pygame.mouse.get_pos())

pygame.quit()
