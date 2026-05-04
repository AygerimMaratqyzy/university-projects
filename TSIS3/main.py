import pygame, sys, time, random, os
from pygame.locals import *

import persistence
import ui
from racer import (
    Player, Enemy, Coin, PowerUp, OilSpill, NitroStrip, MovingBarrier,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)

#Asset path resolution
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.join(_BASE_DIR, "assets")

def asset(filename):
    """Return the full path to a file inside the assets/ folder."""
    return os.path.join(_ASSETS_DIR, filename)

#Init
pygame.init()
pygame.mixer.init()

FPS = 60
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car Racer: Turbo Edition")
clock = pygame.time.Clock()

#Background
def make_road_bg():
    """Fallback procedural road background."""
    surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    surf.fill((60, 60, 60))
    for lane_x in [SCREEN_WIDTH//3, 2*SCREEN_WIDTH//3]:
        for y in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.rect(surf, (230,230,230), (lane_x-3, y, 6, 30))
    return surf

try:
    background = pygame.image.load(asset("AnimatedStreet.png")).convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception:
    background = make_road_bg()

#Sound helpers
def try_play_sound(path, sound_on):
    if not sound_on: return
    try:
        pygame.mixer.Sound(path).play()
    except Exception:
        pass

#Difficulty presets
DIFF = {
    "easy":   {"base_speed": 3.5, "enemy_count": 2, "obstacle_rate": 0.003, "speed_inc": 0.3},
    "normal": {"base_speed": 5.0, "enemy_count": 3, "obstacle_rate": 0.005, "speed_inc": 0.5},
    "hard":   {"base_speed": 6.5, "enemy_count": 4, "obstacle_rate": 0.008, "speed_inc": 0.7},
}
SPEED_UP_EVERY = 5   # coins between speed bumps

#Custom events
SPAWN_COIN   = USEREVENT + 1
SPAWN_PWORUP = USEREVENT + 2
SPAWN_NITRO  = USEREVENT + 3
SPAWN_BARRIER= USEREVENT + 4

def run_game(settings: dict, player_name: str):
    """Runs one full game session. Returns 'retry' or 'menu'."""
    diff   = DIFF[settings.get("difficulty", "normal")]
    sound  = settings.get("sound", True)

    #State
    SPEED          = diff["base_speed"]
    SCORE          = 0
    COINS          = 0
    DISTANCE       = 0          # pixels driven (divide by 10 for "metres")
    NEXT_SPEED_UP  = SPEED_UP_EVERY
    bg_y           = 0
    speedup_timer  = 0
    oil_slow_timer = 0          # frames of oil-slow remaining
    repair_flash   = 0          # visual flash on repair
    active_powerup = None       # "nitro"|"shield"|"repair"|None (for HUD)

    #Sprites
    P1 = Player(settings.get("car_color", "default"))

    enemies = pygame.sprite.Group()
    for _ in range(diff["enemy_count"]):
        enemies.add(Enemy(P1.rect))

    coins      = pygame.sprite.Group()
    powerups   = pygame.sprite.Group()
    oils       = pygame.sprite.Group()
    nitrostrips= pygame.sprite.Group()
    barriers   = pygame.sprite.Group()

    all_sprites = pygame.sprite.Group()
    all_sprites.add(P1)
    all_sprites.add(*enemies)

    #Timers
    pygame.time.set_timer(SPAWN_COIN,    2500)
    pygame.time.set_timer(SPAWN_PWORUP, 7000)
    pygame.time.set_timer(SPAWN_NITRO,  9000)
    pygame.time.set_timer(SPAWN_BARRIER,11000)

    font_big = pygame.font.SysFont("Verdana", 30, bold=True)

    #Helper: safe enemy spawn
    def spawn_enemy():
        e = Enemy(P1.rect)
        enemies.add(e)
        all_sprites.add(e)

    #Main loop
    running = True
    while running:

        # 1. Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); sys.exit()

            if event.type == SPAWN_COIN:
                c = Coin()
                coins.add(c); all_sprites.add(c)

            if event.type == SPAWN_PWORUP:
                if len(powerups) < 2:          # cap on screen
                    pu = PowerUp()
                    powerups.add(pu); all_sprites.add(pu)

            if event.type == SPAWN_NITRO:
                if random.random() < 0.5:      # 50 % chance
                    ns = NitroStrip()
                    nitrostrips.add(ns); all_sprites.add(ns)

            if event.type == SPAWN_BARRIER:
                if random.random() < diff["obstacle_rate"] * 100:
                    b = MovingBarrier()
                    barriers.add(b); all_sprites.add(b)

            if event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        # 2. Spawn oil spills randomly
        if random.random() < diff["obstacle_rate"]:
            o = OilSpill()
            oils.add(o); all_sprites.add(o)

        # 3. Scale speed by difficulty increase
        if COINS >= NEXT_SPEED_UP:
            SPEED        += diff["speed_inc"]
            NEXT_SPEED_UP += SPEED_UP_EVERY
            speedup_timer = 90
            # Spawn extra enemy on hard
            if settings.get("difficulty") == "hard":
                spawn_enemy()

        # Nitro multiplier
        effective_speed = SPEED * (1.6 if P1.nitro_active else 1.0)
        effective_speed *= (0.5 if oil_slow_timer > 0 else 1.0)

        # 4. Scroll background
        bg_y = (bg_y + effective_speed) % SCREEN_HEIGHT
        DISPLAYSURF.blit(background, (0, bg_y))
        DISPLAYSURF.blit(background, (0, bg_y - SCREEN_HEIGHT))

        # 5. Move everything
        P1.move()
        P1.update_powerups()
        if oil_slow_timer > 0: oil_slow_timer -= 1
        if repair_flash   > 0: repair_flash   -= 1

        for e in enemies:       e.move(effective_speed)
        for c in list(coins):   c.move(SPEED)
        for pu in list(powerups): pu.move(SPEED)
        for o in list(oils):    o.move(SPEED)
        for ns in list(nitrostrips): ns.move(SPEED)
        for b in list(barriers): b.move(SPEED)

        DISTANCE += int(effective_speed)
        SCORE_DISPLAY = SCORE + COINS * 2 + DISTANCE // 100

        # 6. Draw all sprites
        for entity in all_sprites:
            DISPLAYSURF.blit(entity.image, entity.rect)

        # 7. Coin collection
        collected = pygame.sprite.spritecollide(P1, coins, True, pygame.sprite.collide_mask)
        for coin in collected:
            COINS += coin.value
            try_play_sound(asset("coin.mp3"), sound)
            pop = pygame.font.SysFont("Verdana",16,bold=True).render(f"+{coin.value}", True, coin.colour)
            DISPLAYSURF.blit(pop, coin.rect.topleft)

        # 8. Power-up collection
        hit_pus = pygame.sprite.spritecollide(P1, powerups, True, pygame.sprite.collide_mask)
        for pu in hit_pus:
            P1.apply_powerup(pu.kind)
            active_powerup = pu.kind
            try_play_sound(asset("powerup.mp3"), sound)
            if pu.kind == "repair":
                repair_flash = 60

        # 9. Nitro-strip
        hit_ns = pygame.sprite.spritecollide(P1, nitrostrips, True, pygame.sprite.collide_mask)
        if hit_ns:
            P1.apply_powerup("nitro")
            active_powerup = "nitro"

        # 10. Oil spill
        hit_oil = pygame.sprite.spritecollide(P1, oils, True, pygame.sprite.collide_mask)
        if hit_oil:
            oil_slow_timer = 120    # 2 s slow

        # Determine active power-up label for HUD
        pu_timer = 0
        if P1.nitro_active:
            active_powerup = "nitro";  pu_timer = P1.nitro_timer
        elif P1.shield_active:
            active_powerup = "shield"; pu_timer = P1.shield_timer
        else:
            active_powerup = None

        # 11. HUD
        ui.draw_hud(
            DISPLAYSURF, SCORE_DISPLAY, COINS, DISTANCE // 10,
            effective_speed, P1, NEXT_SPEED_UP,
            active_powerup, pu_timer, oil_slow_timer > 0
        )

        if speedup_timer > 0:
            su = font_big.render(f"SPEED UP! {SPEED:.1f}", True, (255, 80, 0))
            DISPLAYSURF.blit(su, su.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            speedup_timer -= 1

        if repair_flash > 0:
            rf = font_big.render("REPAIRED!", True, (0,200,80))
            DISPLAYSURF.blit(rf, rf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40)))

        # 12. Collision with enemy or barrier
        hit_enemy   = pygame.sprite.spritecollide(P1, enemies,  False, pygame.sprite.collide_mask)
        hit_barrier = pygame.sprite.spritecollide(P1, barriers, False, pygame.sprite.collide_mask)

        crashed = bool(hit_enemy or hit_barrier)
        if crashed:
            if P1.shield_active and not P1.shield_used:
                P1.shield_used   = True
                P1.shield_active = False
                # Remove the obstacle that was hit
                for s in (hit_enemy + hit_barrier):
                    s.kill()
                try_play_sound(asset("powerup.mp3"), sound)
            else:
                try_play_sound(asset("crash.mp3"), sound)
                # Flash red
                DISPLAYSURF.fill((255, 60, 60))
                pygame.display.flip()
                time.sleep(0.3)
                running = False

        pygame.display.flip()
        clock.tick(FPS)

    # ── End of session ────────────────────────────────────────────────────────
    pygame.time.set_timer(SPAWN_COIN,    0)
    pygame.time.set_timer(SPAWN_PWORUP, 0)
    pygame.time.set_timer(SPAWN_NITRO,  0)
    pygame.time.set_timer(SPAWN_BARRIER,0)

    final_score = SCORE_DISPLAY if 'SCORE_DISPLAY' in dir() else SCORE + COINS * 2
    persistence.save_score(player_name, final_score, DISTANCE // 10, COINS)
    board = persistence.load_leaderboard()
    return ui.game_over_screen(DISPLAYSURF, final_score, DISTANCE // 10, COINS, player_name)



#  APP LOOP

def main():
    settings = persistence.load_settings()
    player_name = ui.username_screen(DISPLAYSURF)

    while True:
        action = ui.main_menu(DISPLAYSURF)

        if action == "quit":
            break

        elif action == "play":
            result = run_game(settings, player_name)
            while result == "retry":
                result = run_game(settings, player_name)
            # result == "menu" → loop back to main menu

        elif action == "leaderboard":
            board = persistence.load_leaderboard()
            ui.leaderboard_screen(DISPLAYSURF, board)

        elif action == "settings":
            ui.settings_screen(DISPLAYSURF, settings)
            persistence.save_settings(settings)

    persistence.save_settings(settings)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
