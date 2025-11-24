"""
Migration script to add signature date columns to inspections table
Run this manually if the automatic migration doesn't work
"""
from db_config import get_db_connection

def migrate_signature_dates():
    """Add signature date columns to inspections table"""
    conn = get_db_connection()
    cursor = conn.cursor()

    columns = [
        'inspector_signature_date',
        'manager_signature_date',
        'received_by_date'
    ]

    for column in columns:
        try:
            print(f"Adding column: {column}")
            cursor.execute(f"ALTER TABLE inspections ADD COLUMN {column} TEXT")
            conn.commit()
            print(f"✓ Successfully added {column}")
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print(f"⚠ Column {column} already exists, skipping")
            else:
                print(f"✗ Error adding {column}: {e}")
            conn.rollback()

    conn.close()
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate_signature_dates()
