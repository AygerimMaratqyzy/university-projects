import json, os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

DEFAULT_SETTINGS = {
    "sound":       True,
    "car_color":   "default",   # "default" | "red" | "blue" | "green"
    "difficulty":  "normal",    # "easy" | "normal" | "hard"
}

#Settings

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

#Leaderboard

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_score(name: str, score: int, distance: int, coins: int):
    board = load_leaderboard()
    board.append({"name": name, "score": score, "distance": distance, "coins": coins})
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(board, f, indent=2)
    return board
