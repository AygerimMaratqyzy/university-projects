
import pygame
import sys
import json
import os

from config import (
    WIDTH, HEIGHT, CELL,
    BLACK, WHITE, YELLOW, GRAY, DARK_GRAY, GREEN, ORANGE,
)
import db
from game import run_game

#settings
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {
    "snake_color": [50, 205, 50],
    "grid_overlay": True,
    "sound": False,
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"[settings] save failed: {e}")


#pygame init 

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

font_big   = pygame.font.SysFont("Verdana", 42, bold=True)
font_med   = pygame.font.SysFont("Verdana", 26)
font_small = pygame.font.SysFont("Verdana", 16)
font_tiny  = pygame.font.SysFont("Verdana", 13)


#button

class Button:
    def __init__(self, text, x, y, w=220, h=48,
                 color=GRAY, hover=(80,80,80), text_color=WHITE):
        self.rect  = pygame.Rect(x, y, w, h)
        self.text  = text
        self.color = color
        self.hover = hover
        self.tc    = text_color

    def draw(self, surf):
        c = self.hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color
        pygame.draw.rect(surf, c,     self.rect, border_radius=8)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=8)
        lbl = font_med.render(self.text, True, self.tc)
        surf.blit(lbl, (self.rect.centerx - lbl.get_width()//2,
                        self.rect.centery - lbl.get_height()//2))

    def clicked(self, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                and self.rect.collidepoint(ev.pos))


#shared helpers
def draw_bg():
    for r in range(HEIGHT // CELL):
        for c in range(WIDTH // CELL):
            col = DARK_GRAY if (r + c) % 2 == 0 else GRAY
            pygame.draw.rect(screen, col, (c*CELL, r*CELL, CELL, CELL))


def draw_title(text, y, color=YELLOW):
    s = font_big.render(text, True, color)
    screen.blit(s, (WIDTH//2 - s.get_width()//2, y))


def pump_quit():
    """Process quit events so the window stays responsive."""
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        yield ev


#username entry
def screen_username(db_ok):
    """Returns (username: str, player_id: int | None)."""
    username  = ""
    error_msg = "" if db_ok else "DB unavailable - scores won't be saved"

    while True:
        clock.tick(30)
        draw_bg()
        draw_title("SNAKE", HEIGHT//2 - 160)

        prompt = font_med.render("Enter your username:", True, WHITE)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 60))

        box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 44)
        pygame.draw.rect(screen, (60,60,60), box, border_radius=6)
        pygame.draw.rect(screen, YELLOW,     box, 2, border_radius=6)
        ns = font_med.render(username + "|", True, YELLOW)
        screen.blit(ns, (box.x + 10, box.centery - ns.get_height()//2))

        hint = font_small.render("Press ENTER to start", True, (160,160,160))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 40))

        if error_msg:
            es = font_small.render(error_msg, True, ORANGE)
            screen.blit(es, (WIDTH//2 - es.get_width()//2, HEIGHT//2 + 68))

        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and username.strip():
                    uname = username.strip()[:50]
                    pid   = None
                    if db_ok:
                        pid = db.get_or_create_player(uname)
                        if pid is None:
                            error_msg = f"DB error saving '{uname}' - check console"
                            continue          # stay on screen, let player retry
                    return uname, pid
                elif ev.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif ev.unicode.isprintable() and len(username) < 20:
                    username += ev.unicode


#main menu in the screen
def screen_main_menu():
    """Returns 'play' | 'leaderboard' | 'settings' | 'quit'."""
    bx = WIDTH//2 - 110
    by = HEIGHT//2 - 70
    buttons = [
        (Button("Play",        bx, by,       220, 48), "play"),
        (Button("Leaderboard", bx, by+65,    220, 48), "leaderboard"),
        (Button("Settings",    bx, by+130,   220, 48), "settings"),
        (Button("Quit",        bx, by+195,   220, 48,
                color=(80,30,30), hover=(120,40,40)), "quit"),
    ]

    while True:
        clock.tick(30)
        draw_bg()
        draw_title("SNAKE", HEIGHT//2 - 170)
        for btn, _ in buttons:
            btn.draw(screen)
        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            for btn, action in buttons:
                if btn.clicked(ev):
                    return action


#game over in the screen
def screen_game_over(score, level, personal_best, saved):
    """Returns 'retry' | 'menu'."""
    bx = WIDTH//2 - 110
    by = HEIGHT//2 + 75
    btn_retry = Button("Retry",     bx, by,     220, 48)
    btn_menu  = Button("Main Menu", bx, by + 65, 220, 48)

    while True:
        clock.tick(30)
        draw_bg()

        title = font_big.render("GAME OVER", True, (220, 50, 50))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 200))

        for i, (txt, col) in enumerate([
            (f"Score:  {score}",         WHITE),
            (f"Level:  {level}",         YELLOW),
            (f"Best:   {personal_best}", (180, 180, 255)),
        ]):
            s = font_med.render(txt, True, col)
            screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 - 115 + i*42))

        # Save status
        if saved:
            st = font_tiny.render("Score saved to leaderboard", True, GREEN)
        else:
            st = font_tiny.render("Score NOT saved (DB error - see console)", True, ORANGE)
        screen.blit(st, (WIDTH//2 - st.get_width()//2, HEIGHT//2 + 18))

        btn_retry.draw(screen)
        btn_menu.draw(screen)
        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if btn_retry.clicked(ev): return "retry"
            if btn_menu.clicked(ev):  return "menu"


#leaderboard
def screen_leaderboard():
    btn_back = Button("Back", WIDTH//2 - 60, HEIGHT - 60, 120, 40)
    rows = db.get_top10()

    while True:
        clock.tick(30)
        draw_bg()
        draw_title("Leaderboard", 20)

        if not rows:
            s = font_med.render("No scores yet!", True, (180,180,180))
            screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2))
        else:
            headers = ["#", "Username", "Score", "Lv", "Date"]
            col_x   = [25, 65, 245, 335, 395]
            hy      = 90
            for h, x in zip(headers, col_x):
                s = font_small.render(h, True, YELLOW)
                screen.blit(s, (x, hy))
            pygame.draw.line(screen, YELLOW, (20, hy+22), (WIDTH-20, hy+22), 1)

            for row in rows:
                y     = hy + 30 + (row["rank"]-1) * 28
                color = YELLOW if row["rank"] == 1 else WHITE
                for txt, x in zip(
                    [str(row["rank"]), row["username"][:16],
                     str(row["score"]), str(row["level_reached"]), row["played_at"]],
                    col_x
                ):
                    s = font_small.render(txt, True, color)
                    screen.blit(s, (x, y))

        btn_back.draw(screen)
        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if btn_back.clicked(ev): return


#settings
COLOR_PRESETS = [
    ("Green",  [50,  205,  50]),
    ("Blue",   [30,  144, 255]),
    ("Orange", [255, 140,   0]),
    ("Pink",   [255, 105, 180]),
    ("White",  [220, 220, 220]),
]


def screen_settings(settings):
    btn_save = Button("Save & Back", WIDTH//2 - 110, HEIGHT - 70, 220, 46)

    while True:
        clock.tick(30)
        draw_bg()
        draw_title("Settings", 20)

        # Grid overlay
        screen.blit(font_med.render("Grid overlay:", True, WHITE), (60, 110))
        gv  = "ON" if settings["grid_overlay"] else "OFF"
        gc  = GREEN if settings["grid_overlay"] else (180,60,60)
        gbc = Button(gv, 300, 105, 100, 38, color=gc, hover=tuple(min(255,c+30) for c in gc))
        gbc.draw(screen)

        # Sound
        screen.blit(font_med.render("Sound:", True, WHITE), (60, 170))
        sv  = "ON" if settings["sound"] else "OFF"
        sc  = GREEN if settings["sound"] else (180,60,60)
        sbc = Button(sv, 300, 165, 100, 38, color=sc, hover=tuple(min(255,c+30) for c in sc))
        sbc.draw(screen)

        # Snake color presets
        screen.blit(font_med.render("Snake color:", True, WHITE), (60, 240))
        preset_rects = []
        for i, (name, rgb) in enumerate(COLOR_PRESETS):
            rx, ry = 60 + i*100, 285
            r = pygame.Rect(rx, ry, 80, 36)
            sel = list(settings["snake_color"]) == rgb
            pygame.draw.rect(screen, tuple(rgb), r, border_radius=6)
            pygame.draw.rect(screen, YELLOW if sel else WHITE, r,
                             3 if sel else 2, border_radius=6)
            ns = font_tiny.render(name, True, BLACK if sum(rgb)>400 else WHITE)
            screen.blit(ns, (rx + r.w//2 - ns.get_width()//2,
                             ry + r.h//2 - ns.get_height()//2))
            preset_rects.append((r, rgb))

        btn_save.draw(screen)
        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if gbc.clicked(ev): settings["grid_overlay"] = not settings["grid_overlay"]
            if sbc.clicked(ev): settings["sound"]        = not settings["sound"]
            for r, rgb in preset_rects:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and r.collidepoint(ev.pos):
                    settings["snake_color"] = rgb
            if btn_save.clicked(ev):
                save_settings(settings)
                return


#main
def main():
    settings = load_settings()

    # Connect to DB once — all saves depend on this succeeding
    db_ok = db.init_db()
    if not db_ok:
        print("[main] WARNING: DB init failed. Check DB_CONFIG in config.py")

    username, player_id = screen_username(db_ok)
    print(f"[main] Logged in: username={username!r}, player_id={player_id}")

    personal_best = db.get_personal_best(player_id) if player_id else 0

    while True:
        action = screen_main_menu()

        if action == "quit":
            pygame.quit(); sys.exit()

        elif action == "leaderboard":
            screen_leaderboard()

        elif action == "settings":
            screen_settings(settings)

        elif action == "play":
            while True:
                score, level = run_game(
                    screen, clock, settings, personal_best,
                    font_big, font_med, font_small, font_tiny
                )
                print(f"[main] Game over — score={score}, level={level}")

                # ── Save score ────────────────────────────────────────────
                saved = False
                if player_id is not None:
                    saved = db.save_session(player_id, score, level)
                    if saved:
                        personal_best = db.get_personal_best(player_id)
                        print(f"[main] personal_best updated to {personal_best}")
                    else:
                        print("[main] save_session failed — check console above for DB error")
                else:
                    print("[main] player_id=None — score not saved")

                choice = screen_game_over(score, level, personal_best, saved)
                if choice == "menu":
                    break
                #loop back and play again


if __name__ == "__main__":
    main()