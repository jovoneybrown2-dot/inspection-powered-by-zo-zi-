#!/usr/bin/env python3
"""
Database Initialization Script for Docker
Automatically detects and initializes SQLite or PostgreSQL
"""
import os
import sys
import time


def wait_for_database():
    """Wait for PostgreSQL to be ready (if using PostgreSQL)"""
    from db_config import get_db_type, get_db_connection

    db_type = get_db_type()

    if db_type == 'postgresql':
        print("🐘 Waiting for PostgreSQL to be ready...")
        max_retries = 30
        retry_count = 0

        while retry_count < max_retries:
            try:
                conn = get_db_connection()
                conn.close()
                print("✅ PostgreSQL is ready!")
                return True
            except Exception as e:
                retry_count += 1
                print(f"⏳ Attempt {retry_count}/{max_retries}: Waiting for database... ({str(e)})")
                time.sleep(2)

        print("❌ Could not connect to PostgreSQL after 30 attempts")
        return False
    else:
        print("📁 Using SQLite - no wait needed")
        return True


def initialize_database():
    """Initialize database schema"""
    from db_config import init_database

    try:
        init_database()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main initialization function"""
    print("=" * 60)
    print("🚀 Food Inspection Management System - Database Initialization")
    print("=" * 60)

    # Step 1: Wait for database to be available
    if not wait_for_database():
        sys.exit(1)

    # Step 2: Initialize database schema
    print("\n📊 Initializing database schema...")
    if not initialize_database():
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Database initialization complete!")
    print("=" * 60)
    print("\n🎉 System is ready to use!")


if __name__ == "__main__":
    main()
