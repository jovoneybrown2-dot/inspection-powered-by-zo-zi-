#!/usr/bin/env python3
"""
Emergency Admin User Creator for Render PostgreSQL
Run this ONCE to create the admin user directly in the database
"""
import os
from db_config import get_db_connection, release_db_connection, get_db_type

def create_admin_user():
    """Create admin user directly in PostgreSQL database"""

    if get_db_type() != 'postgresql':
        print("❌ This script is only for PostgreSQL (Render deployment)")
        return

    print("="*70)
    print("🚨 EMERGENCY ADMIN USER CREATION")
    print("="*70)

    conn = get_db_connection()
    c = conn.cursor()

    try:
        # First, check if admin already exists
        c.execute("SELECT id, username, password FROM users WHERE username = 'admin'")
        existing_admin = c.fetchone()

        if existing_admin:
            print(f"⚠️  Admin user already exists:")
            print(f"   ID: {existing_admin[0]}")
            print(f"   Username: {existing_admin[1]}")
            print(f"   Password: {existing_admin[2]}")
            print()
            print("✅ You should be able to login with:")
            print("   Username: admin")
            print("   Password: Admin901!secure")
            return

        # Create admin user
        print("Creating admin user...")
        c.execute("""
            INSERT INTO users (username, password, role, email, parish)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE
            SET password = EXCLUDED.password,
                role = EXCLUDED.role,
                email = EXCLUDED.email,
                parish = EXCLUDED.parish
        """, ('admin', 'Admin901!secure', 'admin', 'admin@inspection.local', 'Westmoreland'))

        conn.commit()

        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print()
        print("="*70)
        print("🎉 LOGIN CREDENTIALS:")
        print("="*70)
        print("   Username: admin")
        print("   Password: Admin901!secure")
        print("="*70)
        print()
        print("✅ You can now login to your Render app!")
        print("✅ After login, you can create more admins and inspectors")
        print("   in the Admin Tools → User Management section")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.rollback()
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    create_admin_user()
