#!/usr/bin/env python3
"""
Add admin and inspector users to database
Run this if you can't login after deployment
"""

from db_config import get_db_connection, release_db_connection, get_placeholder

def add_users():
    """Add default users to the database"""
    conn = get_db_connection()
    ph = get_placeholder()

    try:
        c = conn.cursor()

        # Check if users table exists
        c.execute("SELECT COUNT(*) FROM users")
        count = c.fetchone()[0]
        print(f"Current users in database: {count}")

        # List of users to add
        users = [
            ('admin', 'Admin901!secure', 'admin'),
            ('inspector1', 'Insp123!secure', 'inspector'),
            ('inspector2', 'Insp456!secure', 'inspector'),
        ]

        added = 0
        for username, password, role in users:
            try:
                # Try to insert user
                c.execute(f"INSERT INTO users (username, password, role) VALUES ({ph}, {ph}, {ph})",
                         (username, password, role))
                conn.commit()
                print(f"✅ Added user: {username} ({role})")
                added += 1
            except Exception as e:
                # User might already exist
                if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                    print(f"⚠️  User already exists: {username}")
                else:
                    print(f"❌ Error adding {username}: {e}")
                conn.rollback()

        # List all users
        c.execute("SELECT username, role FROM users")
        all_users = c.fetchall()

        print(f"\n📋 All users in database:")
        for user in all_users:
            print(f"   - {user[0]} ({user[1]})")

        print(f"\n✅ Done! Added {added} new users")
        print(f"\nDefault credentials:")
        print(f"  Admin: username=admin, password=Admin901!secure")
        print(f"  Inspector: username=inspector1, password=Insp123!secure")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    print("🔐 Adding default users to database...\n")
    add_users()