# init_db.py
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = 'palus_vikas.db'
DEFAULT_ADMIN_USER = 'admin'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # complaints table (same as before)
    c.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT NOT NULL UNIQUE,
        main_category TEXT,
        sub_category TEXT,
        prabhag TEXT,
        address TEXT,
        contact TEXT,
        email TEXT,
        created_at TEXT
    )
    ''')

    # admin users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT
    );
    ''')
    conn.commit()

    # create default admin if not exists
    c.execute("SELECT id FROM admins WHERE username = ?", (DEFAULT_ADMIN_USER,))
    if not c.fetchone():
        # password sourcing: prefer env var ADMIN_PASSWORD
        admin_pw = os.environ.get('ADMIN_PASSWORD', 'admin123')
        pw_hash = generate_password_hash(admin_pw)
        from datetime import datetime
        c.execute('''
            INSERT INTO admins (username, password_hash, created_at)
            VALUES (?, ?, ?)
        ''', (DEFAULT_ADMIN_USER, pw_hash, datetime.utcnow().isoformat()))
        conn.commit()
        print(f"Created default admin user '{DEFAULT_ADMIN_USER}'. Change password ASAP.")
        if 'ADMIN_PASSWORD' not in os.environ:
            print("Tip: set ADMIN_PASSWORD env variable before running init_db.py to choose a secure password.")
    else:
        print("Admin user already exists, skipping creation.")

    conn.close()
    print("Database initialized (palus_vikas.db)")

if __name__ == "__main__":
    init_db()
