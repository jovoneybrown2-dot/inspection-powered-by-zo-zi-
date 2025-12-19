#!/usr/bin/env python3
"""
Initialize database and sync checklists on startup.
PRESERVES existing data - does NOT delete the database.
Only ensures schema exists and checklists are up to date.
"""
import os
import sys

def init_database():
    """Initialize database schema and sync checklists WITHOUT deleting data"""
    db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')

    # Check if database exists
    if os.path.exists(db_path):
        print(f"✓ Found existing database: {db_path}")
        print(f"  Preserving all existing inspection data...")
    else:
        print(f"📁 Creating new database: {db_path}")

    # Initialize database schema (only creates tables if they don't exist)
    print(f"🔄 Ensuring database schema is up to date...")
    try:
        from database import init_db
        init_db()
        print(f"✅ Database schema initialized")

        # Sync ALL form checklists to ensure correct weights
        print(f"🔄 Syncing all form checklists...")
        try:
            from sync_all_checklists import sync_all_checklists
            sync_all_checklists()
            print(f"✅ All form checklists synced")
        except Exception as e:
            print(f"⚠️  Warning: Could not sync form checklists: {e}")

        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
