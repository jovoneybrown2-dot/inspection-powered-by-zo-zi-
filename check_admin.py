#!/usr/bin/env python3
"""
Check if admin users exist in the database
"""
from database import get_db_connection, release_db_connection

conn = get_db_connection()
cursor = conn.cursor()

try:
    # Check for admin users
    cursor.execute("SELECT id, username, email, role, parish FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()

    print("=" * 60)
    print("ADMIN USERS CHECK")
    print("=" * 60)

    if not admins:
        print("❌ NO ADMIN USERS FOUND!")
        print("\nTo create an admin user, run:")
        print("  python reset_admin_password.py YourPassword")
    else:
        print(f"✓ Found {len(admins)} admin user(s):\n")
        for admin in admins:
            print(f"  ID: {admin[0]}")
            print(f"  Username: {admin[1]}")
            print(f"  Email: {admin[2]}")
            print(f"  Role: {admin[3]}")
            print(f"  Parish: {admin[4]}")
            print()

    # Check all users
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    print(f"Total users in database: {total}")

    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    release_db_connection(conn)
