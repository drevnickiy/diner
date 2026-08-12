import os
import sys
import hashlib
import secrets
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = bool(DATABASE_URL)

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), 'votes.db')

def get_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def execute(cursor, query, params=()):
    if IS_POSTGRES:
        query = query.replace('?', '%s')
    cursor.execute(query, params)

def init_db():
    """Creates the necessary tables if they don't exist and migrates schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # SQLite vs PostgreSQL schema differences
        primary_key = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
        timestamp_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        
        execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS users (
                id {primary_key},
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                car TEXT DEFAULT '',
                created_at {timestamp_default}
            )
        ''')
        
        execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at {timestamp_default}
            )
        ''')
        
        execute(cursor, f'''
            CREATE TABLE IF NOT EXISTS votes (
                id {primary_key},
                vote_date TEXT NOT NULL,
                name TEXT NOT NULL,
                choice TEXT NOT NULL,
                restaurant TEXT DEFAULT '',
                car TEXT DEFAULT '',
                role TEXT DEFAULT '',
                note TEXT DEFAULT '',
                updated_at {timestamp_default},
                UNIQUE(vote_date, name)
            )
        ''')
        
        # Check for column existence
        if IS_POSTGRES:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='votes'")
            columns = [row[0] for row in cursor.fetchall()]
            
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
            user_columns = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("PRAGMA table_info(votes)")
            columns = [col['name'] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [col['name'] for col in cursor.fetchall()]

        # Migrate votes table
        if 'restaurant' not in columns:
            execute(cursor, "ALTER TABLE votes ADD COLUMN restaurant TEXT DEFAULT ''")
        if 'car' not in columns:
            execute(cursor, "ALTER TABLE votes ADD COLUMN car TEXT DEFAULT ''")
        if 'role' not in columns:
            execute(cursor, "ALTER TABLE votes ADD COLUMN role TEXT DEFAULT ''")
            
        # Migrate users table
        if 'car' not in user_columns:
            execute(cursor, "ALTER TABLE users ADD COLUMN car TEXT DEFAULT ''")
            
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
            execute(cursor, 'SELECT 1 FROM users WHERE username = ?', (username,))
            if not cursor.fetchone():
                salt = os.urandom(16)
                password_hash = _hash_password(password, salt)
                execute(cursor,
                    'INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)',
                    (username, password_hash, salt.hex())
                )
        conn.commit()

def get_today_date_str():
    return datetime.now().strftime('%Y-%m-%d')

def get_votes(vote_date=None):
    if not vote_date:
        vote_date = get_today_date_str()
    
    init_db()
    with get_connection() as conn:
        if IS_POSTGRES:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = conn.cursor()
            
        execute(cursor, 'SELECT id, vote_date, name, choice, restaurant, car, role, note, updated_at FROM votes WHERE vote_date = ? ORDER BY updated_at ASC', (vote_date,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def upsert_vote(name, choice, restaurant='', car='', role='', note='', vote_date=None):
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
        
        if IS_POSTGRES:
            # PostgreSQL upsert
            execute(cursor, '''
                INSERT INTO votes (vote_date, name, choice, restaurant, car, role, note, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(vote_date, name) DO UPDATE SET
                    choice = EXCLUDED.choice,
                    restaurant = EXCLUDED.restaurant,
                    car = EXCLUDED.car,
                    role = EXCLUDED.role,
                    note = EXCLUDED.note,
                    updated_at = CURRENT_TIMESTAMP
            ''', (vote_date, name, choice, restaurant, car, role, note))
        else:
            # SQLite upsert
            execute(cursor, '''
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
    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        execute(cursor, 'DELETE FROM votes WHERE vote_date = ? AND name = ?', (vote_date, name.strip()))
        conn.commit()
    return get_votes(vote_date)

def clear_votes(vote_date=None):
    if not vote_date:
        vote_date = get_today_date_str()

    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        execute(cursor, 'DELETE FROM votes WHERE vote_date = ?', (vote_date,))
        conn.commit()
    return []

def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex()

def register_user(username, password, car=''):
    username = username.strip()
    car = car.strip() if car else ''
    if not username or not password:
        raise ValueError("Ім'я та пароль не можуть бути порожніми.")
        
    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)
    
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            execute(cursor, 'INSERT INTO users (username, password_hash, salt, car) VALUES (?, ?, ?, ?)', (username, password_hash, salt.hex(), car))
        except Exception as e:
            raise ValueError(f"Користувач з ім'ям '{username}' вже існує.")
        
        token = secrets.token_hex(32)
        execute(cursor, 'INSERT INTO sessions (token, username) VALUES (?, ?)', (token, username))
        conn.commit()
    return token, username, car

def login_user(username, password):
    username = username.strip()
    
    init_db()
    with get_connection() as conn:
        if IS_POSTGRES:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = conn.cursor()
            
        execute(cursor, 'SELECT password_hash, salt, car FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError("Невірне ім'я або пароль.")
            
        stored_hash = row['password_hash']
        salt = bytes.fromhex(row['salt'])
        car = row['car'] if row['car'] else ''
        
        if _hash_password(password, salt) != stored_hash:
            raise ValueError("Невірне ім'я або пароль.")
            
        token = secrets.token_hex(32)
        execute(cursor, 'INSERT INTO sessions (token, username) VALUES (?, ?)', (token, username))
        conn.commit()
    return token, username, car

def logout_user(token):
    if not token:
        return
    with get_connection() as conn:
        cursor = conn.cursor()
        execute(cursor, 'DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()

def get_user_by_token(token):
    if not token:
        return None
    with get_connection() as conn:
        if IS_POSTGRES:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            cursor = conn.cursor()
            
        execute(cursor, 'SELECT s.username, u.car FROM sessions s JOIN users u ON s.username = u.username WHERE s.token = ?', (token,))
        row = cursor.fetchone()
        return {'username': row['username'], 'car': row['car']} if row else None

if __name__ == '__main__':
    init_db()
    print("✅ Database initialized successfully.")
