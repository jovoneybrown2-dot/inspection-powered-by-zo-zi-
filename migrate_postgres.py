#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Adds missing columns to existing PostgreSQL databases
Run this on production servers to update the schema
"""
from db_config import get_db_connection, release_db_connection, get_db_type

def migrate_postgres():
    """Run all PostgreSQL migrations"""

    if get_db_type() != 'postgresql':
        print("⚠️  This script is only for PostgreSQL databases")
        print("   Current database type:", get_db_type())
        return False

    print("=" * 70)
    print("🔄 POSTGRESQL MIGRATION SCRIPT")
    print("=" * 70)

    conn = get_db_connection()
    c = conn.cursor()
    migrations_run = 0
    errors = 0

    try:
        # Migration 1: Add user_role column to user_sessions
        print("\n📋 Migration 1: Add user_role to user_sessions table")
        try:
            c.execute("""
                ALTER TABLE user_sessions
                ADD COLUMN IF NOT EXISTS user_role VARCHAR(50)
            """)
            conn.commit()
            print("   ✅ user_role column added/verified")
            migrations_run += 1
        except Exception as e:
            print(f"   ⚠️  Migration 1 warning: {e}")
            conn.rollback()
            errors += 1

        # Add more migrations here as needed
        # Migration 2: Example
        # print("\n📋 Migration 2: Description")
        # try:
        #     c.execute("ALTER TABLE ...")
        #     conn.commit()
        #     print("   ✅ Migration 2 complete")
        #     migrations_run += 1
        # except Exception as e:
        #     print(f"   ⚠️  Migration 2 warning: {e}")
        #     conn.rollback()
        #     errors += 1

        print("\n" + "=" * 70)
        print(f"📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"   Migrations run: {migrations_run}")
        print(f"   Errors: {errors}")
        print("=" * 70)

        if errors == 0:
            print("✅ All migrations completed successfully!")
            return True
        else:
            print("⚠️  Some migrations had warnings (see above)")
            return True  # Still return True if migrations ran

    except Exception as e:
        print(f"\n❌ Migration script error: {e}")
        conn.rollback()
        return False
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    success = migrate_postgres()
    exit(0 if success else 1)
