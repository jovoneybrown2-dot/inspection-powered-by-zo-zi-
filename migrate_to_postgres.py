#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates all data from inspections.db (SQLite) to PostgreSQL database
"""

import sqlite3
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'inspections_db'),
    'user': os.getenv('DB_USER', 'inspector_app'),
    'password': os.getenv('DB_PASSWORD', 'your_secure_password'),
    'port': os.getenv('DB_PORT', '5432')
}

SQLITE_DB = 'inspections.db'

def connect_sqlite():
    """Connect to SQLite database"""
    return sqlite3.connect(SQLITE_DB)

def connect_postgres():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(**PG_CONFIG)

def migrate_users():
    """Migrate users table"""
    print("Migrating users...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all users from SQLite
    sqlite_cursor.execute("SELECT id, username, password, role, is_flagged, last_login, is_active, email FROM users")
    users = sqlite_cursor.fetchall()

    migrated = 0
    for user in users:
        try:
            # Convert SQLite integers to PostgreSQL booleans
            user_data = list(user)
            user_data[4] = bool(user_data[4]) if user_data[4] is not None else False  # is_flagged
            user_data[6] = bool(user_data[6]) if user_data[6] is not None else True   # is_active

            pg_cursor.execute("""
                INSERT INTO users (id, username, password, role, is_flagged, last_login, is_active, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, tuple(user_data))
            migrated += 1
        except Exception as e:
            print(f"Error migrating user {user[1]}: {e}")

    pg_conn.commit()

    # Update sequence to match last ID
    pg_cursor.execute("SELECT MAX(id) FROM users")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('users_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} users")

def migrate_inspections():
    """Migrate inspections table"""
    print("Migrating inspections...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all inspections from SQLite
    sqlite_cursor.execute("SELECT * FROM inspections")
    inspections = sqlite_cursor.fetchall()

    # Get column names
    column_names = [description[0] for description in sqlite_cursor.description]

    migrated = 0
    for inspection in inspections:
        try:
            # Create placeholders for SQL
            placeholders = ', '.join(['%s'] * len(inspection))
            columns = ', '.join(column_names)

            pg_cursor.execute(f"""
                INSERT INTO inspections ({columns})
                VALUES ({placeholders})
                ON CONFLICT (id) DO NOTHING
            """, inspection)
            migrated += 1
        except Exception as e:
            print(f"Error migrating inspection {inspection[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    pg_cursor.execute("SELECT MAX(id) FROM inspections")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('inspections_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} inspections")

def migrate_inspection_items():
    """Migrate inspection_items table"""
    print("Migrating inspection items...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT id, inspection_id, item_id, details, obser, error FROM inspection_items")
    items = sqlite_cursor.fetchall()

    migrated = 0
    for item in items:
        try:
            pg_cursor.execute("""
                INSERT INTO inspection_items (id, inspection_id, item_id, details, obser, error)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, item)
            migrated += 1
        except Exception as e:
            print(f"Error migrating inspection item {item[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    pg_cursor.execute("SELECT MAX(id) FROM inspection_items")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('inspection_items_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} inspection items")

def migrate_burial_inspections():
    """Migrate burial_site_inspections table"""
    print("Migrating burial inspections...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT * FROM burial_site_inspections")
    inspections = sqlite_cursor.fetchall()

    migrated = 0
    for inspection in inspections:
        try:
            pg_cursor.execute("""
                INSERT INTO burial_site_inspections
                (id, inspection_date, applicant_name, deceased_name, burial_location, site_description,
                 proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway,
                 proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks,
                 inspector_signature, received_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, inspection)
            migrated += 1
        except Exception as e:
            print(f"Error migrating burial inspection {inspection[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    pg_cursor.execute("SELECT MAX(id) FROM burial_site_inspections")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('burial_site_inspections_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} burial inspections")

def migrate_residential_inspections():
    """Migrate residential_inspections table"""
    print("Migrating residential inspections...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT * FROM residential_inspections")
    inspections = sqlite_cursor.fetchall()

    # Get column names
    column_names = [description[0] for description in sqlite_cursor.description]

    migrated = 0
    for inspection in inspections:
        try:
            placeholders = ', '.join(['%s'] * len(inspection))
            columns = ', '.join(column_names)

            pg_cursor.execute(f"""
                INSERT INTO residential_inspections ({columns})
                VALUES ({placeholders})
                ON CONFLICT (id) DO NOTHING
            """, inspection)
            migrated += 1
        except Exception as e:
            print(f"Error migrating residential inspection {inspection[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    pg_cursor.execute("SELECT MAX(id) FROM residential_inspections")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('residential_inspections_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} residential inspections")

def migrate_residential_checklist_scores():
    """Migrate residential_checklist_scores table"""
    print("Migrating residential checklist scores...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    sqlite_cursor.execute("SELECT id, form_id, item_id, score FROM residential_checklist_scores")
    scores = sqlite_cursor.fetchall()

    migrated = 0
    for score in scores:
        try:
            pg_cursor.execute("""
                INSERT INTO residential_checklist_scores (id, form_id, item_id, score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, score)
            migrated += 1
        except Exception as e:
            print(f"Error migrating checklist score {score[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    pg_cursor.execute("SELECT MAX(id) FROM residential_checklist_scores")
    max_id = pg_cursor.fetchone()[0]
    if max_id:
        pg_cursor.execute(f"SELECT setval('residential_checklist_scores_id_seq', {max_id})")
        pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} residential checklist scores")

def migrate_messages():
    """Migrate messages table"""
    print("Migrating messages...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Try to get messages - handle if receiver_id column doesn't exist
    try:
        sqlite_cursor.execute("SELECT id, sender_id, receiver_id, content, timestamp, is_read FROM messages")
    except sqlite3.OperationalError:
        # Try with recipient_id if receiver_id doesn't exist
        try:
            sqlite_cursor.execute("SELECT id, sender_id, recipient_id, content, timestamp, is_read FROM messages")
        except:
            print("Could not find messages table or compatible schema")
            return

    messages = sqlite_cursor.fetchall()

    migrated = 0
    for message in messages:
        try:
            pg_cursor.execute("""
                INSERT INTO messages (id, sender_id, receiver_id, content, timestamp, is_read)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, message)
            migrated += 1
        except Exception as e:
            print(f"Error migrating message {message[0]}: {e}")

    pg_conn.commit()

    # Update sequence
    if migrated > 0:
        pg_cursor.execute("SELECT MAX(id) FROM messages")
        max_id = pg_cursor.fetchone()[0]
        if max_id:
            pg_cursor.execute(f"SELECT setval('messages_id_seq', {max_id})")
            pg_conn.commit()

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

    print(f"Migrated {migrated} messages")

def migrate_contacts():
    """Migrate contacts table"""
    print("Migrating contacts...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    try:
        sqlite_cursor.execute("SELECT user_id, contact_id FROM contacts")
        contacts = sqlite_cursor.fetchall()

        migrated = 0
        for contact in contacts:
            try:
                pg_cursor.execute("""
                    INSERT INTO contacts (user_id, contact_id)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, contact_id) DO NOTHING
                """, contact)
                migrated += 1
            except Exception as e:
                print(f"Error migrating contact: {e}")

        pg_conn.commit()
        print(f"Migrated {migrated} contacts")
    except sqlite3.OperationalError:
        print("No contacts table found or empty")

    sqlite_cursor.close()
    pg_cursor.close()
    sqlite_conn.close()
    pg_conn.close()

def main():
    """Run all migrations"""
    print("="*60)
    print("SQLite to PostgreSQL Migration")
    print("="*60)
    print(f"Source: {SQLITE_DB}")
    print(f"Destination: {PG_CONFIG['database']} @ {PG_CONFIG['host']}")
    print("="*60)

    # Test connections
    try:
        sqlite_conn = connect_sqlite()
        print("✓ SQLite connection successful")
        sqlite_conn.close()
    except Exception as e:
        print(f"✗ SQLite connection failed: {e}")
        return

    try:
        pg_conn = connect_postgres()
        print("✓ PostgreSQL connection successful")
        pg_conn.close()
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        print("Make sure PostgreSQL is running and schema is created!")
        return

    print("\nStarting migration...\n")

    # Run migrations in order (respecting foreign keys)
    migrate_users()
    migrate_contacts()
    migrate_messages()
    migrate_inspections()
    migrate_inspection_items()
    migrate_burial_inspections()
    migrate_residential_inspections()
    migrate_residential_checklist_scores()

    print("\n" + "="*60)
    print("Migration completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python verify_migration.py")
    print("2. Test your application with PostgreSQL")
    print("3. Keep SQLite backup until you're confident")

if __name__ == "__main__":
    main()
