import pygame
import random
import sys
import time

from config import (
    CELL, COLS, ROWS, WIDTH, HEIGHT, FPS,
    FOODS_PER_LEVEL, SPEED_INCREMENT,
    FOOD_TYPES, _FOOD_WEIGHTS,
    POISON_COLOR, POISON_LIFETIME, POISON_SHORTEN,
    POWERUP_TYPES,
    OBSTACLE_START_LEVEL, OBSTACLES_PER_LEVEL,
    BLACK, WHITE, GREEN, DARK_GREEN, YELLOW,
    GRAY, DARK_GRAY, ORANGE, OBSTACLE_COLOR,
)


#food helpers
def pick_food_type():
    return random.choices(FOOD_TYPES, weights=_FOOD_WEIGHTS, k=1)[0]


def make_food(snake, food_list, obstacles, powerup):
    occupied = (set(map(tuple, snake))
                | {item['pos'] for item in food_list}
                | set(obstacles)
                | ({powerup['pos']} if powerup else set()))
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(1, ROWS - 1))
        if pos not in occupied:
            break
    name, pts, colour, _w, lifetime = pick_food_type()
    expires_at = time.time() + lifetime if lifetime is not None else None
    return {'pos': pos, 'colour': colour, 'pts': pts,
            'name': name, 'expires_at': expires_at, 'kind': 'normal'}


def make_poison(snake, food_list, obstacles, powerup):
    occupied = (set(map(tuple, snake))
                | {item['pos'] for item in food_list}
                | set(obstacles)
                | ({powerup['pos']} if powerup else set()))
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(1, ROWS - 1))
        if pos not in occupied:
            break
    return {'pos': pos, 'colour': POISON_COLOR, 'pts': 0,
            'name': 'poison', 'expires_at': time.time() + POISON_LIFETIME,
            'kind': 'poison'}


def purge_expired(food_list):
    now = time.time()
    return [i for i in food_list
            if i['expires_at'] is None or i['expires_at'] > now]


#power-up helpers
def make_powerup(snake, food_list, obstacles):
    occupied = (set(map(tuple, snake))
                | {item['pos'] for item in food_list}
                | set(obstacles))
    name, colour, field_ms, effect_ms = random.choice(POWERUP_TYPES)
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(1, ROWS - 1))
        if pos not in occupied:
            break
    now_ms = pygame.time.get_ticks()
    return {
        'pos':        pos,
        'colour':     colour,
        'name':       name,
        'expires_at': now_ms + field_ms,
        'effect_ms':  effect_ms,
    }


#obstacle helpers
def make_obstacles(snake, food_list, existing, count):
    """
    Place `count` new wall blocks that don't trap the snake head.
    Flood-fill check ensures the head cell stays reachable from itself
    (simple BFS of free cells).
    """
    blocked = (set(map(tuple, snake))
               | {item['pos'] for item in food_list}
               | set(existing))
    new_blocks = set(existing)
    attempts   = 0

    while len(new_blocks) - len(existing) < count and attempts < 1000:
        attempts += 1
        pos = (random.randint(0, COLS - 1), random.randint(1, ROWS - 1))
        if pos in blocked or pos in new_blocks:
            continue

        candidate = new_blocks | {pos}

        # BFS: make sure snake head can still reach ≥ (snake_len) free cells
        head  = tuple(snake[0])
        walls = candidate | set(map(tuple, snake[1:]))

        visited = set()
        queue   = [head]
        while queue:
            cx, cy = queue.pop()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (cx+dx, cy+dy)
                if nb in visited:
                    continue
                if not (0 <= nb[0] < COLS and 0 <= nb[1] < ROWS):
                    continue
                if nb in walls:
                    continue
                visited.add(nb)
                queue.append(nb)

        if len(visited) >= len(snake):
            new_blocks.add(pos)
            blocked.add(pos)

    return list(new_blocks)


#draw helpers
def draw_background(screen, grid_overlay):
    for row in range(ROWS):
        for col in range(COLS):
            color = DARK_GRAY if (row + col) % 2 == 0 else GRAY
            pygame.draw.rect(screen, color,
                             (col * CELL, row * CELL, CELL, CELL))
    if grid_overlay:
        for row in range(ROWS):
            for col in range(COLS):
                pygame.draw.rect(screen, (60, 60, 60),
                                 (col*CELL, row*CELL, CELL, CELL), 1)


def draw_snake(screen, snake, snake_color, shield_active):
    head_col = tuple(min(255, c + 40) for c in snake_color)
    for i, (col, row) in enumerate(snake):
        color = head_col if i == 0 else snake_color
        pygame.draw.rect(screen, color,
                         (col * CELL, row * CELL, CELL, CELL))
        pygame.draw.rect(screen, BLACK,
                         (col*CELL+2, row*CELL+2, CELL-4, CELL-4), 1)
    # Shield halo on head
    if shield_active:
        hx, hy = snake[0]
        centre = (hx * CELL + CELL // 2, hy * CELL + CELL // 2)
        pygame.draw.circle(screen, (144, 238, 144), centre, CELL // 2 + 3, 2)


def draw_food(screen, food_list, font_small):
    now = time.time()
    for item in food_list:
        col, row = item['pos']
        centre = (col * CELL + CELL // 2, row * CELL + CELL // 2)
        pygame.draw.circle(screen, item['colour'], centre, CELL // 2 - 2)
        if item['expires_at'] is not None:
            remaining = item['expires_at'] - now
            if remaining < 2.0 and int(remaining * 2) % 2 == 0:
                pygame.draw.circle(screen, ORANGE, centre, CELL // 2, 2)
        # Skull icon for poison
        if item['kind'] == 'poison':
            skull = font_small.render("☠", True, WHITE)
            screen.blit(skull,
                        (col*CELL + CELL//2 - skull.get_width()//2,
                         row*CELL + CELL//2 - skull.get_height()//2))
        else:
            pts_surf = font_small.render(f"+{item['pts']}", True, WHITE)
            screen.blit(pts_surf,
                        (col*CELL + CELL//2 - pts_surf.get_width()//2,
                         row*CELL - pts_surf.get_height()))


def draw_powerup(screen, powerup, font_small):
    if powerup is None:
        return
    col, row = powerup['pos']
    centre = (col * CELL + CELL // 2, row * CELL + CELL // 2)
    pygame.draw.rect(screen, powerup['colour'],
                     (col*CELL+1, row*CELL+1, CELL-2, CELL-2))
    pygame.draw.rect(screen, WHITE,
                     (col*CELL+1, row*CELL+1, CELL-2, CELL-2), 2)
    label_map = {"speed_boost": "S", "slow_motion": "W", "shield": "🛡"}
    lbl = font_small.render(label_map.get(powerup['name'], "?"), True, BLACK)
    screen.blit(lbl, (col*CELL + CELL//2 - lbl.get_width()//2,
                      row*CELL + CELL//2 - lbl.get_height()//2))


def draw_obstacles(screen, obstacles):
    for col, row in obstacles:
        pygame.draw.rect(screen, OBSTACLE_COLOR,
                         (col*CELL, row*CELL, CELL, CELL))
        pygame.draw.rect(screen, (60, 60, 70),
                         (col*CELL, row*CELL, CELL, CELL), 2)


def draw_hud(screen, score, level, fps, personal_best,
             active_effect, effect_end_ms, shield_active,
             font_small, font_tiny):
    score_text = font_small.render(f"Score: {score}", True, WHITE)
    level_text = font_small.render(f"Level: {level}", True, YELLOW)
    speed_text = font_small.render(f"Speed: {fps}",   True, WHITE)
    pb_text    = font_small.render(f"PB: {personal_best}", True, (180,180,255))
    screen.blit(score_text, (10, 5))
    screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 5))
    screen.blit(speed_text, (WIDTH - speed_text.get_width() - 10, 5))
    screen.blit(pb_text,    (WIDTH - pb_text.get_width() - 10, 22))

    # Active power-up indicator
    now_ms = pygame.time.get_ticks()
    if active_effect == "shield" and shield_active:
        pu_txt = font_tiny.render("🛡 SHIELD", True, (144, 238, 144))
        screen.blit(pu_txt, (10, 22))
    elif active_effect and effect_end_ms:
        remaining = max(0, (effect_end_ms - now_ms) // 1000)
        color_map = {"speed_boost": ORANGE, "slow_motion": (100,149,237)}
        c = color_map.get(active_effect, WHITE)
        label_map = {"speed_boost": "⚡ BOOST", "slow_motion": "🐢 SLOW"}
        pu_txt = font_tiny.render(
            f"{label_map.get(active_effect, active_effect)} {remaining}s", True, c)
        screen.blit(pu_txt, (10, 22))


#level-up pause screen
def show_level_up(screen, level, fps, font_big, font_med, clock):
    screen.fill(BLACK)
    t = font_big.render(f"Level {level}!", True, YELLOW)
    s = font_med.render(f"Speed → {fps}  |  Press SPACE", True, WHITE)
    screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2 - 60))
    screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 + 10))
    pygame.display.update()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_SPACE, pygame.K_RETURN):
                return
        clock.tick(30)


#main game function
def run_game(screen, clock, settings, personal_best,
             font_big, font_med, font_small, font_tiny):
    """
    Run one complete game session.
    Returns (score, level_reached).
    """
    snake_color = tuple(settings.get("snake_color", [50, 205, 50]))

    #State
    snake     = [(COLS//2, ROWS//2),
                 (COLS//2-1, ROWS//2),
                 (COLS//2-2, ROWS//2)]
    direction = (1, 0)

    obstacles  = []
    food_list  = []
    food_list.append(make_food(snake, food_list, obstacles, None))
    food_list.append(make_food(snake, food_list, obstacles, None))

    # Spawn initial poison food
    food_list.append(make_poison(snake, food_list, obstacles, None))

    powerup        = None
    powerup_timer  = pygame.time.get_ticks() + random.randint(5000, 12000)

    score       = 0
    level       = 1
    current_fps = FPS
    foods_eaten = 0

    # Power-up effect state
    active_effect  = None   # "speed_boost" | "slow_motion" | "shield" | None
    effect_end_ms  = 0
    shield_active  = False
    base_fps       = FPS    # fps before any speed/slow effect

    #game loop
    while True:
        now_ms = pygame.time.get_ticks()

        # 1. Events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_UP    and direction != (0,  1):
                    direction = (0, -1)
                if ev.key == pygame.K_DOWN  and direction != (0, -1):
                    direction = (0,  1)
                if ev.key == pygame.K_LEFT  and direction != (1,  0):
                    direction = (-1, 0)
                if ev.key == pygame.K_RIGHT and direction != (-1, 0):
                    direction = (1,  0)

        # 2. Power-up effect expiry
        if active_effect in ("speed_boost", "slow_motion") and now_ms >= effect_end_ms:
            current_fps   = base_fps
            active_effect = None

        # 3. Spawn / expire field power-up
        if powerup is None and now_ms >= powerup_timer:
            powerup = make_powerup(snake, food_list, obstacles)
        if powerup and now_ms >= powerup['expires_at']:
            powerup       = None
            powerup_timer = now_ms + random.randint(8000, 18000)

        # 4. New head
        new_head = (snake[0][0] + direction[0],
                    snake[0][1] + direction[1])

        # 5. Collision checks
        hit_wall = not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
        hit_self = new_head in snake
        hit_obstacle = tuple(new_head) in obstacles

        if hit_wall or hit_self or hit_obstacle:
            if shield_active:
                # Shield absorbs one collision
                shield_active = False
                active_effect = None
                # Teleport snake head back (don't move)
                new_head = snake[0]   # stay in place this tick
            else:
                return score, level

        # 6. Move snake
        snake.insert(0, new_head)

        # 7. Purge expired food
        food_list = purge_expired(food_list)
        # Always keep at least 1 normal food and 1 poison
        normal_count = sum(1 for f in food_list if f['kind'] == 'normal')
        poison_count = sum(1 for f in food_list if f['kind'] == 'poison')
        if normal_count == 0:
            food_list.append(make_food(snake, food_list, obstacles, powerup))
        if poison_count == 0:
            food_list.append(make_poison(snake, food_list, obstacles, powerup))

        # 8. Check food collision
        eaten = None
        for item in food_list:
            if tuple(new_head) == tuple(item['pos']):
                eaten = item
                break

        grew = False
        if eaten is not None:
            food_list.remove(eaten)

            if eaten['kind'] == 'poison':
                # Shorten snake
                for _ in range(POISON_SHORTEN):
                    if len(snake) > 1:
                        snake.pop()
                # Game over if too short
                if len(snake) <= 1:
                    return score, level
                # Respawn a poison
                food_list.append(make_poison(snake, food_list, obstacles, powerup))
            else:
                score       += eaten['pts']
                foods_eaten += 1
                grew         = True
                food_list.append(make_food(snake, food_list, obstacles, powerup))

                # Level-up
                if foods_eaten >= FOODS_PER_LEVEL:
                    foods_eaten  = 0
                    level       += 1
                    base_fps    += SPEED_INCREMENT
                    current_fps  = base_fps
                    if active_effect == "speed_boost":
                        current_fps = base_fps + 3
                    elif active_effect == "slow_motion":
                        current_fps = max(2, base_fps - 3)

                    # Add obstacles from level 3 onward
                    if level >= OBSTACLE_START_LEVEL:
                        obstacles = make_obstacles(
                            snake, food_list, obstacles, OBSTACLES_PER_LEVEL)

                    show_level_up(screen, level, base_fps,
                                  font_big, font_med, clock)

        # 9. Check power-up collision
        if powerup and tuple(new_head) == tuple(powerup['pos']):
            name      = powerup['name']
            effect_ms = powerup['effect_ms']
            powerup   = None
            powerup_timer = now_ms + random.randint(8000, 18000)

            if name == "speed_boost":
                active_effect  = "speed_boost"
                effect_end_ms  = now_ms + effect_ms
                current_fps    = base_fps + 3
            elif name == "slow_motion":
                active_effect  = "slow_motion"
                effect_end_ms  = now_ms + effect_ms
                current_fps    = max(2, base_fps - 3)
            elif name == "shield":
                active_effect  = "shield"
                shield_active  = True

        # 10. Tail removal if didn't grow
        if not grew:
            snake.pop()

        # 11. Draw
        draw_background(screen, settings.get("grid_overlay", True))
        draw_obstacles(screen, obstacles)
        draw_food(screen, food_list, font_small)
        draw_powerup(screen, powerup, font_small)
        draw_snake(screen, snake, snake_color, shield_active)
        draw_hud(screen, score, level, base_fps, personal_best,
                 active_effect, effect_end_ms, shield_active,
                 font_small, font_tiny)

        pygame.display.update()
        clock.tick(current_fps)
