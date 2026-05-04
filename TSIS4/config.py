# Grid / display
CELL   = 20
COLS   = 30
ROWS   = 25
WIDTH  = CELL * COLS   # 600 px
HEIGHT = CELL * ROWS   # 500 px
FPS    = 7

# Progression
FOODS_PER_LEVEL  = 3
SPEED_INCREMENT  = 1

# Obstacles start appearing at this level
OBSTACLE_START_LEVEL = 3
OBSTACLES_PER_LEVEL  = 5   # new blocks added each level (after level 3)

#Food types
# (name, points, colour, weight, lifetime_seconds)
FOOD_TYPES = [
    ("apple",      10, (220,  20,  60),  50,    None),
    ("cherry",     25, (200,   0, 100),  25,      10),
    ("banana",     15, (255, 215,   0),  15,       8),
    ("blueberry",  50, ( 70, 130, 180),   7,       5),
    ("diamond",   100, (  0, 255, 255),   3,       3),
]
_FOOD_WEIGHTS = [ft[3] for ft in FOOD_TYPES]

#Poison food
POISON_COLOR    = (139,  0,  0)   # dark red
POISON_LIFETIME = 12              # seconds before it vanishes
POISON_SHORTEN  = 2               # segments removed when eaten

#Power-up definitions
# (name, colour, field_lifetime_ms, effect_duration_ms)
POWERUP_TYPES = [
    ("speed_boost",  (255, 165,   0), 8000, 5000),   # orange
    ("slow_motion",  ( 100, 149, 237), 8000, 5000),  # cornflower blue
    ("shield",       (144, 238, 144), 8000,    0),   # light green (lasts until triggered)
]

#Colours
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 50, 205,  50)
DARK_GREEN = ( 34, 139,  34)
YELLOW     = (255, 215,   0)
GRAY       = ( 40,  40,  40)
DARK_GRAY  = ( 25,  25,  25)
ORANGE     = (255, 140,   0)
OBSTACLE_COLOR = (100, 100, 120)

#Database
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "snake_game",
    "user":     "postgres",
    "password": "1234ai",
}