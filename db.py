import sqlite3
import time

conn = sqlite3.connect("health.db", check_same_thread=False)
cursor = conn.cursor()

# Signals table
cursor.execute("""
CREATE TABLE IF NOT EXISTS signals (
    guild_id INTEGER,
    user_id INTEGER,
    signal TEXT,
    timestamp REAL
)
""")

conn.commit()


def add_signal(guild_id, user_id, signal):
    cursor.execute(
        "INSERT INTO signals VALUES (?, ?, ?, ?)",
        (guild_id, user_id, signal, time.time())
    )
    conn.commit()


def get_recent_signals(guild_id, user_id, seconds=300):
    cutoff = time.time() - seconds
    cursor.execute("""
        SELECT signal FROM signals
        WHERE guild_id=? AND user_id=? AND timestamp > ?
    """, (guild_id, user_id, cutoff))
    return [row[0] for row in cursor.fetchall()]
# -------------------------------------------------------------

-- User warnings
CREATE TABLE IF NOT EXISTS warnings (
    guild_id INTEGER,
    user_id INTEGER,
    mod_id INTEGER,
    reason TEXT,
    timestamp REAL
);

-- Safety alerts (spam, autoclick, etc.)
CREATE TABLE IF NOT EXISTS safety_alerts (
    guild_id INTEGER,
    user_id INTEGER,
    type TEXT,
    details TEXT,
    timestamp REAL
);
