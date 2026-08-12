import sqlite3
import os
import hashlib
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'votes.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the necessary tables if they don't exist and migrates schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vote_date TEXT NOT NULL,
                name TEXT NOT NULL,
                choice TEXT NOT NULL,
                restaurant TEXT DEFAULT '',
                car TEXT DEFAULT '',
                role TEXT DEFAULT '',
                note TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vote_date, name)
            )
        ''')
        # Check if restaurant, car & role columns exist
        cursor.execute("PRAGMA table_info(votes)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'restaurant' not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN restaurant TEXT DEFAULT ''")
        if 'car' not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN car TEXT DEFAULT ''")
        if 'role' not in columns:
            cursor.execute("ALTER TABLE votes ADD COLUMN role TEXT DEFAULT ''")
        conn.commit()
    seed_users()

def seed_users():
    """Seeds the database with default users if they don't exist."""
    default_users = [
        ("Bohdan", "Qwerty123"),
        ("Богдан", "password123")
    ]
    with get_connection() as conn:
        cursor = conn.cursor()
        for username, password in default_users:
            cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            if not cursor.fetchone():
                salt = os.urandom(16)
                password_hash = _hash_password(password, salt)
                cursor.execute(
                    'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                    (username, password_hash, salt.hex())
                )
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
            'SELECT id, vote_date, name, choice, restaurant, car, role, note, updated_at FROM votes WHERE vote_date = ? ORDER BY updated_at ASC',
            (vote_date,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def upsert_vote(name, choice, restaurant='', car='', role='', note='', vote_date=None):
    """Inserts or updates a user's vote for a given date."""
    if not name or not name.strip():
        raise ValueError("Имя пользователя не может быть пустым.")
    
    if choice not in ['going', 'not_going']:
        raise ValueError("Некорректный выбор (ожидается 'going' или 'not_going').")

    name = name.strip()
    restaurant = restaurant.strip() if restaurant else ''
    car = car.strip() if car else ''
    role = role.strip() if role else ''
    note = note.strip() if note else ''

    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO votes (vote_date, name, choice, restaurant, car, role, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(vote_date, name) DO UPDATE SET
                choice = excluded.choice,
                restaurant = excluded.restaurant,
                car = excluded.car,
                role = excluded.role,
                note = excluded.note,
                updated_at = CURRENT_TIMESTAMP
        ''', (vote_date, name, choice, restaurant, car, role, note))
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

# Authentication functions
def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()

def register_user(username, password):
    """Registers a new user and returns a session token."""
    username = username.strip()
    if not username or not password:
        raise ValueError("Ім'я та пароль не можуть бути порожніми.")
        
    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)
    
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                (username, password_hash, salt.hex())
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Користувач з ім'ям '{username}' вже існує.")
        
        token = secrets.token_hex(32)
        cursor.execute(
            'INSERT INTO sessions (token, username) VALUES (?, ?)',
            (token, username)
        )
        conn.commit()
    return token, username

def login_user(username, password):
    """Authenticates a user and returns a session token."""
    username = username.strip()
    
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError("Невірне ім'я або пароль.")
            
        stored_hash = row['password_hash']
        salt = bytes.fromhex(row['salt'])
        
        if _hash_password(password, salt) != stored_hash:
            raise ValueError("Невірне ім'я або пароль.")
            
        token = secrets.token_hex(32)
        cursor.execute(
            'INSERT INTO sessions (token, username) VALUES (?, ?)',
            (token, username)
        )
        conn.commit()
    return token, username

def logout_user(token):
    """Invalidates a session token."""
    if not token:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()

def get_user_by_token(token):
    """Returns the username for a given session token, or None if invalid."""
    if not token:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM sessions WHERE token = ?', (token,))
        row = cursor.fetchone()
        return row['username'] if row else None

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized successfully at", DB_PATH)
