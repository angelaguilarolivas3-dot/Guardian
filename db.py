# db.py
import sqlite3
import threading
import time

DB_PATH = "guardian.db"

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
lock = threading.Lock()

# ---------- TABLES ----------

# Warnings per server
cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    mod_id INTEGER NOT NULL,
    reason TEXT,
    timestamp REAL NOT NULL
)
""")

# Safety alerts (from detectors)
cursor.execute("""
CREATE TABLE IF NOT EXISTS safety_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    details TEXT,
    timestamp REAL NOT NULL
)
""")

conn.commit()


# ---------- WARNINGS API ----------

def add_warning(guild_id: int, user_id: int, mod_id: int, reason: str):
    ts = time.time()
    with lock:
        cursor.execute(
            "INSERT INTO warnings (guild_id, user_id, mod_id, reason, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, mod_id, reason, ts)
        )
        conn.commit()


def get_warning_count(guild_id: int, user_id: int) -> int:
    with lock:
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        (count,) = cursor.fetchone()
    return count


def get_warnings_for_user(guild_id: int, user_id: int, limit: int = 10):
    with lock:
        cursor.execute(
            "SELECT mod_id, reason, timestamp "
            "FROM warnings WHERE guild_id = ? AND user_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (guild_id, user_id, limit)
        )
        rows = cursor.fetchall()
    return rows


def clear_warnings_for_user(guild_id: int, user_id: int):
    with lock:
        cursor.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        conn.commit()


def clear_warnings_for_guild(guild_id: int):
    with lock:
        cursor.execute(
            "DELETE FROM warnings WHERE guild_id = ?",
            (guild_id,)
        )
        conn.commit()


# ---------- ALERTS API ----------

def add_alert(guild_id: int, user_id: int, alert_type: str, details: str = ""):
    ts = time.time()
    with lock:
        cursor.execute(
            "INSERT INTO safety_alerts (guild_id, user_id, type, details, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, alert_type, details, ts)
        )
        conn.commit()


def get_recent_alerts_for_guild(guild_id: int, limit: int = 20):
    with lock:
        cursor.execute(
            "SELECT user_id, type, details, timestamp "
            "FROM safety_alerts WHERE guild_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (guild_id, limit)
        )
        rows = cursor.fetchall()
    return rows
