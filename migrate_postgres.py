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
        # Migration 1: Add missing columns to user_sessions table
        print("\n📋 Migration 1: Add missing columns to user_sessions table")

        # Check which columns exist
        c.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_sessions'
        """)
        existing_columns = {row[0] for row in c.fetchall()}
        print(f"   Existing columns: {existing_columns}")

        # Define required columns
        required_columns = {
            'user_role': 'VARCHAR(50)',
            'login_time': 'TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP',
            'logout_time': 'TEXT',
            'last_activity': 'TEXT',
            'location_lat': 'REAL',
            'location_lng': 'REAL',
            'parish': 'TEXT',
            'ip_address': 'TEXT',
            'is_active': 'INTEGER DEFAULT 1'
        }

        # Add missing columns
        columns_added = 0
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                try:
                    # For NOT NULL columns with no default, make them nullable
                    safe_col_type = col_type.replace('NOT NULL', '').strip()
                    c.execute(f"ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS {col_name} {safe_col_type}")
                    conn.commit()
                    print(f"   ✅ Added column: {col_name}")
                    columns_added += 1
                except Exception as e:
                    print(f"   ⚠️  Failed to add {col_name}: {e}")
                    conn.rollback()
                    errors += 1

        if columns_added == 0:
            print("   ✅ All required columns already exist")
        else:
            print(f"   ✅ Added {columns_added} missing columns")

        migrations_run += 1

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
