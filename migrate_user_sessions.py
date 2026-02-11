#!/usr/bin/env python3
"""
Migration: Add user_role column to user_sessions table
This fixes the login error where user_role column is missing
"""
from db_config import get_db_connection, release_db_connection, get_db_type

def migrate_user_sessions():
    """Add user_role column to user_sessions table if it doesn't exist"""

    print("=" * 70)
    print("🔄 MIGRATION: Adding user_role to user_sessions table")
    print("=" * 70)

    conn = get_db_connection()
    c = conn.cursor()
    db_type = get_db_type()

    try:
        # Check if column exists
        if db_type == 'postgresql':
            # PostgreSQL: Check information_schema
            c.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_sessions' AND column_name='user_role'
            """)
            column_exists = c.fetchone() is not None
        else:
            # SQLite: Use PRAGMA table_info
            c.execute("PRAGMA table_info(user_sessions)")
            columns = [row[1] for row in c.fetchall()]
            column_exists = 'user_role' in columns

        if column_exists:
            print("✅ user_role column already exists in user_sessions table")
            print("   No migration needed")
        else:
            print("⚠️  user_role column is MISSING from user_sessions table")
            print("   Adding column now...")

            # Add the column
            c.execute("ALTER TABLE user_sessions ADD COLUMN user_role TEXT")
            conn.commit()

            print("✅ user_role column added successfully!")

        # Verify the column exists now
        if db_type == 'postgresql':
            c.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='user_sessions' AND column_name='user_role'
            """)
            verified = c.fetchone() is not None
        else:
            c.execute("PRAGMA table_info(user_sessions)")
            columns = [row[1] for row in c.fetchall()]
            verified = 'user_role' in columns

        if verified:
            print("✅ MIGRATION SUCCESSFUL - user_role column is present")
        else:
            print("❌ MIGRATION FAILED - user_role column still missing")
            return False

        print("=" * 70)
        print("✅ Migration complete! You can now login without errors")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        return False
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    success = migrate_user_sessions()
    exit(0 if success else 1)
