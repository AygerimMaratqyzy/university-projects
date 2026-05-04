import pygame
import random
import sys
import time  # needed for food expiry timestamps

pygame.init()

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
CELL        = 20          # Size of each grid cell in pixels
COLS        = 30          # Number of columns in the grid
ROWS        = 25          # Number of rows in the grid
WIDTH       = CELL * COLS # Screen width  = 600 px
HEIGHT      = CELL * ROWS # Screen height = 500 px
FPS         = 7           # Starting frames per second (snake speed)

FOODS_PER_LEVEL = 3       # Foods eaten before advancing to the next level
SPEED_INCREMENT = 1       # FPS increase per level-up

# ─────────────────────────────────────────────
# EXTRA TASK 1 – FOOD TYPE TABLE
# ─────────────────────────────────────────────
# Each row: (name, points, colour, weight, lifetime_seconds)
#
# "weight"   – controls spawn probability via random.choices().
#              Higher weight → appears more often.
# "lifetime" – how many seconds the food stays on screen before
#              disappearing (Extra Task 2).  None = never expires.
#
FOOD_TYPES = [
    # name,       pts, colour,              weight, lifetime
    ("apple",      10, (220,  20,  60),        50,    None),  # common, never expires
    ("cherry",     25, (200,   0, 100),        25,      10),  # uncommon, 10 s
    ("banana",     15, (255, 215,   0),        15,       8),  # less common, 8 s
    ("blueberry",  50, ( 70, 130, 180),         7,       5),  # rare, 5 s
    ("diamond",   100, (  0, 255, 255),         3,       3),  # very rare, 3 s
]

# Pre-extract weights list once so random.choices() can use it directly
_FOOD_WEIGHTS = [ft[3] for ft in FOOD_TYPES]


def pick_food_type():
    """
    Return one entry from FOOD_TYPES chosen at random according
    to the weight column.  Rarer foods have lower weights.
    """
    return random.choices(FOOD_TYPES, weights=_FOOD_WEIGHTS, k=1)[0]


# ─────────────────────────────────────────────
# COLOURS
# ─────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 50, 205,  50)
DARK_GREEN = ( 34, 139,  34)
YELLOW     = (255, 215,   0)
GRAY       = ( 40,  40,  40)
DARK_GRAY  = ( 25,  25,  25)
ORANGE     = (255, 140,   0)   # colour for the expiry warning flash

# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock  = pygame.time.Clock()

# ─────────────────────────────────────────────
# FONTS
# ─────────────────────────────────────────────
font_big   = pygame.font.SysFont("Verdana", 48, bold=True)
font_med   = pygame.font.SysFont("Verdana", 28)
font_small = pygame.font.SysFont("Verdana", 18)


# ─────────────────────────────────────────────
# DRAW HELPERS
# ─────────────────────────────────────────────
def draw_background():
    """Fill the screen with alternating dark cells to create a grid look."""
    for row in range(ROWS):
        for col in range(COLS):
            color = DARK_GRAY if (row + col) % 2 == 0 else GRAY
            pygame.draw.rect(screen, color,
                             (col * CELL, row * CELL, CELL, CELL))


def draw_snake(snake):
    """
    Draw each segment of the snake.
    The head (index 0) is brighter green; body segments are darker.
    A thin black inner rectangle gives a segmented appearance.
    """
    for i, (col, row) in enumerate(snake):
        color = GREEN if i == 0 else DARK_GREEN
        pygame.draw.rect(screen, color,
                         (col * CELL, row * CELL, CELL, CELL))
        pygame.draw.rect(screen, BLACK,
                         (col * CELL + 2, row * CELL + 2, CELL - 4, CELL - 4), 1)


def draw_food(food_list):
    """
    Extra Task 1 & 2: draw every active food item.

    Each item in food_list is a dict:
        { 'pos': (col, row), 'colour': RGB, 'pts': int,
          'expires_at': float | None, 'name': str }

    Rendering:
    - The circle is drawn in the food's colour.
    - If the food expires within 2 seconds a thin ORANGE ring
      flashes around it to warn the player.
    - A small points label is drawn above the food cell so the
      player knows how much it is worth.
    """
    now = time.time()
    for item in food_list:
        col, row = item['pos']
        centre = (col * CELL + CELL // 2, row * CELL + CELL // 2)

        # ── draw the food circle ──────────────────────────────────────────
        pygame.draw.circle(screen, item['colour'], centre, CELL // 2 - 2)

        # ── expiry warning ring ───────────────────────────────────────────
        # Extra Task 2: if the food has a timer and fewer than 2 seconds
        # remain, draw an orange ring that blinks every half-second.
        if item['expires_at'] is not None:
            remaining = item['expires_at'] - now
            if remaining < 2.0 and int(remaining * 2) % 2 == 0:
                pygame.draw.circle(screen, ORANGE, centre, CELL // 2, 2)

        # ── points label ─────────────────────────────────────────────────
        pts_surf = font_small.render(f"+{item['pts']}", True, WHITE)
        screen.blit(pts_surf,
                    (col * CELL + CELL // 2 - pts_surf.get_width() // 2,
                     row * CELL - pts_surf.get_height()))


def draw_hud(score, level, fps):
    """Display score (left), level (centre), and speed (right) at the top."""
    score_text = font_small.render(f"Score: {score}", True, WHITE)
    level_text = font_small.render(f"Level: {level}", True, YELLOW)
    speed_text = font_small.render(f"Speed: {fps}",   True, WHITE)
    screen.blit(score_text, (10, 5))
    screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 5))
    screen.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 5))


# ─────────────────────────────────────────────
# FOOD HELPERS
# ─────────────────────────────────────────────
def make_food(snake, food_list):
    """
    Extra Task 1 & 2: create one new food item.

    Picks a weighted-random type from FOOD_TYPES, finds a grid
    position that is not occupied by the snake or existing food,
    and sets an expiry timestamp (or None for immortal food).

    Returns a dict that draw_food() and the game loop can use.
    """
    # Collect positions already occupied so the new food doesn't overlap
    occupied = set(snake) | {item['pos'] for item in food_list}

    # Pick a free position
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(1, ROWS - 1))
        # row starts at 1 to avoid the HUD row at the very top
        if pos not in occupied:
            break

    # Choose a weighted-random food type
    name, pts, colour, _weight, lifetime = pick_food_type()

    # Calculate absolute expiry time (or None if this food never expires)
    expires_at = time.time() + lifetime if lifetime is not None else None

    return {
        'pos':        pos,
        'colour':     colour,
        'pts':        pts,
        'name':       name,
        'expires_at': expires_at,
    }


def purge_expired(food_list):
    """
    Extra Task 2: remove any food items whose timer has run out.
    Returns the filtered list (items that are still alive).
    """
    now = time.time()
    return [item for item in food_list
            if item['expires_at'] is None or item['expires_at'] > now]


# ─────────────────────────────────────────────
# SCREEN HELPERS
# ─────────────────────────────────────────────
def show_screen(title, subtitle):
    """Show a centred title + subtitle and wait for SPACE or ENTER."""
    screen.fill(BLACK)
    t = font_big.render(title,    True, YELLOW)
    s = font_med.render(subtitle, True, WHITE)
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


def show_level_up(level, fps):
    """Show the level-up announcement and wait for SPACE or ENTER."""
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


# ─────────────────────────────────────────────
# MAIN GAME FUNCTION
# ─────────────────────────────────────────────
def game():
    """
    Run one full game session.
    Returns (final_score, final_level) when the player dies.
    """

    # ── Initial state ────────────────────────────────────────────────────
    # Snake starts as 3 horizontal segments in the middle of the screen
    snake     = [(COLS // 2, ROWS // 2),
                 (COLS // 2 - 1, ROWS // 2),
                 (COLS // 2 - 2, ROWS // 2)]
    direction = (1, 0)       # start moving right (dx=1, dy=0)

    # Extra Tasks 1 & 2: food is now a LIST of dicts (not a single tuple)
    # Start with two food items on the board for variety
    food_list = []
    food_list.append(make_food(snake, food_list))
    food_list.append(make_food(snake, food_list))

    score       = 0
    level       = 1
    current_fps = FPS        # speed increases each level
    foods_eaten = 0          # counts toward the next level-up

    # ── Game Loop ────────────────────────────────────────────────────────
    while True:

        # 1. Handle input events ─────────────────────────────────────────
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

        # 2. Calculate the new head position ─────────────────────────────
        new_head = (snake[0][0] + direction[0],
                    snake[0][1] + direction[1])

        # 3. Wall collision — head outside grid → game over ──────────────
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            return score, level

        # 4. Self collision — head hits a body segment → game over ────────
        if new_head in snake:
            return score, level

        # 5. Move snake — insert new head, remove tail later if no food ───
        snake.insert(0, new_head)

        # 6. Extra Task 2: remove expired food before checking collection ─
        food_list = purge_expired(food_list)

        # Ensure at least one food is always visible
        if len(food_list) == 0:
            food_list.append(make_food(snake, food_list))

        # 7. Check if the head landed on any food item ───────────────────
        eaten_item = None
        for item in food_list:
            if new_head == item['pos']:
                eaten_item = item
                break

        if eaten_item is not None:
            # Award the food's weighted point value (Extra Task 1)
            score       += eaten_item['pts']
            foods_eaten += 1

            # Remove the eaten food and spawn a fresh one
            food_list.remove(eaten_item)
            food_list.append(make_food(snake, food_list))

            # 8. Level-up check: if enough foods eaten this level ─────────
            if foods_eaten >= FOODS_PER_LEVEL:
                foods_eaten  = 0
                level       += 1
                current_fps += SPEED_INCREMENT
                show_level_up(level, current_fps)
        else:
            # No food eaten — remove tail to keep snake length constant
            snake.pop()

        # 9. Draw everything ─────────────────────────────────────────────
        draw_background()
        draw_food(food_list)      # draw all active food items
        draw_snake(snake)
        draw_hud(score, level, current_fps)

        pygame.display.update()
        clock.tick(current_fps)   # FPS controls the snake's speed


# ─────────────────────────────────────────────
# PROGRAM ENTRY POINT
# ─────────────────────────────────────────────
show_screen("SNAKE", "Press SPACE to start")

while True:
    # Run one game session; get final stats when the player dies
    final_score, final_level = game()

    # Show game-over screen with final stats; loop back to restart
    show_screen(
        "GAME OVER",
        f"Score: {final_score}  Level: {final_level}  |  SPACE to restart"
    )