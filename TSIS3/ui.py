import pygame
from pygame.locals import *

BLACK  = (0,   0,   0)
WHITE  = (255, 255, 255)
GOLD   = (255, 215,   0)
RED    = (255,  50,  50)
GREEN  = (  0, 200,  80)
BLUE   = ( 30, 144, 255)
ORANGE = (255, 140,   0)
GRAY   = (180, 180, 180)
DARK   = ( 30,  30,  30)
BG     = ( 20,  20,  30)

SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600

_font_cache = {}

def _font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("Verdana", size, bold=bold)
    return _font_cache[key]


def _text(surf, text, size, color, cx, cy, bold=False):
    s = _font(size, bold).render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))
    return s.get_rect(center=(cx, cy))


def _button(surf, label, cx, cy, w=200, h=44, color=BLUE, hover=False):
    r = pygame.Rect(cx - w//2, cy - h//2, w, h)
    bg = tuple(min(255, c+40) for c in color) if hover else color
    pygame.draw.rect(surf, bg, r, border_radius=8)
    pygame.draw.rect(surf, WHITE, r, 2, border_radius=8)
    _text(surf, label, 18, WHITE, cx, cy, bold=True)
    return r


def _is_hovered(rect):
    return rect.collidepoint(pygame.mouse.get_pos())


#username entry

def username_screen(surf):
    """Blocking: asks for player name, returns string."""
    name = ""
    clock = pygame.time.Clock()
    while True:
        surf.fill(BG)
        _text(surf, "ENTER YOUR NAME", 26, GOLD, SCREEN_WIDTH//2, 180, bold=True)
        # Input box
        box = pygame.Rect(70, 240, 260, 44)
        pygame.draw.rect(surf, DARK, box, border_radius=6)
        pygame.draw.rect(surf, GOLD, box, 2, border_radius=6)
        _text(surf, name + "|", 22, WHITE, SCREEN_WIDTH//2, 262)
        _text(surf, "Press ENTER to start", 16, GRAY, SCREEN_WIDTH//2, 320)
        pygame.display.flip()
        clock.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); raise SystemExit
            if e.type == KEYDOWN:
                if e.key == K_RETURN and name.strip():
                    return name.strip()[:16]
                elif e.key == K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 16 and e.unicode.isprintable():
                    name += e.unicode

#main menu

def main_menu(surf):
    """Returns: 'play' | 'leaderboard' | 'settings' | 'quit'"""
    clock = pygame.time.Clock()
    while True:
        surf.fill(BG)
        # Title
        _text(surf, "CAR RACER",  38, GOLD,  SCREEN_WIDTH//2, 110, bold=True)
        _text(surf, "TURBO EDITION", 16, GRAY, SCREEN_WIDTH//2, 150)

        mx, my = pygame.mouse.get_pos()
        b_play  = _button(surf, "PLAY",        SCREEN_WIDTH//2, 230, color=GREEN,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,208,200,44).collidepoint(mx,my))
        b_lead  = _button(surf, "LEADERBOARD", SCREEN_WIDTH//2, 295, color=BLUE,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,273,200,44).collidepoint(mx,my))
        b_set   = _button(surf, "SETTINGS",    SCREEN_WIDTH//2, 360, color=(100,60,180),
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,338,200,44).collidepoint(mx,my))
        b_quit  = _button(surf, "QUIT",        SCREEN_WIDTH//2, 425, color=RED,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,403,200,44).collidepoint(mx,my))

        pygame.display.flip()
        clock.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT:
                return "quit"
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if b_play.collidepoint(e.pos):  return "play"
                if b_lead.collidepoint(e.pos):  return "leaderboard"
                if b_set.collidepoint(e.pos):   return "settings"
                if b_quit.collidepoint(e.pos):  return "quit"
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                return "quit"

#settings
def settings_screen(surf, settings: dict):
    """Mutates settings dict in-place; returns when user presses Back."""
    clock = pygame.time.Clock()
    CAR_COLORS  = ["default", "red", "blue", "green"]
    DIFFICULTIES = ["easy", "normal", "hard"]

    while True:
        surf.fill(BG)
        _text(surf, "SETTINGS", 30, GOLD, SCREEN_WIDTH//2, 60, bold=True)

        # Sound toggle
        sound_col = GREEN if settings["sound"] else RED
        sound_lbl = "Sound: ON" if settings["sound"] else "Sound: OFF"
        b_sound = _button(surf, sound_lbl, SCREEN_WIDTH//2, 150, color=sound_col,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,128,200,44).collidepoint(*pygame.mouse.get_pos()))

        # Car color
        _text(surf, "Car Colour:", 18, WHITE, SCREEN_WIDTH//2, 215)
        col_rects = []
        for i, cc in enumerate(CAR_COLORS):
            cx = 60 + i * 80
            r = _button(surf, cc[:3].upper(), cx, 250, w=68, h=36,
                        color=BLUE if settings["car_color"]==cc else DARK,
                        hover=pygame.Rect(cx-34,232,68,36).collidepoint(*pygame.mouse.get_pos()))
            col_rects.append((r, cc))

        # Difficulty
        _text(surf, "Difficulty:", 18, WHITE, SCREEN_WIDTH//2, 310)
        diff_rects = []
        diff_colors = {"easy": GREEN, "normal": BLUE, "hard": RED}
        for i, d in enumerate(DIFFICULTIES):
            cx = 75 + i * 110
            r = _button(surf, d.upper(), cx, 350, w=90, h=36,
                        color=diff_colors[d] if settings["difficulty"]==d else DARK,
                        hover=pygame.Rect(cx-45,332,90,36).collidepoint(*pygame.mouse.get_pos()))
            diff_rects.append((r, d))

        b_back = _button(surf, "BACK", SCREEN_WIDTH//2, 450, color=(80,80,80),
                         hover=pygame.Rect(SCREEN_WIDTH//2-100,428,200,44).collidepoint(*pygame.mouse.get_pos()))

        pygame.display.flip()
        clock.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); raise SystemExit
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if b_sound.collidepoint(e.pos):
                    settings["sound"] = not settings["sound"]
                for r, cc in col_rects:
                    if r.collidepoint(e.pos):
                        settings["car_color"] = cc
                for r, d in diff_rects:
                    if r.collidepoint(e.pos):
                        settings["difficulty"] = d
                if b_back.collidepoint(e.pos):
                    return
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                return


#leaderboard
def leaderboard_screen(surf, board: list):
    """Returns when user presses Back."""
    clock = pygame.time.Clock()
    MEDALS = ["#1", "#2", "#3"]
    MEDAL_COLORS = [GOLD, GRAY, (205,127,50)]

    while True:
        surf.fill(BG)
        _text(surf, "LEADERBOARD", 28, GOLD, SCREEN_WIDTH//2, 45, bold=True)
        # Header
        _text(surf, "RANK  NAME            SCORE  DIST", 12, GRAY, SCREEN_WIDTH//2, 80)
        pygame.draw.line(surf, GRAY, (20, 92), (SCREEN_WIDTH-20, 92))

        for i, entry in enumerate(board[:10]):
            y = 108 + i * 40
            rank_col = MEDAL_COLORS[i] if i < 3 else WHITE
            rank_lbl = MEDALS[i] if i < 3 else f"#{i+1}"
            _text(surf, rank_lbl, 14, rank_col, 35,  y, bold=(i<3))
            _text(surf, entry["name"][:12], 14, WHITE,  130, y)
            _text(surf, str(entry["score"]), 14, GOLD,  265, y)
            _text(surf, f"{entry.get('distance',0)}m", 14, GRAY, 345, y)

        if not board:
            _text(surf, "No scores yet — go race!", 18, GRAY, SCREEN_WIDTH//2, 200)

        b_back = _button(surf, "BACK", SCREEN_WIDTH//2, 560, color=(80,80,80),
                         hover=pygame.Rect(SCREEN_WIDTH//2-100,538,200,44).collidepoint(*pygame.mouse.get_pos()))
        pygame.display.flip()
        clock.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); raise SystemExit
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if b_back.collidepoint(e.pos): return
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                return


#game over

def game_over_screen(surf, score, distance, coins, player_name):
    """Returns: 'retry' | 'menu'"""
    clock = pygame.time.Clock()
    while True:
        surf.fill(BG)
        _text(surf, "GAME OVER",  40, RED,   SCREEN_WIDTH//2, 100, bold=True)
        _text(surf, player_name,  20, GRAY,  SCREEN_WIDTH//2, 145)

        pygame.draw.rect(surf, DARK, (40, 170, SCREEN_WIDTH-80, 160), border_radius=10)
        _text(surf, f"Score:    {score}",    18, GOLD,  SCREEN_WIDTH//2, 205)
        _text(surf, f"Distance: {distance}m", 18, WHITE, SCREEN_WIDTH//2, 240)
        _text(surf, f"Coins:    {coins}",    18, GOLD,  SCREEN_WIDTH//2, 275)
        _text(surf, f"Rank saved to leaderboard", 13, GRAY, SCREEN_WIDTH//2, 310)

        mx, my = pygame.mouse.get_pos()
        b_retry = _button(surf, "RETRY",     SCREEN_WIDTH//2, 390, color=GREEN,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,368,200,44).collidepoint(mx,my))
        b_menu  = _button(surf, "MAIN MENU", SCREEN_WIDTH//2, 450, color=BLUE,
                          hover=pygame.Rect(SCREEN_WIDTH//2-100,428,200,44).collidepoint(mx,my))

        pygame.display.flip()
        clock.tick(30)
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit(); raise SystemExit
            if e.type == MOUSEBUTTONDOWN and e.button == 1:
                if b_retry.collidepoint(e.pos): return "retry"
                if b_menu.collidepoint(e.pos):  return "menu"
            if e.type == KEYDOWN:
                if e.key == K_r: return "retry"
                if e.key == K_ESCAPE: return "menu"

#in-game hud

def draw_hud(surf, score, coins, distance, speed, player, next_speed_up,
             active_powerup=None, powerup_timer=0, oil_slow=False):
    f_sm = _font(16)
    f_xs = _font(13)

    # Score / Coins
    surf.blit(f_sm.render(f"Score: {score}", True, BLACK), (8, 8))
    surf.blit(f_sm.render(f"Coins: {coins}", True, GOLD),  (SCREEN_WIDTH-110, 8))
    surf.blit(f_xs.render(f"Dist: {distance}m", True, WHITE), (8, 30))

    # Speed bar
    spd_txt = f_xs.render(f"Spd {speed:.1f}  next+spd @{next_speed_up}c", True, WHITE)
    surf.blit(spd_txt, (8, SCREEN_HEIGHT - 28))

    # Active power-up badge
    if active_powerup:
        secs = powerup_timer // 60
        col = {"nitro": ORANGE, "shield": BLUE, "repair": GREEN}.get(active_powerup, WHITE)
        badge_txt = f_sm.render(f"{active_powerup.upper()} {secs}s", True, col)
        surf.blit(badge_txt, (SCREEN_WIDTH//2 - badge_txt.get_width()//2, 8))

    # Oil-slow indicator
    if oil_slow:
        oi = f_sm.render("OIL! Slow...", True, (180,180,0))
        surf.blit(oi, (SCREEN_WIDTH//2 - oi.get_width()//2, 30))

    # Shield indicator on player
    player.draw_shield(surf)
