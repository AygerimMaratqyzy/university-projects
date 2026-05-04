import pygame, random, os
from pygame.locals import *

#Asset path resolution
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.join(_BASE_DIR, "assets")

def asset(filename):
    """Return the full path to a file inside the assets/ folder."""
    return os.path.join(_ASSETS_DIR, filename)

#Colours
BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
RED    = (255,  0,   0)
GOLD   = (255, 215,  0)
SILVER = (192, 192, 192)
BRONZE = (205, 127,  50)
CYAN   = (  0, 255, 255)
GREEN  = (  0, 200,  80)
ORANGE = (255, 140,   0)
PURPLE = (160,  32, 240)
YELLOW = (255, 255,   0)
BLUE   = ( 30, 144, 255)
DARK_RED = (180, 0, 0)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600

#Helpers
_font_cache = {}

def _font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Verdana", size, bold=bold)
    return _font_cache[key]


def load_and_crop(filename, width, height):
    raw     = pygame.image.load(asset(filename)).convert_alpha()
    bounds  = raw.get_bounding_rect()
    cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    cropped.blit(raw, (0, 0), bounds)
    return pygame.transform.scale(cropped, (width, height))


def draw_car(surface, body_color, w, h, accent=None):
    """Draw a simple car shape programmatically."""
    accent = accent or (max(0, body_color[0]-60),
                        max(0, body_color[1]-60),
                        max(0, body_color[2]-60))
    # Body
    pygame.draw.rect(surface, body_color, (4, h//4, w-8, h*2//3), border_radius=6)
    # Cabin
    pygame.draw.rect(surface, accent,     (8, 4,     w-16, h//3), border_radius=4)
    # Windows
    pygame.draw.rect(surface, CYAN,       (10, 6,    w-20, h//3-6), border_radius=3)
    # Wheels
    for wx, wy in [(2, h//3), (w-14, h//3), (2, h*3//4), (w-14, h*3//4)]:
        pygame.draw.rect(surface, BLACK, (wx, wy, 12, 14), border_radius=3)


#Coin types
COIN_TYPES = [
    ("bronze",  1,  BRONZE, 10, 50),
    ("silver",  3,  SILVER, 12, 30),
    ("gold",    5,  GOLD,   14, 15),
    ("diamond", 10, CYAN,   17,  5),
]
_COIN_WEIGHTS = [ct[4] for ct in COIN_TYPES]


def pick_coin_type():
    return random.choices(COIN_TYPES, weights=_COIN_WEIGHTS, k=1)[0]


#Power-up types
# (label, color, duration_frames, 0=instant)
POWERUP_TYPES = {
    "nitro":  (ORANGE, 180, "NITRO"),    # 3 s @ 60 fps
    "shield": (BLUE,   300, "SHIELD"),   # 5 s
    "repair": (GREEN,    0, "REPAIR"),   # instant
}

#  SPRITES

class Player(pygame.sprite.Sprite):
    CAR_COLORS = {
        "default": (220, 50,  50),
        "red":     (255, 30,  30),
        "blue":    ( 30,144, 255),
        "green":   ( 30,200,  80),
    }

    def __init__(self, car_color="default"):
        super().__init__()
        self.w, self.h = 50, 80
        color = self.CAR_COLORS.get(car_color, self.CAR_COLORS["default"])
        try:
            self.image = load_and_crop("Player.png", self.w, self.h)
        except Exception:
            self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            draw_car(self.image, color, self.w, self.h)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, 520))
        # Power-up state
        self.shield_active  = False
        self.nitro_active   = False
        self.nitro_timer    = 0
        self.shield_timer   = 0
        self.shield_used    = False

    def move(self):
        keys = pygame.key.get_pressed()
        speed = 7 if self.nitro_active else 5
        if self.rect.left  > 0              and keys[K_LEFT]:
            self.rect.move_ip(-speed, 0)
        if self.rect.right < SCREEN_WIDTH   and keys[K_RIGHT]:
            self.rect.move_ip( speed, 0)

    def update_powerups(self):
        if self.nitro_active:
            self.nitro_timer -= 1
            if self.nitro_timer <= 0:
                self.nitro_active = False
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

    def apply_powerup(self, kind):
        if kind == "nitro":
            self.nitro_active = True
            self.nitro_timer  = POWERUP_TYPES["nitro"][1]
        elif kind == "shield":
            self.shield_active = True
            self.shield_timer  = POWERUP_TYPES["shield"][1]
            self.shield_used   = False
        elif kind == "repair":
            pass   # handled in main (clears one obstacle / restores crash)

    def draw_shield(self, surface):
        if self.shield_active:
            cx, cy = self.rect.centerx, self.rect.centery
            alpha_surf = pygame.Surface((70, 90), pygame.SRCALPHA)
            pygame.draw.ellipse(alpha_surf, (30, 144, 255, 80), (0, 0, 70, 90))
            pygame.draw.ellipse(alpha_surf, (30, 144, 255, 200), (0, 0, 70, 90), 2)
            surface.blit(alpha_surf, (cx - 35, cy - 45))


class Enemy(pygame.sprite.Sprite):
    COLORS = [(200,200,200),(180,60,60),(60,60,200),(60,180,60),(255,165,0)]

    def __init__(self, player_rect=None):
        super().__init__()
        self.w, self.h = 50, 80
        color = random.choice(self.COLORS)
        try:
            self.image = load_and_crop("Enemy.png", self.w, self.h)
        except Exception:
            self.image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            draw_car(self.image, color, self.w, self.h, accent=(30,30,30))
        self.mask  = pygame.mask.from_surface(self.image)
        self.rect  = self.image.get_rect()
        self._place(player_rect)

    def _place(self, player_rect):
        for _ in range(20):
            x = random.randint(40, SCREEN_WIDTH - 40)
            self.rect.center = (x, -random.randint(80, 300))
            if player_rect is None or not self.rect.colliderect(player_rect.inflate(80, 200)):
                return
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), -200)

    def move(self, speed):
        self.rect.move_ip(0, speed)
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.center = (random.randint(40, SCREEN_WIDTH-40), -random.randint(60,200))


class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        label, self.value, colour, radius, _ = pick_coin_type()
        self.colour = colour
        diam = radius * 2
        self.image = pygame.Surface((diam, diam), pygame.SRCALPHA)
        pygame.draw.circle(self.image, colour, (radius, radius), radius)
        pygame.draw.circle(self.image, WHITE,  (radius, radius), radius, 2)
        lf = _font(max(8, radius-2), bold=True)
        ls = lf.render(label[0].upper(), True, BLACK)
        self.image.blit(ls, ls.get_rect(center=(radius, radius)))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(random.randint(20, SCREEN_WIDTH-20), -20))
        # timeout: disappear after ~6 s if not collected
        self.life = 360

    def move(self, speed):
        self.rect.move_ip(0, speed * 0.6)
        self.life -= 1
        if self.rect.top > SCREEN_HEIGHT or self.life <= 0:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, kind=None):
        super().__init__()
        self.kind = kind or random.choice(list(POWERUP_TYPES.keys()))
        colour, _, label = POWERUP_TYPES[self.kind]
        r = 18
        self.image = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, colour, (r, r), r)
        pygame.draw.circle(self.image, WHITE,  (r, r), r, 2)
        lf = _font(11, bold=True)
        ls = lf.render(label[:2], True, WHITE)
        self.image.blit(ls, ls.get_rect(center=(r, r)))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(random.randint(30, SCREEN_WIDTH-30), -30))
        self.life = 300   # 5 s timeout

    def move(self, speed):
        self.rect.move_ip(0, speed * 0.5)
        self.life -= 1
        if self.rect.top > SCREEN_HEIGHT or self.life <= 0:
            self.kill()


class OilSpill(pygame.sprite.Sprite):
    """Slows the player for a short time on contact."""
    def __init__(self):
        super().__init__()
        w, h = random.randint(50, 90), 20
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (20, 20, 20, 160), (0, 0, w, h))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(random.randint(50, SCREEN_WIDTH-50), -30))
        self.life = 480

    def move(self, speed):
        self.rect.move_ip(0, speed * 0.4)
        self.life -= 1
        if self.rect.top > SCREEN_HEIGHT or self.life <= 0:
            self.kill()


class NitroStrip(pygame.sprite.Sprite):
    """Gives a short speed boost when driven over."""
    def __init__(self):
        super().__init__()
        w, h = 60, 14
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 200, 0, 200), (0, 0, w, h), border_radius=4)
        f = _font(9, bold=True)
        s = f.render("NITRO", True, BLACK)
        self.image.blit(s, s.get_rect(center=(w//2, h//2)))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(random.randint(50, SCREEN_WIDTH-50), -20))
        self.life = 420

    def move(self, speed):
        self.rect.move_ip(0, speed * 0.4)
        self.life -= 1
        if self.rect.top > SCREEN_HEIGHT or self.life <= 0:
            self.kill()


class MovingBarrier(pygame.sprite.Sprite):
    """Horizontal barrier that slides across the road."""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 18), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 80, 0), (0, 0, 100, 18), border_radius=4)
        pygame.draw.rect(self.image, BLACK,       (0, 0, 100, 18), 2, border_radius=4)
        f = _font(9, bold=True)
        s = f.render("BARRIER", True, WHITE)
        self.image.blit(s, s.get_rect(center=(50, 9)))
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        side = random.choice([-1, 1])
        self.rect.x = 0 if side == 1 else SCREEN_WIDTH
        self.rect.y = random.randint(100, SCREEN_HEIGHT - 200)
        self.hspeed = side * random.randint(2, 4)
        self.life   = 360

    def move(self, speed):
        self.rect.move_ip(self.hspeed, speed * 0.3)
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.hspeed *= -1
        self.life -= 1
        if self.rect.top > SCREEN_HEIGHT or self.life <= 0:
            self.kill()
