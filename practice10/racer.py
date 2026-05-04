import pygame, sys
from pygame.locals import *
import random, time

pygame.init()

# ── Constants ──────────────────────────────────────────────
FPS           = 60
FramePerSec   = pygame.time.Clock()

BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,  0,   0)
GOLD  = (255, 215,  0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
SPEED = 5
SCORE = 0
COINS = 0

# ── Fonts ──────────────────────────────────────────────────
font       = pygame.font.SysFont("Verdana", 60)
font_small = pygame.font.SysFont("Verdana", 20)
game_over  = font.render("Game Over", True, BLACK)

# ── Display ────────────────────────────────────────────────
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Car Racing Game")

# ── Background ─────────────────────────────────────────────
background = pygame.image.load("AnimatedStreet.png").convert()
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))


# ── Helper: load, crop and scale any car image ─────────────
def load_and_crop(filename, width, height):
    """
    Loads an image, crops out all transparent padding using
    get_bounding_rect(), then scales to the given width/height.
    This ensures the sprite rect tightly fits the actual car.
    """
    raw      = pygame.image.load(filename).convert_alpha()
    bounds   = raw.get_bounding_rect()                          # Smallest rect around non-transparent pixels
    cropped  = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    cropped.blit(raw, (0, 0), bounds)                          # Copy only the car pixels
    return pygame.transform.scale(cropped, (width, height))    # Scale to desired size


# ── Enemy Class ────────────────────────────────────────────
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Load, crop transparent edges, scale to exact size
        self.image = load_and_crop("Enemy.png", 60, 80)
        # Create pixel-perfect collision mask from non-transparent pixels
        self.mask  = pygame.mask.from_surface(self.image)
        self.rect  = self.image.get_rect()
        # Spawn at random x position at the top of the screen
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)

    def move(self):
        global SCORE, SPEED
        # Move downward at current speed
        self.rect.move_ip(0, SPEED)
        # If off screen, reset to top and increase score
        if self.rect.bottom > SCREEN_HEIGHT:
            SCORE += 1
            self.rect.top = 0
            self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), 0)


# ── Player Class ───────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Load, crop transparent edges, scale to same size as enemy
        self.image = load_and_crop("Player.png", 60, 80)
        # Create pixel-perfect collision mask
        self.mask  = pygame.mask.from_surface(self.image)
        self.rect  = self.image.get_rect()
        # Start at bottom center of screen
        self.rect.center = (SCREEN_WIDTH // 2, 520)

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        # Move left if not at left edge
        if self.rect.left > 0 and pressed_keys[K_LEFT]:
            self.rect.move_ip(-5, 0)
        # Move right if not at right edge
        if self.rect.right < SCREEN_WIDTH and pressed_keys[K_RIGHT]:
            self.rect.move_ip(5, 0)


# ── Coin Class ─────────────────────────────────────────────
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Draw a gold circle as the coin (no image file needed)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD, (10, 10), 10)
        # Mask for pixel-perfect collection detection
        self.mask  = pygame.mask.from_surface(self.image)
        self.rect  = self.image.get_rect()
        # Spawn at random x position at the top
        self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)

    def move(self):
        # Coins fall slower than enemies for variety
        self.rect.move_ip(0, SPEED * 0.6)
        # If missed, respawn at top
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.top = 0
            self.rect.center = (random.randint(20, SCREEN_WIDTH - 20), 0)


# ── Sprite Setup ───────────────────────────────────────────
P1 = Player()
E1 = Enemy()
C1 = Coin()

# Enemy group for crash collision detection
enemies = pygame.sprite.Group()
enemies.add(E1)

# Coin group for collection detection
coins = pygame.sprite.Group()
coins.add(C1)

# All sprites group for drawing
all_sprites = pygame.sprite.Group()
all_sprites.add(P1, E1, C1)

# ── Timers ─────────────────────────────────────────────────
INC_SPEED  = pygame.USEREVENT + 1
SPAWN_COIN = pygame.USEREVENT + 2
pygame.time.set_timer(INC_SPEED,  1000)   # Increase speed every 1 second
pygame.time.set_timer(SPAWN_COIN, 3000)   # Spawn new coin every 3 seconds


# ── Game Loop ──────────────────────────────────────────────
while True:

    # 1. Handle events
    for event in pygame.event.get():
        if event.type == INC_SPEED:
            SPEED += 0.5                        # Gradually increase difficulty

        if event.type == SPAWN_COIN:
            # Create and register a new coin
            new_coin = Coin()
            coins.add(new_coin)
            all_sprites.add(new_coin)

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # 2. Draw background first so everything else appears on top
    DISPLAYSURF.blit(background, (0, 0))

    # 3. Draw score in top left corner
    score_text = font_small.render("Score: " + str(SCORE), True, BLACK)
    DISPLAYSURF.blit(score_text, (10, 10))

    # 4. Draw coin counter in top right corner
    coin_text = font_small.render("Coins: " + str(COINS), True, GOLD)
    DISPLAYSURF.blit(coin_text, (SCREEN_WIDTH - 100, 10))

    # 5. Move all sprites
    P1.move()
    E1.move()
    for coin in coins:
        coin.move()

    # 6. Draw all sprites onto the screen
    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)

    # 7. Check if player collects any coins (True = remove coin on touch)
    collected = pygame.sprite.spritecollide(P1, coins, True, pygame.sprite.collide_mask)
    COINS += len(collected)                     # Add collected coins to counter

    # 8. Check if player crashes into an enemy using pixel-perfect mask collision
    if pygame.sprite.spritecollide(P1, enemies, False, pygame.sprite.collide_mask):
        pygame.mixer.Sound('crash.mp3').play()
        time.sleep(0.5)

        # Show game over screen in red
        DISPLAYSURF.fill(RED)
        DISPLAYSURF.blit(game_over, (30, 250))

        # Show final score and coins collected
        final_score = font_small.render("Score: " + str(SCORE), True, BLACK)
        final_coins = font_small.render("Coins: " + str(COINS), True, GOLD)
        DISPLAYSURF.blit(final_score, (10, 10))
        DISPLAYSURF.blit(final_coins, (SCREEN_WIDTH - 100, 10))

        pygame.display.update()

        # Clean up all sprites and exit after 2 seconds
        for entity in all_sprites:
            entity.kill()
        time.sleep(2)
        pygame.quit()
        sys.exit()

    # 9. Refresh display and maintain FPS
    pygame.display.update()
    FramePerSec.tick(FPS)