#!/usr/bin/env python3
"""
Migration script to update meat processing inspection critical flags.
Run this on Render after deployment to update the Postgres database.
"""

import os
import sys

# Try to import psycopg2 for Postgres, fall back to sqlite3 for local testing
try:
    import psycopg2
    from psycopg2 import sql
    USE_POSTGRES = True
except ImportError:
    import sqlite3
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
        # Remove critical flag from specified items
        for item_id in non_critical_items:
            cursor.execute("""
                UPDATE form_items
                SET is_critical = 0
                WHERE item_id = %s
                AND form_template_id IN (
                    SELECT id FROM form_templates WHERE name LIKE %s
                )
            """ if db_type == 'postgres' else """
                UPDATE form_items
                SET is_critical = 0
                WHERE item_id = ?
                AND form_template_id IN (
                    SELECT id FROM form_templates WHERE name LIKE ?
                )
            """, (item_id, '%Meat%'))
            print(f"  ✓ Item {item_id}: Set to NON-critical")

        # Add critical flag to specified items
        for item_id in critical_items:
            cursor.execute("""
                UPDATE form_items
                SET is_critical = 1
                WHERE item_id = %s
                AND form_template_id IN (
                    SELECT id FROM form_templates WHERE name LIKE %s
                )
            """ if db_type == 'postgres' else """
                UPDATE form_items
                SET is_critical = 1
                WHERE item_id = ?
                AND form_template_id IN (
                    SELECT id FROM form_templates WHERE name LIKE ?
                )
            """, (item_id, '%Meat%'))
            print(f"  ✓ Item {item_id}: Set to CRITICAL")

        conn.commit()
        print("\n✅ Successfully updated meat processing critical flags!")

        # Verify the changes
        print("\nVerifying changes...")
        cursor.execute("""
            SELECT item_id, description, is_critical
            FROM form_items
            WHERE form_template_id IN (
                SELECT id FROM form_templates WHERE name LIKE %s
            )
            AND item_id IN %s
            ORDER BY CAST(item_id AS INTEGER)
        """ if db_type == 'postgres' else """
            SELECT item_id, description, is_critical
            FROM form_items
            WHERE form_template_id IN (
                SELECT id FROM form_templates WHERE name LIKE ?
            )
            AND item_id IN ('13','31','34','35','38','39','43','46','47','51')
            ORDER BY CAST(item_id AS INTEGER)
        """, ('%Meat%', tuple(non_critical_items + critical_items)) if db_type == 'postgres' else ('%Meat%',))

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
