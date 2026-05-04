import psycopg2
import psycopg2.extras
from config import DB_CONFIG

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id),
    score         INTEGER   NOT NULL,
    level_reached INTEGER   NOT NULL,
    played_at     TIMESTAMP DEFAULT NOW()
);
"""


def _connect():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


def init_db():
    """Create tables if they don't exist. Returns True on success."""
    try:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(_SCHEMA_SQL)
        conn.commit()
        cur.close()
        conn.close()
        print("[db] init_db OK")
        return True
    except Exception as e:
        print(f"[db] init_db FAILED: {e}")
        return False


def get_or_create_player(username: str):
    """
    Return the player's integer id.
    Creates the row if it doesn't exist.
    Returns None on any error.
    """
    try:
        conn = _connect()
        cur  = conn.cursor()

        # Try insert — ignore if username already exists
        cur.execute(
            "INSERT INTO players (username) VALUES (%s) ON CONFLICT (username) DO NOTHING",
            (username,)
        )
        conn.commit()

        # Always fetch the id (works whether we just inserted or it existed)
        cur.execute("SELECT id FROM players WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            print(f"[db] player '{username}' id={row[0]}")
            return row[0]
        else:
            print(f"[db] get_or_create_player: no row found for '{username}'")
            return None

    except Exception as e:
        print(f"[db] get_or_create_player FAILED: {e}")
        return None


def save_session(player_id: int, score: int, level_reached: int) -> bool:
    """Insert a game_sessions row. Returns True on success."""
    try:
        conn = _connect()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s)",
            (player_id, score, level_reached)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[db] save_session OK — player_id={player_id}, score={score}, level={level_reached}")
        return True
    except Exception as e:
        print(f"[db] save_session FAILED: {e}")
        return False


def get_top10() -> list:
    """Return top 10 scores as list of dicts."""
    try:
        conn = _connect()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT p.username, gs.score, gs.level_reached, gs.played_at
            FROM   game_sessions gs
            JOIN   players p ON p.id = gs.player_id
            ORDER  BY gs.score DESC
            LIMIT  10
        """)
        rows   = cur.fetchall()
        cur.close()
        conn.close()

        result = []
        for rank, row in enumerate(rows, start=1):
            result.append({
                "rank":          rank,
                "username":      row["username"],
                "score":         row["score"],
                "level_reached": row["level_reached"],
                "played_at":     row["played_at"].strftime("%Y-%m-%d") if row["played_at"] else "-",
            })
        return result
    except Exception as e:
        print(f"[db] get_top10 FAILED: {e}")
        return []


def get_personal_best(player_id: int) -> int:
    """Return the player's highest score, or 0."""
    try:
        conn = _connect()
        cur  = conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(score), 0) FROM game_sessions WHERE player_id = %s",
            (player_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"[db] get_personal_best FAILED: {e}")
        return 0