from dataclasses import dataclass, field
from math import cos, sin, tau

import pygame
import sys


# ----------------------------
# Configuration
# ----------------------------
# The board currently uses an 8x8 layout.
# If a larger board is desired, piece starting
# positions must also be updated.
BOARD_SIZE = 8
GENERAL_SIZE = 1
SQUARE_SIZE = 100 * GENERAL_SIZE

BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
MENU_WIDTH = 220

WINDOW_WIDTH = BOARD_WIDTH + MENU_WIDTH
WINDOW_HEIGHT = BOARD_WIDTH

LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)

MENU_BG = (40, 40, 40)
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER = (100, 100, 100)
MENU_TEXT_COLOR = (255, 255, 255)
MENU_FONT_SIZE = int(30 * GENERAL_SIZE)
PIECE_FONT_SIZE = int(20 * GENERAL_SIZE)
FONT_NAME = "Tahoma"

class Game:
    def __init__(self):
        self.players = None
        self.pieces = None

        self.selected_piece = None
        self.allowed_moves = None

        self.screen = None
        self.buttons = []

@dataclass(frozen=True)
class Color:
    """Represents a color."""
    red: int = 0
    green: int = 0
    blue: int = 0

    def get_rgb_color(self) -> tuple[int, int, int]:
        """Returns the rgb color as a tuple."""
        return self.red, self.green, self.blue


@dataclass(frozen=True)
class Player:
    name: str
    color: Color

    def get_rgb_color(self):
        return self.color.get_rgb_color()

@dataclass(frozen=True)
class PlayerGroup:
    """Represents a group of players."""
    players: list[Player] = field(default_factory=list)

    def add_player(self, player: Player) -> None:
        """Adds a player to the group.
        :type player: Player
        """
        self.players.append(player)

# repeat=0 means a single-step move.
# Larger values allow sliding multiple squares
# in the same direction (rook, bishop, queen).
@dataclass(frozen=True)
class MovePattern:
    """Represents a piece move pattern."""
    dx: int
    dy: int
    repeat: int = 0  # How many more times the piece can move in this direction


@dataclass(frozen=True)
class PieceType:
    """Represents a piece type."""
    name: str
    moves: tuple[MovePattern, ...]


class Piece:
    """Represents a piece."""

    def __init__(self, piece_type: PieceType, player: Player, x: int, y: int):
        """
        :type piece_type: PieceType
        :type player: Player
        :type x: int
        :type y: int
        """
        self.piece_type = piece_type
        self.player = player
        self.x = x
        self.y = y

    # Checks whether a target coordinate matches one
    # of the piece's movement patterns.
    # This function only validates movement geometry,
    # not game rules such as blocking pieces.
    def can_move_to(self, x: int, y: int) -> bool:
        """Returns if the piece can be moved to the given coordinates.
        :type x: int
        :type y: int
        """
        for move in self.piece_type.moves:
            for step in range(1, move.repeat + 2):
                if (
                        self.x + step * move.dx == x
                        and self.y + step * move.dy == y
                ):
                    return True
        return False

    def get_player(self) -> Player:
        """Returns the player of the piece."""
        return self.player

    def belongs_to_player(self, player: Player) -> bool:
        """Returns if the piece belongs to the given player.
        :type player: Player
        """
        return self.player == player

    def get_color(self) -> Color:
        """Returns the color of the piece."""
        return self.player.color

@dataclass(frozen=True)
class PieceGroup:
    """Represents all pieces."""
    piece_list: list = field(default_factory=list)

    def add_piece(self, piece: Piece) -> None:
        """Adds a piece to the group.
        :type piece: Piece
        """
        self.piece_list.append(piece)

    def remove_piece(self, piece: Piece) -> None:
        """Removes a piece from the group.
        :type piece: Piece
        """
        self.piece_list.remove(piece)

    def get_num_pieces(self) -> int:
        """Returns the number of pieces in the group."""
        return len(self.piece_list)

    def get_num_pieces_of_player(self, player: Player) -> int:
        """Returns the number of pieces in the group belonging to the given player.
        :type player: Player
        """
        return len([piece for piece in self.piece_list if piece.belongs_to_player(player)])

    def render(self, screen: pygame.Surface) -> None:
        """Renders the group.
        :type screen: pygame.Surface
        """
        for piece in self.piece_list:
            center_x = piece.x * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = piece.y * SQUARE_SIZE + SQUARE_SIZE // 2

            fill_color = piece.player.get_rgb_color()
            outline_color = tuple(v // 2 for v in piece.player.get_rgb_color())
            background_color = tuple(255 - v for v in piece.player.get_rgb_color())

            # Render the piece by drawing several nested hexagons to create a
            # stylized game piece appearance.
            for scale, color, width in (tuple((0.08 * m, fill_color, 4) for m in range(6)) + ((0.48, outline_color, 3),)):
                pygame.draw.lines(
                    screen,
                    color,
                    True,
                    [
                        (cos(i * tau / 6) * SQUARE_SIZE * scale + center_x,
                         sin(i * tau / 6) * SQUARE_SIZE * scale + center_y)
                        for i in range(6)
                    ],
                    width
                )
            pygame.draw.ellipse(screen, background_color,(center_x - 0.4 * SQUARE_SIZE, center_y-0.12 * SQUARE_SIZE,
                                                          0.8 * SQUARE_SIZE, 0.24 * SQUARE_SIZE))
            # Render the piece name
            label = PIECE_FONT.render(
                piece.piece_type.name.upper(),
                True,
                outline_color
            )

            label_rect = label.get_rect(
                center=(center_x, center_y)
            )

            screen.blit(label, label_rect)



# Helper functions
def get_piece_at_position(x: int, y: int, game: Game) -> Piece | None:
    """
    :type x: int
    :type y: int
    :type game: Game
    """
    for piece in game.pieces.piece_list:
        if piece.x == x and piece.y == y:
            return piece
    return None

# Generates all board coordinates that match the
# movement pattern of the selected piece.
# Does not currently check for collisions,
# captures, or board occupancy.
def get_allowed_moves(piece: Piece):
    """
    :type piece: Piece
    """
    moves = []

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if piece.can_move_to(x, y):
                moves.append((x, y))

    return moves



# ----------------------------
# Generic Button Callback
# ----------------------------
def generic_action(button_name):
    """
    :type button_name: str
    """
    print(f"Button clicked: {button_name}")
    if button_name == "Exit":
        pygame.quit()
        sys.exit()


# ----------------------------
# Button Class
# ----------------------------
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback

    def draw(self, surface):
        """
        :type surface: pygame.Surface
        """
        mouse_pos = pygame.mouse.get_pos()

        color = BUTTON_COLOR
        if self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER

        pygame.draw.rect(surface, color, self.rect, border_radius=6)

        text_surface = MENU_FONT.render(self.text, True, MENU_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)

        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        """
        :type event: pygame.event.Event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.callback(self.text)


# ----------------------------
# Chess Board Drawing
# ----------------------------
def draw_chess_board(surface):
    """
    :type surface: pygame.Surface
    """
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):

            pygame.draw.rect(
                surface,
                LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE,
                (
                    col * SQUARE_SIZE,
                    row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                ),
            )

def setup_menu(game: Game):
    """
    :type game: Game
    """
    # ----------------------------
    # Create Menu Buttons
    # ----------------------------

    game.buttons = []

    button_names = [
        "New Game",
        "Load Game",
        "Save Game",
        "Undo Move",
        "Settings",
        "Exit",
    ]

    start_x = BOARD_WIDTH + 20
    start_y = 30
    button_width = MENU_WIDTH - 40
    button_height = 50
    spacing = 15

    for i, name in enumerate(button_names):
        game.buttons.append(
            Button(
                start_x,
                start_y + i * (button_height + spacing),
                button_width,
                button_height,
                name,
                generic_action,
            )
        )

def setup(game: Game) -> None:
    setup_menu(game)

    # Selection state setup
    game.selected_piece = None
    game.allowed_moves = []

    # Create two players with different colors
    player1 = Player("Alice", Color(red=255, green=0, blue=0))  # Red
    player2 = Player("Bob", Color(red=0, green=0, blue=255))  # Blue

    # Create the player group
    game.players = PlayerGroup()
    game.players.add_player(player1)
    game.players.add_player(player2)

    # Define the possible moves
    pawn_moves = ((0, 1), (0, -1)) # temporarily allow pawns to move backwards for both players to be able to work
    orthogonal = ((0, 1), (1, 0), (0, -1), (-1, 0))
    diagonal = ((1, 1), (-1, -1), (1, -1), (-1, 1))
    king_moves = orthogonal + diagonal
    knight_vectors = ((1, 2), (2, 1), (-1, -2), (-2, -1),
                      (-1, 2), (-2, 1), (1, -2), (2, -1))

    # Converts movement vectors into MovePattern objects
    # with a common repeat count.
    def build_move_patterns(vectors: tuple[tuple[int, int], ...], repeat: int):
        """
        :type vectors: tuple[tuple[int, int], ...]
        :type repeat: int
        """
        return tuple(MovePattern(dx=dx, dy=dy, repeat=repeat) for dx, dy in vectors)


    pawn_type = PieceType("Pawn", build_move_patterns(pawn_moves, 0))
    queen_type = PieceType("Queen", build_move_patterns(king_moves,7))
    bishop_type = PieceType("Bishop", build_move_patterns(diagonal, 7))
    rook_type = PieceType("Rook", build_move_patterns(orthogonal, 7))
    king_type = PieceType("King", build_move_patterns(king_moves, 0))
    knight_type = PieceType("Knight", build_move_patterns(knight_vectors, 0))




    # Create the piece group
    game.pieces = PieceGroup()

    # Pawns
    for y, player in ((1, player1), (6, player2)):
        for x in range(BOARD_SIZE):
            game.pieces.add_piece(
                Piece(pawn_type, player, x, y)
            )


    # This section creates symmetrical piece placement for both players.
    # Each tuple contains the columns where that piece type starts.
    starting_positions = {
        rook_type: (0, 7),
        knight_type: (1, 6),
        bishop_type: (2, 5),
        king_type: (3,),
        queen_type: (4,),
    }
    # Other pieces
    for y, player in ((0, player1), (7, player2)):
        for piece_type, columns in starting_positions.items():
            for x in columns:
                game.pieces.add_piece(
                    Piece(piece_type, player, x, y)
                )

    # Set up the pygame screen
    game.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess Board with Menu")

def main_loop(game: Game):
    # ----------------------------
    # Main Loop
    # ----------------------------
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            for button in game.buttons:
                button.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos

                # Ignore clicks that occur inside the menu panel.
                if mouse_x < BOARD_WIDTH:
                    board_column = mouse_x // SQUARE_SIZE
                    board_row = mouse_y // SQUARE_SIZE

                    # If a piece is selected, attempt move
                    if game.selected_piece:
                        # Move the selected piece if the destination
                        # is one of its allowed moves.
                        # Capturing and collision detection are not yet implemented.
                        if (board_column, board_row) in game.allowed_moves:
                            game.selected_piece.x = board_column
                            game.selected_piece.y = board_row

                        # Deselect regardless of whether move succeeded
                        game.selected_piece = None
                        game.allowed_moves = []

                    else:
                        piece = get_piece_at_position(board_column, board_row, game)

                        if piece:
                            game.selected_piece = piece
                            game.allowed_moves = get_allowed_moves(piece)

        # Background
        game.screen.fill((0, 0, 0))

        # Chess board
        draw_chess_board(game.screen)

        # Render pieces
        game.pieces.render(game.screen)
        if game.selected_piece:
            for mouse_x, mouse_y in game.allowed_moves:
                center = (
                    mouse_x * SQUARE_SIZE + SQUARE_SIZE // 2,
                    mouse_y * SQUARE_SIZE + SQUARE_SIZE // 2,
                )

                # Draw green markers on all legal destinations
                # for the currently selected piece.
                pygame.draw.circle(
                    game.screen,
                    (0, 255, 0),
                    center,
                    SQUARE_SIZE // 8,
                )
            # Highlight the selected piece with a yellow border.
            pygame.draw.rect(
                game.screen,
                (255, 255, 0),
                (
                    game.selected_piece.x * SQUARE_SIZE,
                    game.selected_piece.y * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                ),
                4,
            )
        # Menu panel
        pygame.draw.rect(
            game.screen,
            MENU_BG,
            (BOARD_WIDTH, 0, MENU_WIDTH, WINDOW_HEIGHT),
        )

        # Buttons
        for button in game.buttons:
            button.draw(game.screen)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    pygame.init()
    MENU_FONT = pygame.font.SysFont(FONT_NAME, MENU_FONT_SIZE)
    PIECE_FONT = pygame.font.SysFont(FONT_NAME, PIECE_FONT_SIZE)

    g = Game()
    setup(g)
    main_loop(g)
