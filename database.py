import sqlite3
import random
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for subscribers
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for admin info (kept for compatibility)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_info (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        admin_id INTEGER
    )
    ''')
    
    # Table for cached booklets
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS booklets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        hindi_url TEXT,
        urdu_url TEXT,
        published_on DATE,
        is_latest BOOLEAN DEFAULT 0
    )
    ''')
    
    # Table for bot settings (welcome photo, etc)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Table for donations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        amount TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        approved_at TIMESTAMP
    )
    ''')
    
    # Table for darood sharif images
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS darood_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        caption TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table for hadees messages (with sent tracking)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hadees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        is_sent BOOLEAN DEFAULT 0,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP
    )
    ''')
    
    # Migrate old hadees table if needed (add is_sent, sent_at columns)
    try:
        cursor.execute('SELECT is_sent FROM hadees LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE hadees ADD COLUMN is_sent BOOLEAN DEFAULT 0')
        except:
            pass
    try:
        cursor.execute('SELECT sent_at FROM hadees LIMIT 1')
    except sqlite3.OperationalError:
        try:
            cursor.execute('ALTER TABLE hadees ADD COLUMN sent_at TIMESTAMP')
        except:
            pass
    
    conn.commit()
    conn.close()

# --- Subscribers ---

def add_subscriber(user_id, username, first_name=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO subscribers (user_id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
    conn.commit()
    conn.close()

def get_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM subscribers')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_subscriber_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM subscribers')
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- Admin ---

def set_admin(admin_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO admin_info (id, admin_id) VALUES (1, ?)', (admin_id,))
    conn.commit()
    conn.close()

def get_admin():
    from config import ADMIN_ID
    return ADMIN_ID

# --- Booklets ---

def update_latest_booklet(title, hindi_url, urdu_url, published_on):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE booklets SET is_latest = 0')
    cursor.execute('''
    INSERT INTO booklets (title, hindi_url, urdu_url, published_on, is_latest)
    VALUES (?, ?, ?, ?, 1)
    ''', (title, hindi_url, urdu_url, published_on))
    conn.commit()
    conn.close()

def get_latest_booklet():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT title, hindi_url, urdu_url FROM booklets WHERE is_latest = 1 ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row

def get_latest_booklet_published_date():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT published_on FROM booklets WHERE is_latest = 1 ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# --- Settings ---

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# --- Donations ---

def create_donation(user_id, username, first_name, amount):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO donations (user_id, username, first_name, amount, status)
    VALUES (?, ?, ?, ?, 'pending')
    ''', (user_id, username, first_name, amount))
    donation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return donation_id

def approve_donation(donation_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE donations SET status = 'approved', approved_at = CURRENT_TIMESTAMP WHERE id = ?", (donation_id,))
    conn.commit()
    conn.close()

def reject_donation(donation_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE donations SET status = 'rejected' WHERE id = ?", (donation_id,))
    conn.commit()
    conn.close()

def get_donation(donation_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, user_id, username, first_name, amount, status FROM donations WHERE id = ?', (donation_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_total_donations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(CAST(amount AS REAL)), 0) FROM donations WHERE status = 'approved'")
    row = cursor.fetchone()
    conn.close()
    return row

# --- Darood Sharif ---

def add_darood_image(file_id, caption=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO darood_images (file_id, caption) VALUES (?, ?)', (file_id, caption))
    conn.commit()
    conn.close()

def get_darood_images():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, file_id, caption FROM darood_images ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_darood_image(image_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM darood_images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

# --- Hadees ---

def add_hadees(message):
    """Add a new hadees to the collection."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO hadees (message, is_sent) VALUES (?, 0)', (message,))
    hadees_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return hadees_id

def get_next_hadees():
    """Get next unsent hadees. If all sent, reset and pick random."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First try to get an unsent hadees
    cursor.execute('SELECT id, message FROM hadees WHERE is_sent = 0 ORDER BY id ASC LIMIT 1')
    row = cursor.fetchone()
    
    if row:
        # Mark it as sent
        cursor.execute('UPDATE hadees SET is_sent = 1, sent_at = CURRENT_TIMESTAMP WHERE id = ?', (row[0],))
        conn.commit()
        conn.close()
        return row
    
    # All hadees have been sent - reset all and pick random
    cursor.execute('SELECT COUNT(*) FROM hadees')
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return None
    
    # Reset all to unsent
    cursor.execute('UPDATE hadees SET is_sent = 0, sent_at = NULL')
    conn.commit()
    
    # Pick a random one
    cursor.execute('SELECT id, message FROM hadees ORDER BY RANDOM() LIMIT 1')
    row = cursor.fetchone()
    
    if row:
        cursor.execute('UPDATE hadees SET is_sent = 1, sent_at = CURRENT_TIMESTAMP WHERE id = ?', (row[0],))
        conn.commit()
    
    conn.close()
    return row

def get_all_hadees():
    """Get all hadees with their status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, message, is_sent FROM hadees ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_hadees_count():
    """Get total and unsent hadees count."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM hadees')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM hadees WHERE is_sent = 0')
    unsent = cursor.fetchone()[0]
    conn.close()
    return total, unsent

def delete_hadees(hadees_id):
    """Delete a hadees by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM hadees WHERE id = ?', (hadees_id,))
    conn.commit()
    conn.close()

def reset_hadees_sent():
    """Reset all hadees to unsent."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE hadees SET is_sent = 0, sent_at = NULL')
    conn.commit()
    conn.close()
