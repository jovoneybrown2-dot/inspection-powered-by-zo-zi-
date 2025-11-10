#!/usr/bin/env python3
"""
Database migration script to add photo support to all inspection tables
"""
import sqlite3
import os

def add_photo_columns():
    """Add photo_data column to all inspection tables"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # List of tables that need photo support
    tables = [
        'inspections',
        'meat_processing_inspections',
        'residential_inspections',
        'burial_site_inspections'
    ]

    for table in tables:
        try:
            # Add photo_data column to store JSON array of photos
            c.execute(f"ALTER TABLE {table} ADD COLUMN photo_data TEXT")
            print(f"✓ Added photo_data column to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  Column already exists in {table}")
            else:
                print(f"✗ Error adding column to {table}: {e}")

    conn.commit()
    conn.close()
    print("\n✓ Database migration completed!")

def create_uploads_directory():
    """Create directory structure for storing uploaded inspection photos"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    uploads_path = os.path.join(base_path, 'static', 'uploads', 'inspections')

    try:
        os.makedirs(uploads_path, exist_ok=True)
        print(f"✓ Created uploads directory: {uploads_path}")

        # Create a .gitkeep file to preserve the directory in git
        gitkeep_path = os.path.join(uploads_path, '.gitkeep')
        with open(gitkeep_path, 'w') as f:
            f.write('')
        print(f"✓ Created .gitkeep file")

        return True
    except Exception as e:
        print(f"✗ Error creating uploads directory: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Photo Support Migration Script")
    print("=" * 60)
    print("\n1. Adding photo columns to database tables...")
    add_photo_columns()

    print("\n2. Creating uploads directory structure...")
    create_uploads_directory()

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)