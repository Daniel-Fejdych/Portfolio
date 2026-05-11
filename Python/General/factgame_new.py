import pygame
import sys
from typing import Tuple, Optional

# ------------------------------
# Constants
# ------------------------------
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
GRID_COLS = WIDTH // TILE_SIZE
GRID_ROWS = HEIGHT // TILE_SIZE

# Colors (RGB)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (100, 200, 100)
YELLOW = (240, 220, 70)
RED = (200, 100, 100)
BLUE = (50, 100, 255)

# Player
PLAYER_SIZE = 30
PLAYER_SPEED = 5

# ------------------------------
# Classes
# ------------------------------
class Tile:
    """A single tile in the grid."""
    __slots__ = ("collidable", "color")

    def __init__(self, collidable: bool, color: Tuple[int, int, int]) -> None:
        self.collidable = collidable
        self.color = color

    def draw(self, surface: pygame.Surface, x: int, y: int) -> None:
        """Draw the tile at pixel coordinates (x, y)."""
        rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, GRAY, rect, 1)  # border


class Grid:
    """2D grid of tiles."""
    def __init__(self) -> None:
        self.tiles: list[list[Tile]] = []
        self._create_grid()

    def _create_grid(self) -> None:
        """Build the grid with border walls and interior obstacles."""
        for row in range(GRID_ROWS):
            grid_row = []
            for col in range(GRID_COLS):
                if self._is_wall(row, col):
                    grid_row.append(Tile(True, RED))
                elif self._is_obstacle(row, col):
                    grid_row.append(Tile(True, RED))
                else:
                    grid_row.append(Tile(False, GREEN))
            self.tiles.append(grid_row)

    @staticmethod
    def _is_wall(row: int, col: int) -> bool:
        """Return True if the cell is on the border."""
        return (row == 0 or row == GRID_ROWS - 1 or
                col == 0 or col == GRID_COLS - 1)

    @staticmethod
    def _is_obstacle(row: int, col: int) -> bool:
        """Return True if the cell should be an obstacle."""
        # Creates a pattern: every 7th row and 5th column
        return (row % 7 == 0 and col % 5 == 0)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all tiles."""
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = col * TILE_SIZE
                y = row * TILE_SIZE
                self.tiles[row][col].draw(surface, x, y)

    def get_tile_at_pixel(self, x: int, y: int) -> Optional[Tile]:
        """Return the tile at the given pixel coordinates, or None if out of bounds."""
        col = x // TILE_SIZE
        row = y // TILE_SIZE
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            return self.tiles[row][col]
        return None

    def is_colliding(self, rect: pygame.Rect) -> bool:
        """Check if the given rectangle collides with any collidable tile."""
        # Determine grid cells the rectangle overlaps
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE

        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
                    if self.tiles[row][col].collidable:
                        return True
        return False


class Player:
    """Player character that can move and interact."""
    __slots__ = ("rect", "speed")

    def __init__(self, x: int, y: int, size: int, speed: int) -> None:
        self.rect = pygame.Rect(x, y, size, size)
        self.speed = speed

    def move(self, dx: int, dy: int, grid: Grid) -> None:
        """Attempt to move the player, checking collisions."""
        # Horizontal movement
        self.rect.x += dx
        if grid.is_colliding(self.rect):
            self.rect.x -= dx

        # Vertical movement
        self.rect.y += dy
        if grid.is_colliding(self.rect):
            self.rect.y -= dy

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the player."""
        pygame.draw.rect(surface, BLUE, self.rect)

    def get_center(self) -> Tuple[int, int]:
        """Return the center point of the player."""
        return self.rect.centerx, self.rect.centery


class Game:
    """Main game class managing the loop and state."""
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("2D Grid World with Interaction")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game objects
        self.grid = Grid()
        start_x = WIDTH // 2 - PLAYER_SIZE // 2
        start_y = 200
        self.player = Player(start_x, start_y, PLAYER_SIZE, PLAYER_SPEED)

    def handle_events(self) -> None:
        """Process Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.interact_with_tile()

    def interact_with_tile(self) -> None:
        """Toggle the color of the tile the player is standing on (if not collidable)."""
        cx, cy = self.player.get_center()
        tile = self.grid.get_tile_at_pixel(cx, cy)
        if tile and not tile.collidable:
            # Toggle between GREEN and YELLOW
            tile.color = YELLOW if tile.color == GREEN else GREEN

    def update(self) -> None:
        """Update player movement based on pressed keys."""
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= self.player.speed
        if keys[pygame.K_s]:
            dy += self.player.speed
        if keys[pygame.K_a]:
            dx -= self.player.speed
        if keys[pygame.K_d]:
            dx += self.player.speed

        if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.grid)

    def draw(self) -> None:
        """Render everything."""
        self.screen.fill(WHITE)
        self.grid.draw(self.screen)
        self.player.draw(self.screen)
        pygame.display.update()

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()


# ------------------------------
# Entry point
# ------------------------------
def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
