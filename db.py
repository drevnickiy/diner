import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'votes.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the votes table if it doesn't exist and migrates schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vote_date TEXT NOT NULL,
                name TEXT NOT NULL,
                choice TEXT NOT NULL,
                restaurant TEXT DEFAULT '',
                note TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vote_date, name)
            )
        ''')
        # Check if restaurant column exists (for existing databases)
        cursor.execute("PRAGMA table_info(votes)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'restaurant' not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN restaurant TEXT DEFAULT ''")
        conn.commit()

def get_today_date_str():
    return datetime.now().strftime('%Y-%m-%d')

def get_votes(vote_date=None):
    """Retrieves all votes for a given date (defaults to today)."""
    if not vote_date:
        vote_date = get_today_date_str()
    
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, vote_date, name, choice, restaurant, note, updated_at FROM votes WHERE vote_date = ? ORDER BY updated_at ASC',
            (vote_date,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def upsert_vote(name, choice, restaurant='', note='', vote_date=None):
    """Inserts or updates a user's vote for a given date."""
    if not name or not name.strip():
        raise ValueError("Имя пользователя не может быть пустым.")
    
    if choice not in ['going', 'not_going']:
        raise ValueError("Некорректный выбор (ожидается 'going' или 'not_going').")

    name = name.strip()
    restaurant = restaurant.strip() if restaurant else ''
    note = note.strip() if note else ''

    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO votes (vote_date, name, choice, restaurant, note, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(vote_date, name) DO UPDATE SET
                choice = excluded.choice,
                restaurant = excluded.restaurant,
                note = excluded.note,
                updated_at = CURRENT_TIMESTAMP
        ''', (vote_date, name, choice, restaurant, note))
        conn.commit()
    
    return get_votes(vote_date)

def delete_vote(name, vote_date=None):
    """Deletes a user's vote for a given date."""
    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM votes WHERE vote_date = ? AND name = ?',
            (vote_date, name.strip())
        )
        conn.commit()
    
    return get_votes(vote_date)

def clear_votes(vote_date=None):
    """Clears all votes for a given date."""
    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM votes WHERE vote_date = ?', (vote_date,))
        conn.commit()
    
    return []

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized successfully at", DB_PATH)
