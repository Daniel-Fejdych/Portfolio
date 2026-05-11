import pygame
import sys
import copy

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
BOARD_SIZE = 8
SQUARE_SIZE = WIDTH // BOARD_SIZE
FPS = 60

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (0, 255, 0, 128)
SELECTED_COLOR = (255, 255, 0, 128)
POSSIBLE_MOVE_COLOR = (0, 255, 0, 100)
CHECK_COLOR = (255, 0, 0, 100)

# Piece colors
WHITE = 'white'
BLACK = 'black'

# Piece types
PAWN = 'pawn'
KNIGHT = 'knight'
BISHOP = 'bishop'
ROOK = 'rook'
QUEEN = 'queen'
KING = 'king'

# Unicode mapping for display (optional, we use letters for clarity)
PIECE_SYMBOLS = {
    PAWN: 'P',
    KNIGHT: 'N',
    BISHOP: 'B',
    ROOK: 'R',
    QUEEN: 'Q',
    KING: 'K'
}


class Piece:
    """Represents a chess piece."""
    def __init__(self, piece_type, color, has_moved=False):
        self.type = piece_type
        self.color = color
        self.has_moved = has_moved

    def __repr__(self):
        return f"{self.color[0]}{self.type[0]}"

    def get_symbol(self):
        return PIECE_SYMBOLS[self.type]


class Board:
    """Represents the chess board and game state."""
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.turn = WHITE
        self.en_passant_target = None  # (row, col) where en passant capture is possible
        self.white_king_moved = False
        self.white_queen_rook_moved = False  # left rook (a1)
        self.white_king_rook_moved = False   # right rook (h1)
        self.black_king_moved = False
        self.black_queen_rook_moved = False  # left rook (a8)
        self.black_king_rook_moved = False   # right rook (h8)
        self.check = False
        self.game_over = False
        self.winner = None
        self.setup_board()

    def setup_board(self):
        """Initialize pieces in starting positions."""
        # Pawns
        for col in range(BOARD_SIZE):
            self.board[1][col] = Piece(PAWN, BLACK)
            self.board[6][col] = Piece(PAWN, WHITE)

        # Major pieces - Black
        self.board[0][0] = Piece(ROOK, BLACK)
        self.board[0][1] = Piece(KNIGHT, BLACK)
        self.board[0][2] = Piece(BISHOP, BLACK)
        self.board[0][3] = Piece(QUEEN, BLACK)
        self.board[0][4] = Piece(KING, BLACK)
        self.board[0][5] = Piece(BISHOP, BLACK)
        self.board[0][6] = Piece(KNIGHT, BLACK)
        self.board[0][7] = Piece(ROOK, BLACK)

        # Major pieces - White
        self.board[7][0] = Piece(ROOK, WHITE)
        self.board[7][1] = Piece(KNIGHT, WHITE)
        self.board[7][2] = Piece(BISHOP, WHITE)
        self.board[7][3] = Piece(QUEEN, WHITE)
        self.board[7][4] = Piece(KING, WHITE)
        self.board[7][5] = Piece(BISHOP, WHITE)
        self.board[7][6] = Piece(KNIGHT, WHITE)
        self.board[7][7] = Piece(ROOK, WHITE)

    def copy(self):
        """Create a deep copy of the board for move validation."""
        new_board = Board()
        new_board.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece:
                    new_board.board[r][c] = Piece(piece.type, piece.color, piece.has_moved)
        new_board.turn = self.turn
        new_board.en_passant_target = self.en_passant_target
        new_board.white_king_moved = self.white_king_moved
        new_board.white_queen_rook_moved = self.white_queen_rook_moved
        new_board.white_king_rook_moved = self.white_king_rook_moved
        new_board.black_king_moved = self.black_king_moved
        new_board.black_queen_rook_moved = self.black_queen_rook_moved
        new_board.black_king_rook_moved = self.black_king_rook_moved
        new_board.check = self.check
        new_board.game_over = self.game_over
        new_board.winner = self.winner
        return new_board

    def in_bounds(self, row, col):
        """Check if coordinates are inside the board."""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def is_square_attacked(self, row, col, color):
        """Check if a square is attacked by any piece of the given color."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece and piece.color == color:
                    if self.is_pseudo_legal_move((r, c), (row, col), piece):
                        return True
        return False

    def is_pseudo_legal_move(self, start, end, piece):
        """Check if a move is pseudo-legal (ignores check)."""
        start_row, start_col = start
        end_row, end_col = end
        target_piece = self.board[end_row][end_col]

        # Cannot capture own piece
        if target_piece and target_piece.color == piece.color:
            return False

        # Move logic based on piece type
        dr = end_row - start_row
        dc = end_col - start_col
        abs_dr = abs(dr)
        abs_dc = abs(dc)

        if piece.type == PAWN:
            direction = -1 if piece.color == WHITE else 1
            # One step forward
            if dr == direction and dc == 0 and not target_piece:
                return True
            # Two steps from starting position
            if (piece.color == WHITE and start_row == 6) or (piece.color == BLACK and start_row == 1):
                if dr == 2 * direction and dc == 0 and not target_piece and not self.board[start_row + direction][start_col]:
                    return True
            # Diagonal capture
            if dr == direction and abs_dc == 1 and target_piece:
                return True
            # En passant capture
            if self.en_passant_target == (end_row, end_col) and dr == direction and abs_dc == 1 and not target_piece:
                return True
            return False

        elif piece.type == KNIGHT:
            return (abs_dr, abs_dc) in [(2, 1), (1, 2)]

        elif piece.type == BISHOP:
            if abs_dr != abs_dc:
                return False
            step_r = 1 if dr > 0 else -1
            step_c = 1 if dc > 0 else -1
            r, c = start_row + step_r, start_col + step_c
            while (r, c) != (end_row, end_col):
                if self.board[r][c]:
                    return False
                r += step_r
                c += step_c
            return True

        elif piece.type == ROOK:
            if start_row != end_row and start_col != end_col:
                return False
            if start_row == end_row:
                step_c = 1 if dc > 0 else -1
                for c in range(start_col + step_c, end_col, step_c):
                    if self.board[start_row][c]:
                        return False
            else:
                step_r = 1 if dr > 0 else -1
                for r in range(start_row + step_r, end_row, step_r):
                    if self.board[r][start_col]:
                        return False
            return True

        elif piece.type == QUEEN:
            return (self.is_pseudo_legal_move(start, end, Piece(ROOK, piece.color)) or
                    self.is_pseudo_legal_move(start, end, Piece(BISHOP, piece.color)))

        elif piece.type == KING:
            # Normal king move
            if max(abs_dr, abs_dc) == 1:
                return True
            # Castling
            if not piece.has_moved and dr == 0 and abs_dc == 2:
                if dc == 2:  # King-side castling
                    rook_col = 7
                    if piece.color == WHITE:
                        if self.white_king_rook_moved:
                            return False
                        rook = self.board[7][rook_col]
                    else:
                        if self.black_king_rook_moved:
                            return False
                        rook = self.board[0][rook_col]
                    if not rook or rook.type != ROOK or rook.has_moved:
                        return False
                    # Check squares between are empty and not under attack
                    for c in range(start_col + 1, rook_col):
                        if self.board[start_row][c]:
                            return False
                    for c in range(start_col, rook_col + 1):
                        if self.is_square_attacked(start_row, c, piece.color):
                            return False
                    return True
                elif dc == -2:  # Queen-side castling
                    rook_col = 0
                    if piece.color == WHITE:
                        if self.white_queen_rook_moved:
                            return False
                        rook = self.board[7][rook_col]
                    else:
                        if self.black_queen_rook_moved:
                            return False
                        rook = self.board[0][rook_col]
                    if not rook or rook.type != ROOK or rook.has_moved:
                        return False
                    for c in range(rook_col + 1, start_col):
                        if self.board[start_row][c]:
                            return False
                    for c in range(rook_col + 1, start_col + 1):
                        if self.is_square_attacked(start_row, c, piece.color):
                            return False
                    return True
            return False
        return False

    def get_pseudo_legal_moves(self, start):
        """Get all pseudo-legal moves for a piece at the given position."""
        row, col = start
        piece = self.board[row][col]
        if not piece:
            return []
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.is_pseudo_legal_move((row, col), (r, c), piece):
                    moves.append((r, c))
        return moves

    def is_legal_move(self, start, end, color):
        """Check if a move is legal (does not leave own king in check)."""
        piece = self.board[start[0]][start[1]]
        if not piece or piece.color != color:
            return False
        if not self.is_pseudo_legal_move(start, end, piece):
            return False

        # Simulate move on a copy
        temp_board = self.copy()
        temp_board.execute_raw_move(start, end)
        king_pos = temp_board.find_king(color)
        return not temp_board.is_square_attacked(king_pos[0], king_pos[1], self.opposite_color(color))

    def get_legal_moves(self, start):
        """Get all legal moves for a piece at the given position."""
        piece = self.board[start[0]][start[1]]
        if not piece or piece.color != self.turn:
            return []
        moves = []
        for end in self.get_pseudo_legal_moves(start):
            if self.is_legal_move(start, end, piece.color):
                moves.append(end)
        return moves

    def find_king(self, color):
        """Find the position of the king of the given color."""
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece and piece.type == KING and piece.color == color:
                    return (r, c)
        return None

    def opposite_color(self, color):
        return BLACK if color == WHITE else WHITE

    def execute_raw_move(self, start, end):
        """Execute a move without any legality checks (used for simulation)."""
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        target = self.board[end_row][end_col]

        # Handle en passant capture
        if piece.type == PAWN and self.en_passant_target == (end_row, end_col):
            # Remove the captured pawn
            capture_row = start_row if piece.color == WHITE else end_row + 1
            self.board[capture_row][end_col] = None

        # Move piece
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        piece.has_moved = True

        # Handle pawn promotion
        if piece.type == PAWN:
            if (piece.color == WHITE and end_row == 0) or (piece.color == BLACK and end_row == 7):
                self.board[end_row][end_col] = Piece(QUEEN, piece.color, True)

        # Handle castling rook movement
        if piece.type == KING and abs(end_col - start_col) == 2:
            # King-side castling
            if end_col == 6:
                rook_start = (end_row, 7)
                rook_end = (end_row, 5)
            else:  # Queen-side
                rook_start = (end_row, 0)
                rook_end = (end_row, 3)
            rook = self.board[rook_start[0]][rook_start[1]]
            self.board[rook_end[0]][rook_end[1]] = rook
            self.board[rook_start[0]][rook_start[1]] = None
            rook.has_moved = True

        # Update castling rights
        if piece.type == KING:
            if piece.color == WHITE:
                self.white_king_moved = True
            else:
                self.black_king_moved = True
        if piece.type == ROOK:
            if start_row == 7 and start_col == 0:
                self.white_queen_rook_moved = True
            elif start_row == 7 and start_col == 7:
                self.white_king_rook_moved = True
            elif start_row == 0 and start_col == 0:
                self.black_queen_rook_moved = True
            elif start_row == 0 and start_col == 7:
                self.black_king_rook_moved = True

    def execute_move(self, start, end):
        """Execute a legal move, update turn, en passant target, and check game over."""
        piece = self.board[start[0]][start[1]]
        if not piece or piece.color != self.turn:
            return False
        if not self.is_legal_move(start, end, self.turn):
            return False

        # Clear previous en passant target
        self.en_passant_target = None

        # Set new en passant target if pawn moves two squares
        if piece.type == PAWN and abs(end[0] - start[0]) == 2:
            mid_row = (start[0] + end[0]) // 2
            self.en_passant_target = (mid_row, end[1])

        # Execute the move
        self.execute_raw_move(start, end)

        # Check if opponent's king is in check
        opponent = self.opposite_color(self.turn)
        opponent_king_pos = self.find_king(opponent)
        self.check = self.is_square_attacked(opponent_king_pos[0], opponent_king_pos[1], self.turn)

        # Switch turn
        self.turn = opponent

        # Check for checkmate or stalemate
        if self.is_checkmate():
            self.game_over = True
            self.winner = self.opposite_color(self.turn)
        elif self.is_stalemate():
            self.game_over = True
            self.winner = None

        return True

    def is_checkmate(self):
        """Check if the current player is in checkmate."""
        if not self.is_square_attacked(self.find_king(self.turn)[0], self.find_king(self.turn)[1], self.opposite_color(self.turn)):
            return False
        return self.get_all_legal_moves(self.turn) == []

    def is_stalemate(self):
        """Check if the current player is in stalemate."""
        if self.is_square_attacked(self.find_king(self.turn)[0], self.find_king(self.turn)[1], self.opposite_color(self.turn)):
            return False
        return self.get_all_legal_moves(self.turn) == []

    def get_all_legal_moves(self, color):
        """Get all legal moves for all pieces of the given color."""
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.board[r][c]
                if piece and piece.color == color:
                    for move in self.get_legal_moves((r, c)):
                        moves.append(((r, c), move))
        return moves


class ChessGame:
    """Main game class handling graphics and input."""
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Two-Player Chess")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        self.selected_square = None
        self.possible_moves = []
        self.running = True

    def draw_board(self):
        """Draw the chessboard squares."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

                # Highlight check
                if not self.board.game_over and self.board.check and self.board.turn == self.board.opposite_color(self.board.turn):
                    king_pos = self.board.find_king(self.board.turn)
                    if king_pos == (row, col):
                        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                        s.fill(CHECK_COLOR)
                        self.screen.blit(s, rect)

                # Highlight selected square
                if self.selected_square == (row, col):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(SELECTED_COLOR)
                    self.screen.blit(s, rect)

                # Highlight possible moves
                if (row, col) in self.possible_moves:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(POSSIBLE_MOVE_COLOR)
                    self.screen.blit(s, rect)

    def draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.board[row][col]
                if piece:
                    # Draw circle background
                    center = (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2)
                    radius = SQUARE_SIZE // 2 - 10
                    color = (220, 220, 220) if piece.color == WHITE else (60, 60, 60)
                    pygame.draw.circle(self.screen, color, center, radius)

                    # Draw piece symbol
                    text = self.font.render(piece.get_symbol(), True, (0, 0, 0))
                    text_rect = text.get_rect(center=center)
                    self.screen.blit(text, text_rect)

    def draw_ui(self):
        """Draw turn indicator and game status."""
        if not self.board.game_over:
            turn_text = f"Turn: {'White' if self.board.turn == WHITE else 'Black'}"
            if self.board.check:
                turn_text += " (CHECK!)"
            text_surface = self.small_font.render(turn_text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, HEIGHT - 40))
        else:
            if self.board.winner:
                winner_text = f"{'White' if self.board.winner == WHITE else 'Black'} wins by checkmate!"
            else:
                winner_text = "Stalemate!"
            text_surface = self.small_font.render(winner_text, True, (255, 255, 255))
            self.screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT - 40))

    def handle_click(self, pos):
        """Handle mouse clicks on the board."""
        if self.board.game_over:
            return

        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        if self.selected_square is None:
            # Select piece if it belongs to current player
            piece = self.board.board[row][col]
            if piece and piece.color == self.board.turn:
                self.selected_square = (row, col)
                self.possible_moves = self.board.get_legal_moves((row, col))
        else:
            # Attempt to move
            start = self.selected_square
            end = (row, col)
            if end in self.possible_moves:
                self.board.execute_move(start, end)
                self.selected_square = None
                self.possible_moves = []
            else:
                # Deselect if click elsewhere
                self.selected_square = None
                self.possible_moves = []

    def run(self):
        """Main game loop."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(pygame.mouse.get_pos())

            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_pieces()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = ChessGame()
    game.run()
