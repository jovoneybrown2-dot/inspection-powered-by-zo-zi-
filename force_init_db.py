#!/usr/bin/env python3
"""
Force Database Initialization Script
Run this to create ALL missing tables in PostgreSQL
"""
import os
from db_config import get_db_connection, release_db_connection, get_db_type

def force_init_database():
    """Force initialization of all database tables"""

    print("=" * 70)
    print("🔨 FORCE DATABASE INITIALIZATION")
    print("=" * 70)

    db_type = get_db_type()
    print(f"\nDatabase type: {db_type}")

    if db_type != 'postgresql':
        print("⚠️  This script is for PostgreSQL only")
        return False

    conn = get_db_connection()
    c = conn.cursor()

    try:
        # Import database initialization
        from database import init_db
        from form_management_system import init_form_management_db

        print("\n🔄 Step 1: Initializing core database tables...")
        init_db()
        print("   ✅ Core tables initialized")

        print("\n🔄 Step 2: Initializing form management tables...")
        init_form_management_db()
        print("   ✅ Form management tables initialized")

        # List all tables
        print("\n📋 Checking created tables...")
        c.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = c.fetchall()

        if tables:
            print(f"\n✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   • {table[0]}")
        else:
            print("   ❌ No tables found!")
            return False

        # Verify critical tables exist
        critical_tables = ['inspections', 'users', 'user_sessions', 'form_templates', 'form_items']
        print(f"\n🔍 Verifying critical tables...")

        existing_table_names = [t[0] for t in tables]
        all_exist = True

        for table in critical_tables:
            if table in existing_table_names:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - MISSING!")
                all_exist = False

        if all_exist:
            print("\n" + "=" * 70)
            print("✅ DATABASE INITIALIZATION SUCCESSFUL!")
            print("=" * 70)
            print("\nYou can now:")
            print("  • Login as inspector/admin")
            print("  • Create inspections")
            print("  • View dashboard without errors")
            print("=" * 70)
            return True
        else:
            print("\n❌ Some critical tables are missing!")
            return False

    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    success = force_init_database()
    exit(0 if success else 1)
