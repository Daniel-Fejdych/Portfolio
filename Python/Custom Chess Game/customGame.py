from dataclasses import dataclass
from math import cos, sin, tau

import pygame
import sys


@dataclass(frozen=True)
class HexColor:
    """Represents a color."""
    red: int = 0
    green: int = 0
    blue: int = 0


class Player:
    """Represents a player in the game."""

    def __init__(self, name: str, color: HexColor):
        self.name = name
        self.color = color

    def get_color(self) -> HexColor:
        """Returns the color of the player."""
        return self.color


class PlayerGroup:
    """Represents a group of players."""

    def __init__(self):
        self.players = []

    def add_player(self, player: Player) -> None:
        """Adds a player to the group."""
        self.players.append(player)


@dataclass(frozen=True)
class MP:
    """Represents a piece move pattern."""
    dx: int
    dy: int
    repeat: int = 0  # How many more times the piece can move in this direction


@dataclass(frozen=True)
class PieceType:
    """Represents a piece type."""
    name: str
    moves: tuple[MP, ...]


class Piece:
    """Represents a piece."""

    def __init__(self, p_type: PieceType, player: Player, x, y):
        self.p_type = p_type
        self.player = player
        self.x = x
        self.y = y

    def can_move_to(self, x: int, y: int) -> bool:
        """Returns if the piece can be moved to the given coordinates."""
        for move in self.p_type.moves:
            try:
                for rep in range(1, move.repeat + 2):
                    if self.x + rep * move.dx == x and self.y + rep * move.dy == y:
                        return True
            except TypeError:
                if self.x + move.dx == x and self.y + move.dy == y:
                    return True
        return False

    def get_player(self) -> Player:
        """Returns the player of the piece."""
        return self.player

    def belongs_to_player(self, player: Player) -> bool:
        """Returns if the piece belongs to the given player."""
        return self.player == player

    def get_color(self) -> HexColor:
        """Returns the color of the piece."""
        return self.player.get_color()


class PieceGroup:
    """Represents all pieces."""

    def __init__(self):
        self.pArray = []

    def add_piece(self, piece: Piece) -> None:
        """Adds a piece to the group."""
        self.pArray.append(piece)

    def remove_piece(self, piece: Piece) -> None:
        """Removes a piece from the group."""
        self.pArray.remove(piece)

    def get_num_pieces(self) -> int:
        """Returns the number of pieces in the group."""
        return len(self.pArray)

    def get_num_pieces_of_player(self, player: Player) -> int:
        """Returns the number of pieces in the group belonging to the given player."""
        return len(list(filter(
            lambda piece: piece.belongs_to_player(player), self.pArray)))

    def render(self, screen: pygame.Surface) -> None:
        """Renders the group."""
        for piece in self.pArray:
            center_x = piece.x * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = piece.y * SQUARE_SIZE + SQUARE_SIZE // 2

            c = piece.player.get_color()
            col = (c.red, c.green, c.blue)
            col_dark = tuple(v // 2 for v in (c.red, c.green, c.blue))

            radius = SQUARE_SIZE // 3
            # Render the piece
            for scale, color in (tuple((0.2 * m + 0.1, col) for m in range(7)) + ((1.5, col_dark),)):
                pygame.draw.lines(
                    screen,
                    color,
                    True,
                    [
                        (cos(i * tau / 6) * radius * scale + center_x,
                         sin(i * tau / 6) * radius * scale + center_y)
                        for i in range(6)
                    ],
                )

            # Render the piece name
            label = font.render(
                piece.p_type.name.upper(),
                True,
                col_dark
            )

            label_rect = label.get_rect(
                center=(center_x, center_y)
            )

            screen.blit(label, label_rect)


# Create two players with different colors
player1 = Player("Alice", HexColor(red=255, green=0, blue=0))  # Red
player2 = Player("Bob", HexColor(red=0, green=0, blue=255))  # Blue

# Create the player group
players = PlayerGroup()
players.add_player(player1)
players.add_player(player2)

# Define the possible moves
PAWN_MOVES = ((0, 1),)
ORTHOGONAL = ((0, 1), (1, 0), (0, -1), (-1, 0))
DIAGONAL = ((1, 1), (-1, -1), (1, -1), (-1, 1))
KING_MOVES = ORTHOGONAL + DIAGONAL
KNIGHT_VECTORS = ((1, 2), (2, 1), (-1, -2), (-2, -1),
                  (-1, 2), (-2, 1), (1, -2), (2, -1))


def make_moves(vectors, repeat=None):
    return tuple(MP(dx=dx, dy=dy, repeat=repeat) for dx, dy in vectors)


pawn_type = PieceType("Pawn", make_moves(PAWN_MOVES))
queen_type = PieceType("Queen", make_moves(KING_MOVES, repeat=8))
bishop_type = PieceType("Bishop", make_moves(DIAGONAL, repeat=8))
rook_type = PieceType("Rook", make_moves(ORTHOGONAL, repeat=8))
king_type = PieceType("King", make_moves(KING_MOVES))
knight_type = PieceType("Knight", make_moves(KNIGHT_VECTORS))

# Create the piece group
pieces = PieceGroup()

# Pawns
for y, player in ((1, player1), (6, player2)):
    for x in range(10):
        pieces.add_piece(
            Piece(p_type=pawn_type, player=player, x=x, y=y)
        )

# Other pieces
starting_positions = {
    rook_type: (0, 7),
    knight_type: (1, 6),
    bishop_type: (2, 5),
    king_type: (3,),
    queen_type: (4,),
}
for y, player in ((0, player1), (7, player2)):
    for p_type, xs in starting_positions.items():
        for x in xs:
            pieces.add_piece(
                Piece(p_type=p_type, player=player, x=x, y=y)
            )

# Verify
print("Total players:", len(players.players))
print("Total pieces:", pieces.get_num_pieces())
print("Alice pieces:", pieces.get_num_pieces_of_player(player1))
print("Bob pieces:", pieces.get_num_pieces_of_player(player2))

# Helper functions
def get_piece_at(x, y):
    for piece in pieces.pArray:
        if piece.x == x and piece.y == y:
            return piece
    return None


def get_allowed_moves(piece):
    moves = []

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if piece.can_move_to(x, y):
                moves.append((x, y))

    return moves


# Selection state setup
selected_piece = None
allowed_moves = []


# ----------------------------
# Configuration
# ----------------------------
BOARD_SIZE = 8
SQUARE_SIZE = 100

BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
MENU_WIDTH = 220

WINDOW_WIDTH = BOARD_WIDTH + MENU_WIDTH
WINDOW_HEIGHT = BOARD_WIDTH

LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)

MENU_BG = (40, 40, 40)
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER = (100, 100, 100)
TEXT_COLOR = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chess Board with Menu")

font = pygame.font.SysFont(None, 30)



# ----------------------------
# Generic Button Callback
# ----------------------------
def generic_action(button_name):
    print(f"Button clicked: {button_name}")


# ----------------------------
# Button Class
# ----------------------------
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()

        color = BUTTON_COLOR
        if self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER

        pygame.draw.rect(surface, color, self.rect, border_radius=6)

        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)

        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.callback(self.text)


# ----------------------------
# Chess Board Drawing
# ----------------------------
def draw_chess_board(surface):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE

            pygame.draw.rect(
                surface,
                color,
                (
                    col * SQUARE_SIZE,
                    row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                ),
            )


# ----------------------------
# Create Menu Buttons
# ----------------------------
buttons = []

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
    y = start_y + i * (button_height + spacing)

    buttons.append(
        Button(
            start_x,
            y,
            button_width,
            button_height,
            name,
            generic_action,
        )
    )

pieces.render(screen)
# ----------------------------
# Main Loop
# ----------------------------
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        for button in buttons:
            button.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Ignore clicks in menu area
            if mx < BOARD_WIDTH:
                board_x = mx // SQUARE_SIZE
                board_y = my // SQUARE_SIZE

                # If a piece is selected, attempt move
                if selected_piece:

                    if (board_x, board_y) in allowed_moves:
                        selected_piece.x = board_x
                        selected_piece.y = board_y

                    # Deselect regardless of whether move succeeded
                    selected_piece = None
                    allowed_moves = []

                else:
                    piece = get_piece_at(board_x, board_y)

                    if piece:
                        selected_piece = piece
                        allowed_moves = get_allowed_moves(piece)

    # Background
    screen.fill((0, 0, 0))

    # Chess board
    draw_chess_board(screen)

    # Render pieces
    pieces.render(screen)
    if selected_piece:
        for mx, my in allowed_moves:
            center = (
                mx * SQUARE_SIZE + SQUARE_SIZE // 2,
                my * SQUARE_SIZE + SQUARE_SIZE // 2,
            )

            pygame.draw.circle(
                screen,
                (0, 255, 0),
                center,
                SQUARE_SIZE // 8,
            )
    if selected_piece:
        pygame.draw.rect(
            screen,
            (255, 255, 0),
            (
                selected_piece.x * SQUARE_SIZE,
                selected_piece.y * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE,
            ),
            4,
        )
    # Menu panel
    pygame.draw.rect(
        screen,
        MENU_BG,
        (BOARD_WIDTH, 0, MENU_WIDTH, WINDOW_HEIGHT),
    )

    # Buttons
    for button in buttons:
        button.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
