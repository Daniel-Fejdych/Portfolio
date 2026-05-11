import pygame
import sys

pygame.init()

# Window settings
WIDTH, HEIGHT = 800, 600
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Grid World with Interaction")

clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
GREEN = (100, 200, 100)
YELLOW = (240, 220, 70)
RED = (200, 100, 100)
BLUE = (50, 100, 255)

# Grid settings
TILE_SIZE = 40
GRID_COLS = WIDTH // TILE_SIZE
GRID_ROWS = HEIGHT // TILE_SIZE


class Tile:
    def __init__(self, collidable, color):
        self.collidable = collidable
        self.color = color


# Create 2D grid
grid = []
for row in range(GRID_ROWS):
    grid_row = []
    for col in range(GRID_COLS):
        # Border walls
        if row == 0 or row == GRID_ROWS - 1 or col == 0 or col == GRID_COLS - 1:
            grid_row.append(Tile(True, RED))
        # Some interior obstacles
        elif (row % 7 == 0 and col % 5 == 0):
            grid_row.append(Tile(True, RED))
        else:
            grid_row.append(Tile(False, GREEN))
    grid.append(grid_row)


# Player settings
player_size = 30
player_x = WIDTH // 2
player_y = 200
player_speed = 5


def check_collision(new_x, new_y):
    corners = [
        (new_x, new_y),
        (new_x + player_size, new_y),
        (new_x, new_y + player_size),
        (new_x + player_size, new_y + player_size),
    ]

    for corner_x, corner_y in corners:
        grid_x = corner_x // TILE_SIZE
        grid_y = corner_y // TILE_SIZE

        if 0 <= grid_x < GRID_COLS and 0 <= grid_y < GRID_ROWS:
            if grid[grid_y][grid_x].collidable:
                return True
    return False


def interact_with_tile(player_x, player_y):
    """
    Called when E is pressed.
    If player is standing on a non-collidable tile,
    toggle its color.
    """
    center_x = player_x + player_size // 2
    center_y = player_y + player_size // 2

    grid_x = center_x // TILE_SIZE
    grid_y = center_y // TILE_SIZE

    if 0 <= grid_x < GRID_COLS and 0 <= grid_y < GRID_ROWS:
        tile = grid[grid_y][grid_x]

        if not tile.collidable:
            # Toggle between GREEN and YELLOW
            if tile.color == GREEN:
                tile.color = YELLOW
            else:
                tile.color = GREEN


running = True
e_pressed_last_frame = False

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    new_x = player_x
    new_y = player_y

    # Movement
    if keys[pygame.K_w]:
        new_y -= player_speed
    if keys[pygame.K_s]:
        new_y += player_speed
    if keys[pygame.K_a]:
        new_x -= player_speed
    if keys[pygame.K_d]:
        new_x += player_speed

    if not check_collision(new_x, player_y):
        player_x = new_x
    if not check_collision(player_x, new_y):
        player_y = new_y

    # Interaction (E key, press detection not hold)
    if keys[pygame.K_e]:
        if not e_pressed_last_frame:
            interact_with_tile(player_x, player_y)
        e_pressed_last_frame = True
    else:
        e_pressed_last_frame = False

    # Drawing
    WINDOW.fill(WHITE)

    # Draw grid under player
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            tile = grid[row][col]
            pygame.draw.rect(
                WINDOW,
                tile.color,
                (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE),
            )
            pygame.draw.rect(
                WINDOW,
                GRAY,
                (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE),
                1,
            )

    # Draw player
    pygame.draw.rect(WINDOW, BLUE, (player_x, player_y, player_size, player_size))

    pygame.display.update()

pygame.quit()
sys.exit()
