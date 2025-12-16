#!/usr/bin/env python3
"""
Reset admin password
"""
from database import get_db_connection, release_db_connection
from db_config import get_placeholder

def reset_admin_password(new_password="admin123"):
    """Reset admin password to a known value"""
    ph = get_placeholder()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check for admin users
        cursor.execute(f"SELECT id, username, email, role FROM users WHERE role = {ph}", ('admin',))
        admins = cursor.fetchall()

        if not admins:
            print("❌ No admin users found in database")
            print("   Creating a default admin user...")

            # Create default admin
            cursor.execute(f"""
                INSERT INTO users (username, email, password, role, parish, first_login)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, 0)
            """, ('admin', 'admin@inspection.gov.jm', new_password, 'admin', 'Kingston', 0))
            conn.commit()
            print(f"✓ Created admin user with password: {new_password}")

        else:
            print(f"Found {len(admins)} admin user(s):")
            for admin in admins:
                print(f"  - ID: {admin[0]}, Username: {admin[1]}, Email: {admin[2]}")

            # Reset password for first admin
            first_admin_id = admins[0][0]
            cursor.execute(f"UPDATE users SET password = {ph}, first_login = 0 WHERE id = {ph}",
                          (new_password, first_admin_id))
            conn.commit()
            print(f"\n✓ Reset password for admin (ID: {first_admin_id})")
            print(f"  Username: {admins[0][1]}")
            print(f"  New password: {new_password}")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    import sys

    password = sys.argv[1] if len(sys.argv) > 1 else "admin123"

    print("=" * 50)
    print("Admin Password Reset Tool")
    print("=" * 50)
    print(f"New password: {password}")
    print()

    reset_admin_password(password)

    print("\n" + "=" * 50)
    print("✓ Done! You can now login with:")
    print(f"  Password: {password}")
    print("=" * 50)
