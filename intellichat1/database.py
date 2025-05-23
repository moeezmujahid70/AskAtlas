import sqlite3
import os
import bcrypt
from datetime import datetime
from chroma_store import embed_and_store_message

# Ensure the database directory exists
if not os.path.exists('data'):
    os.makedirs('data')

def get_db_connection():
    conn = sqlite3.connect('data/chat_app.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT DEFAULT 'New Chat',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        is_user BOOLEAN NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vector_id TEXT,
        FOREIGN KEY (chat_id) REFERENCES chats (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()

def create_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return user['id']
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_chat(user_id, title=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    title = title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    cursor.execute(
        "INSERT INTO chats (user_id, title) VALUES (?, ?)",
        (user_id, title)
    )
    conn.commit()
    chat_id = cursor.lastrowid
    conn.close()
    return chat_id

def get_user_chats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.title, c.created_at, 
               (SELECT COUNT(*) FROM messages WHERE chat_id = c.id) as message_count
        FROM chats c
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC
    """, (user_id,))
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return chats

def save_message(chat_id, user_id, content, is_user=True, vector_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id, user_id, content, is_user, vector_id) VALUES (?, ?, ?, ?, ?)",
        (chat_id, user_id, content, is_user, vector_id)
    )
    message_id = cursor.lastrowid

    # Embed and store only user messages
    if is_user:
        embed_and_store_message(message_id, content, user_id)

    conn.commit()
    conn.close()
    return message_id

def get_chat_messages(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, is_user, content, timestamp, vector_id
        FROM messages
        WHERE chat_id = ?
        ORDER BY timestamp
    """, (chat_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_all_user_messages(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.chat_id, m.content, m.is_user, m.timestamp, m.vector_id
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = ?
        ORDER BY m.timestamp
    """, (user_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def delete_chat(chat_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()

def update_message_vector_id(message_id, vector_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE messages SET vector_id = ? WHERE id = ?",
        (vector_id, message_id)
    )
    conn.commit()
    conn.close()

def ensure_default_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        password_hash = bcrypt.hashpw("admin".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                       ("admin", "admin@example.com", password_hash))
        conn.commit()
    conn.close()

# Initialize the database and default user
init_db()
ensure_default_admin()
