#!/usr/bin/env python3
"""
Force reset SQLite database - deletes existing database and recreates with proper schema.
This runs automatically on Render startup to ensure database has correct schema.
"""
import os
import sys

def reset_database():
    """Delete and recreate the SQLite database"""
    db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')

    # Check if database exists
    if os.path.exists(db_path):
        print(f"🗑️  Deleting old database: {db_path}")
        try:
            os.remove(db_path)
            print(f"✅ Old database deleted")
        except Exception as e:
            print(f"❌ Failed to delete database: {e}")
            return False

    # Initialize new database with proper schema
    print(f"🔄 Creating fresh database with correct schema...")
    try:
        from database import init_db
        init_db()
        print(f"✅ Database created successfully with all required columns")

        # Sync barbershop checklist to ensure correct weights
        print(f"🔄 Syncing barbershop checklist weights...")
        try:
            from sync_barbershop_checklist import sync_barbershop_checklist
            sync_barbershop_checklist()
            print(f"✅ Barbershop checklist synced (100 overall, 60 critical)")
        except Exception as e:
            print(f"⚠️  Warning: Could not sync barbershop checklist: {e}")

        return True
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
