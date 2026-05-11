import pygame
import sys

def create_checkerboard(screen_width, screen_height, tile_size, color1, color2):
    """
    Renders a checkerboard pattern on the specified surface.

    Args:
        screen_width (int): The width of the drawing area.
        screen_height (int): The height of the drawing area.
        tile_size (int): The width and height of each individual tile.
        color1 (tuple): RGB color for the first tile type.
        color2 (tuple): RGB color for the second tile type.
    """
    
    # Create a new surface to draw the checkerboard onto (optional, but good practice)
    checkerboard_surface = pygame.Surface((screen_width, screen_height))
    checkerboard_surface.fill((0, 0, 0)) # Start with a black background buffer

    # Calculate how many tiles fit along each dimension
    num_tiles_x = (screen_width + tile_size - 1) // tile_size
    num_tiles_y = (screen_height + tile_size - 1) // tile_size

    for y in range(num_tiles_y):
        for x in range(num_tiles_x):
            # Determine the color based on the sum of the coordinates (x + y)
            # If the sum is even, use color1; if odd, use color2.
            if (x + y) % 2 == 0:
                current_color = color1
            else:
                current_color = color2
            
            # Calculate the position of the tile
            rect = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
            
            # Draw the rectangle onto the checkerboard surface
            pygame.draw.rect(checkerboard_surface, current_color, rect)

    # Blit the resulting checkerboard onto the main screen
    screen.blit(checkerboard_surface, (0, 0))


def main():
    # --- Configuration ---
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    TILE_SIZE = 50  # Size of each square tile
    
    # Define Colors (R, G, B)
    RED = (255, 0, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # Colors for the checkerboard
    BOARD_COLOR_1 = (100, 100, 100) # Dark Gray
    BOARD_COLOR_2 = (200, 200, 200) # Light Gray

    # --- Pygame Initialization ---
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pygame Checkerboard")
    
    clock = pygame.time.Clock()
    
    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Drawing ---
        # 1. Fill the background (optional, but resets the screen)
        screen.fill(BLACK) 
        
        # 2. Render the checkerboard pattern
        create_checkerboard(
            SCREEN_WIDTH, 
            SCREEN_HEIGHT, 
            TILE_SIZE, 
            BOARD_COLOR_1, 
            BOARD_COLOR_2
        )
        
        # 3. Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
