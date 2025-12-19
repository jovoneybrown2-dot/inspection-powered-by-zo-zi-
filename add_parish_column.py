#!/usr/bin/env python3
"""
Migration script to add parish column to users table in SQLite database.
Run this script if you're getting "no such column: parish" errors.
"""
import sqlite3
import os

def add_parish_column():
    """Add parish and first_login columns to users table if they don't exist"""
    db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')

    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found")
        print(f"   Looking for: {os.path.abspath(db_path)}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        columns_added = []

        # Add parish column if missing
        if 'parish' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN parish TEXT")
            columns_added.append('parish')
            print(f"✓ Added parish column")
        else:
            print(f"✓ parish column already exists")

        # Add first_login column if missing
        if 'first_login' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN first_login INTEGER DEFAULT 1")
            columns_added.append('first_login')
            print(f"✓ Added first_login column")
        else:
            print(f"✓ first_login column already exists")

        if columns_added:
            conn.commit()
            print(f"✅ Successfully added {len(columns_added)} column(s) to users table in {db_path}")
        else:
            print(f"✅ All required columns already exist in {db_path}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error updating users table: {e}")
        return False

if __name__ == "__main__":
    add_parish_column()
