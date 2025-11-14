"""Add user_settings table for storing user preferences like their name."""

import sqlite3

def add_user_settings_table():
    """Add user_settings table to the database."""
    conn = sqlite3.connect('src/database/app.db')
    cursor = conn.cursor()

    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Insert default user_name setting (empty initially)
    cursor.execute('''
        INSERT OR IGNORE INTO user_settings (setting_key, setting_value)
        VALUES ('user_name', '')
    ''')

    conn.commit()
    conn.close()
    print("✓ user_settings table created successfully")
    print("✓ Default user_name setting added")

if __name__ == '__main__':
    add_user_settings_table()
