from dataclasses import dataclass
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
            for rep in range(1, move.repeat + 2):
                if self.x + rep * move.dx == x and self.y + rep * move.dy == y:
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

    def get_num_pieces_of_player(self, player:Player) -> int:
        """Returns the number of pieces in the group belonging to the given player."""
        return len(list(filter(
            lambda piece: piece.belongs_to_player(player),self.pArray)))

    def render(self, screen: pygame.Surface) -> None:
        """Renders the group."""
        for piece in self.pArray:
            center_x = piece.x * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = piece.y * SQUARE_SIZE + SQUARE_SIZE // 2

            c = piece.player.get_color()

            # Placeholder rendering:
            # Draw a colored circle and the first letter.

            radius = SQUARE_SIZE // 3

            pygame.draw.circle(
                screen,
                (c.red, c.green, c.blue),
                (center_x, center_y),
                radius
            )

            label = font.render(
                piece.p_type.name.upper(),
                True,
                (0, 0, 0)
            )

            label_rect = label.get_rect(
                center=(center_x, center_y)
            )

            screen.blit(label, label_rect)


# Create two players with different colors
player1 = Player("Alice", HexColor(red=255, green=0, blue=0))   # Red
player2 = Player("Bob", HexColor(red=0, green=0, blue=255))     # Blue

# Create the player group
players = PlayerGroup()
players.add_player(player1)
players.add_player(player2)

# Define a pawn piece type
pawn_type = PieceType(
    name="Pawn",
    moves=(MP(dx=0, dy=1),)
)
# Define a queen piece type
queen_type = PieceType(
    name="Queen",
    moves=(MP(dx=0, dy=1, repeat=8), MP(dx=1, dy=0, repeat=8), MP(dx=1, dy=1, repeat=8),
           MP(dx=0, dy=-1, repeat=8), MP(dx=-1, dy=0, repeat=8), MP(dx=-1, dy=-1, repeat=8),
           MP(dx=1, dy=-1, repeat=8), MP(dx=-1, dy=1, repeat=8))
)

# Define a bishop piece type
bishop_type = PieceType(
    name="Bishop",
    moves=(MP(dx=1, dy=1, repeat=8), MP(dx=-1, dy=-1, repeat=8),
           MP(dx=1, dy=-1, repeat=8), MP(dx=-1, dy=1, repeat=8))
)

# Define a rook piece type
rook_type = PieceType(
    name="Rook",
    moves=(MP(dx=0, dy=1, repeat=8), MP(dx=1, dy=0, repeat=8),
           MP(dx=0, dy=-1, repeat=8), MP(dx=-1, dy=0, repeat=8))
)

# Define a knight piece type
knight_type = PieceType(
    name="Knight",
    moves=(MP(dx=1, dy=2),MP(dx=2, dy=1), MP(dx=-1, dy=-2), MP(dx=-2, dy=-1),
           MP(dx=-1, dy=2),MP(dx=-2, dy=1), MP(dx=1, dy=-2), MP(dx=2, dy=-1))
)

# Define a king piece type
king_type = PieceType(
    name="King",
    moves=(MP(dx=0, dy=1), MP(dx=1, dy=0), MP(dx=1, dy=1),
           MP(dx=0, dy=-1), MP(dx=-1, dy=0), MP(dx=-1, dy=-1),
           MP(dx=1, dy=-1), MP(dx=-1, dy=1))
)

# Create the piece group
pieces = PieceGroup()

# Add 10 pieces for player1
for i in range(10):
    pieces.add_piece(
        Piece(
            p_type=pawn_type,
            player=player1,
            x=i,
            y=1
        )
    )

# Add 10 pieces for player2
for i in range(10):
    pieces.add_piece(
        Piece(
            p_type=pawn_type,
            player=player2,
            x=i,
            y=6
        )
    )

# Add 10 pieces for player1
for i in range(10):
    pieces.add_piece(
        Piece(
            p_type=pawn_type,
            player=player1,
            x=i,
            y=1
        )
    )

# Add 10 pieces for player2
for i in range(10):
    pieces.add_piece(
        Piece(
            p_type=pawn_type,
            player=player2,
            x=i,
            y=6
        )
    )

# Add the queen piece for player1
    pieces.add_piece(
        Piece(
            p_type=queen_type,
            player=player1,
            x=4,
            y=0
        )
    )

# Add the queen piece for player2
    pieces.add_piece(
        Piece(
            p_type=queen_type,
            player=player2,
            x=4,
            y=7
        )
    )
# Add the king piece for player1
pieces.add_piece(
    Piece(
        p_type=king_type,
        player=player1,
        x=3,
        y=0
    )
)

# Add the king piece for player2
pieces.add_piece(
    Piece(
        p_type=king_type,
        player=player2,
        x=3,
        y=7
    )
)

# Add the rook pieces
for x in (0, 7):
    pieces.add_piece(
        Piece(
            p_type=rook_type,
            player=player1,
            x=x,
            y=0
        )
    )

    pieces.add_piece(
        Piece(
            p_type=rook_type,
            player=player2,
            x=x,
            y=7
        )
    )

# Add the knight pieces
for x in (1, 6):
    pieces.add_piece(
        Piece(
            p_type=knight_type,
            player=player1,
            x=x,
            y=0
        )
    )

    pieces.add_piece(
        Piece(
            p_type=knight_type,
            player=player2,
            x=x,
            y=7
        )
    )

# Add the bishop pieces
for x in (2, 5):
    pieces.add_piece(
        Piece(
            p_type=bishop_type,
            player=player1,
            x=x,
            y=0
        )
    )

    pieces.add_piece(
        Piece(
            p_type=bishop_type,
            player=player2,
            x=x,
            y=7
        )
    )


# Verify
print("Total players:", len(players.players))
print("Total pieces:", pieces.get_num_pieces())
print("Alice pieces:", pieces.get_num_pieces_of_player(player1))
print("Bob pieces:", pieces.get_num_pieces_of_player(player2))



# ----------------------------
# Configuration
# ----------------------------
BOARD_SIZE = 8
SQUARE_SIZE = 100

BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
MENU_WIDTH = 220

WINDOW_WIDTH = BOARD_WIDTH + MENU_WIDTH
WINDOW_HEIGHT = BOARD_WIDTH

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)

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

    # Background
    screen.fill((0, 0, 0))

    # Chess board
    draw_chess_board(screen)

    # Render pieces
    pieces.render(screen)

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