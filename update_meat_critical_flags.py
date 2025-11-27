#!/usr/bin/env python3
"""
Migration script to update meat processing inspection critical flags.
Run this on Render after deployment to update the Postgres database.
"""

import os
import sys
import sqlite3

# Try to import psycopg2 for Postgres
try:
    import psycopg2
    from psycopg2 import sql
    USE_POSTGRES = True
except ImportError:
    USE_POSTGRES = False

def get_connection():
    """Get database connection (Postgres on Render, SQLite locally)."""
    if USE_POSTGRES and os.environ.get('DATABASE_URL'):
        # Render Postgres
        database_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(database_url)
        return conn, 'postgres'
    else:
        # Local SQLite
        conn = sqlite3.connect('inspections.db')
        return conn, 'sqlite'

def update_meat_critical_flags():
    """Update critical flags for meat processing inspection items."""
    conn, db_type = get_connection()
    cursor = conn.cursor()

    print(f"Connected to {db_type} database")
    print("Updating meat processing critical flags...")

    # Items that should be NON-critical (remove critical flag)
    non_critical_items = ['13', '46', '47']

    # Items that should be critical (add critical flag)
    critical_items = ['31', '34', '35', '38', '39', '43', '51']

    try:
        # First, get the template ID
        if db_type == 'postgres':
            cursor.execute("SELECT id FROM form_templates WHERE form_type LIKE %s OR name LIKE %s", ('%Meat%', '%Meat%'))
        else:
            cursor.execute("SELECT id FROM form_templates WHERE form_type LIKE ? OR name LIKE ?", ('%Meat%', '%Meat%'))

        template = cursor.fetchone()
        if not template:
            print("❌ Error: Meat Processing template not found in database!")
            return

        template_id = template[0]
        print(f"Found template ID: {template_id}")

        # Remove critical flag from specified items
        for item_id in non_critical_items:
            if db_type == 'postgres':
                cursor.execute("""
                    UPDATE form_items
                    SET is_critical = 0
                    WHERE item_id = %s AND form_template_id = %s
                """, (item_id, template_id))
            else:
                cursor.execute("""
                    UPDATE form_items
                    SET is_critical = 0
                    WHERE item_id = ? AND form_template_id = ?
                """, (item_id, template_id))
            print(f"  ✓ Item {item_id}: Set to NON-critical (rows affected: {cursor.rowcount})")

        # Add critical flag to specified items
        for item_id in critical_items:
            if db_type == 'postgres':
                cursor.execute("""
                    UPDATE form_items
                    SET is_critical = 1
                    WHERE item_id = %s AND form_template_id = %s
                """, (item_id, template_id))
            else:
                cursor.execute("""
                    UPDATE form_items
                    SET is_critical = 1
                    WHERE item_id = ? AND form_template_id = ?
                """, (item_id, template_id))
            print(f"  ✓ Item {item_id}: Set to CRITICAL (rows affected: {cursor.rowcount})")

        conn.commit()
        print("\n✅ Successfully updated meat processing critical flags!")

        # Verify the changes
        print("\nVerifying changes...")
        all_items = non_critical_items + critical_items

        if db_type == 'postgres':
            placeholders = ', '.join(['%s'] * len(all_items))
            cursor.execute(f"""
                SELECT item_id, description, is_critical
                FROM form_items
                WHERE form_template_id = %s
                AND item_id IN ({placeholders})
                ORDER BY item_id::INTEGER
            """, (template_id, *all_items))
        else:
            placeholders = ', '.join(['?'] * len(all_items))
            cursor.execute(f"""
                SELECT item_id, description, is_critical
                FROM form_items
                WHERE form_template_id = ?
                AND item_id IN ({placeholders})
                ORDER BY CAST(item_id AS INTEGER)
            """, (template_id, *all_items))

        results = cursor.fetchall()
        print("\nUpdated items:")
        for item_id, description, is_critical in results:
            status = "CRITICAL" if is_critical else "non-critical"
            desc_short = description[:60] + "..." if len(description) > 60 else description
            print(f"  {item_id}: {status} - {desc_short}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error updating database: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 70)
    print("MEAT PROCESSING INSPECTION - CRITICAL FLAGS UPDATE")
    print("=" * 70)
    update_meat_critical_flags()
    print("=" * 70)
