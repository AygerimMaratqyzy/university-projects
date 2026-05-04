import pygame
import random
import sys

pygame.init()

# ── Constants ──────────────────────────────────────────────
CELL        = 20          # Size of each grid cell in pixels
COLS        = 30          # Number of columns in the grid
ROWS        = 25          # Number of rows in the grid
WIDTH       = CELL * COLS # Screen width  = 600px
HEIGHT      = CELL * ROWS # Screen height = 500px
FPS         = 10          # Starting frames per second (snake speed)

FOODS_PER_LEVEL = 3       # How many foods eaten to advance to next level
SPEED_INCREMENT = 1      # How much FPS increases per level

# ── Colors ─────────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 50, 205,  50)
DARK_GREEN = ( 34, 139,  34)
RED        = (220,  20,  60)
YELLOW     = (255, 215,   0)
GRAY       = ( 40,  40,  40)
DARK_GRAY  = ( 25,  25,  25)

# ── Display ────────────────────────────────────────────────
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock  = pygame.time.Clock()

# ── Fonts ──────────────────────────────────────────────────
font_big   = pygame.font.SysFont("Verdana", 48, bold=True)
font_med   = pygame.font.SysFont("Verdana", 28)
font_small = pygame.font.SysFont("Verdana", 18)


# ── Draw grid background ───────────────────────────────────
def draw_background():
    """Fill screen with alternating dark cells for a grid look."""
    for row in range(ROWS):
        for col in range(COLS):
            color = DARK_GRAY if (row + col) % 2 == 0 else GRAY
            pygame.draw.rect(screen, color,
                             (col * CELL, row * CELL, CELL, CELL))


# ── Draw the snake ─────────────────────────────────────────
def draw_snake(snake):
    """
    Draw each segment of the snake.
    Head is bright green, body segments are dark green.
    """
    for i, (col, row) in enumerate(snake):
        color = GREEN if i == 0 else DARK_GREEN
        # Outer rectangle (the cell)
        pygame.draw.rect(screen, color,
                         (col * CELL, row * CELL, CELL, CELL))
        # Inner rectangle for a segmented look
        pygame.draw.rect(screen, BLACK,
                         (col * CELL + 2, row * CELL + 2, CELL - 4, CELL - 4), 1)


# ── Draw the food ──────────────────────────────────────────
def draw_food(food):
    """Draw food as a red circle inside its grid cell."""
    col, row = food
    center = (col * CELL + CELL // 2, row * CELL + CELL // 2)
    pygame.draw.circle(screen, RED, center, CELL // 2 - 2)


# ── Draw HUD (score, level, speed) ────────────────────────
def draw_hud(score, level, fps):
    """Draw score, level, and current speed at the top of the screen."""
    score_text = font_small.render(f"Score: {score}", True, WHITE)
    level_text = font_small.render(f"Level: {level}", True, YELLOW)
    speed_text = font_small.render(f"Speed: {fps}",   True, WHITE)
    screen.blit(score_text, (10, 5))
    screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 5))
    screen.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 5))


# ── Generate random food position ─────────────────────────
def random_food(snake):
    """
    Keep generating random positions until one is found
    that is not occupied by the snake body.
    """
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in snake:   # Make sure food doesn't spawn on snake
            return pos


# ── Show centered message screen ──────────────────────────
def show_screen(title, subtitle):
    """
    Display a message screen with a title and subtitle.
    Waits for the player to press SPACE or ENTER to continue.
    """
    screen.fill(BLACK)
    t = font_big.render(title,    True, YELLOW)
    s = font_med.render(subtitle, True, WHITE)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 60))
    screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 10))
    pygame.display.update()

    # Wait for SPACE or ENTER key to continue
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return


# ── Level-up screen ────────────────────────────────────────
def show_level_up(level, fps):
    """Show a brief level-up notification."""
    screen.fill(BLACK)
    t = font_big.render(f"Level {level}!", True, YELLOW)
    s = font_med.render(f"Speed increased to {fps}! Press SPACE", True, WHITE)
    screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 60))
    screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 10))
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return


# ── Main game function ─────────────────────────────────────
def game():
    """
    Main game loop. Handles:
    - Snake movement and growth
    - Wall collision detection
    - Self collision detection
    - Food spawning
    - Level progression and speed increase
    - Score tracking
    """

    # ── Initial state ──────────────────────────────────────
    # Snake starts as 3 segments in the middle of the screen
    snake     = [(COLS // 2, ROWS // 2),
                 (COLS // 2 - 1, ROWS // 2),
                 (COLS // 2 - 2, ROWS // 2)]
    direction = (1, 0)        # Start moving right (dx=1, dy=0)
    food      = random_food(snake)

    score          = 0
    level          = 1
    current_fps    = FPS       # Current speed (increases each level)
    foods_eaten    = 0         # Count foods eaten in current level

    # ── Game Loop ──────────────────────────────────────────
    while True:

        # 1. Handle input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Change direction — prevent reversing into itself
                if event.key == pygame.K_UP    and direction != (0,  1):
                    direction = (0, -1)
                if event.key == pygame.K_DOWN  and direction != (0, -1):
                    direction = (0,  1)
                if event.key == pygame.K_LEFT  and direction != (1,  0):
                    direction = (-1, 0)
                if event.key == pygame.K_RIGHT and direction != (-1, 0):
                    direction = (1,  0)

        # 2. Calculate new head position
        new_head = (snake[0][0] + direction[0],
                    snake[0][1] + direction[1])

        # 3. Wall collision — if head goes outside grid, game over
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            return score, level    # Exit game loop → triggers game over

        # 4. Self collision — if head hits any body segment, game over
        if new_head in snake:
            return score, level

        # 5. Move snake — insert new head at front
        snake.insert(0, new_head)

        # 6. Check if food is eaten
        if new_head == food:
            score       += 10          # Increase score
            foods_eaten += 1           # Track progress toward next level
            food = random_food(snake)  # Spawn new food not on snake

            # 7. Check if level should increase
            if foods_eaten >= FOODS_PER_LEVEL:
                foods_eaten  = 0                      # Reset food counter
                level       += 1                      # Advance level
                current_fps += SPEED_INCREMENT        # Increase speed
                show_level_up(level, current_fps)     # Show level-up screen
        else:
            # If no food eaten, remove tail to maintain snake length
            snake.pop()

        # 8. Draw everything
        draw_background()
        draw_food(food)
        draw_snake(snake)
        draw_hud(score, level, current_fps)

        pygame.display.update()
        clock.tick(current_fps)   # Speed controlled by current_fps


# ── Program Entry Point ────────────────────────────────────
show_screen("SNAKE", "Press SPACE to start")

while True:
    # Run game and get final score and level when game ends
    final_score, final_level = game()

    # Show game over screen with final stats
    show_screen(
        "GAME OVER",
        f"Score: {final_score}  Level: {final_level}  |  SPACE to restart"
    )
    # Loop back to game() to let player restart