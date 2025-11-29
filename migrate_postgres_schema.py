#!/usr/bin/env python3
"""
Migration script to add missing tables and columns to PostgreSQL database
"""
from db_config import get_db_connection

def run_migration():
    """Add missing tables and columns"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Add threshold_alerts table with all required columns
        print("Creating/updating threshold_alerts table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threshold_alerts (
                id SERIAL PRIMARY KEY,
                inspection_id INTEGER NOT NULL,
                inspector_name TEXT NOT NULL,
                form_type TEXT NOT NULL,
                score REAL NOT NULL,
                threshold_value REAL NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Check if acknowledged column exists, if not add it
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='threshold_alerts' AND column_name='acknowledged'
        """)
        if not cursor.fetchone():
            print("Adding acknowledged column...")
            cursor.execute("ALTER TABLE threshold_alerts ADD COLUMN acknowledged INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE threshold_alerts ADD COLUMN acknowledged_by TEXT")
            cursor.execute("ALTER TABLE threshold_alerts ADD COLUMN acknowledged_at TIMESTAMP")

        conn.commit()
        print("✅ threshold_alerts table updated successfully")

        # Ensure tasks table exists
        print("Checking tasks table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'tasks'
            )
        """)
        tasks_exists = cursor.fetchone()[0]

        if not tasks_exists:
            print("Creating tasks table...")
            cursor.execute('''
                CREATE TABLE tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    assignee_id INTEGER,
                    assignee_name TEXT,
                    due_date TIMESTAMP,
                    details TEXT,
                    status TEXT DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ tasks table created successfully")
        else:
            # Check if status column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='tasks'
            """)
            task_columns = [row[0] for row in cursor.fetchall()]

            if 'status' not in task_columns:
                print("Adding status column to tasks...")
                cursor.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'Pending'")
                conn.commit()

            print("✅ tasks table updated successfully")

        # Ensure users table has is_flagged column
        print("Checking users table...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='users'
        """)
        user_columns = [row[0] for row in cursor.fetchall()]

        if 'is_flagged' not in user_columns:
            print("Adding is_flagged column to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_flagged INTEGER DEFAULT 0")
            conn.commit()

        print("✅ users table updated successfully")

        # Add critical_score to meat_processing_inspections
        print("Checking meat_processing_inspections table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'meat_processing_inspections'
            )
        """)
        meat_table_exists = cursor.fetchone()[0]

        if meat_table_exists:
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='meat_processing_inspections'
            """)
            meat_columns = [row[0] for row in cursor.fetchall()]

            if 'critical_score' not in meat_columns:
                print("Adding critical_score column to meat_processing_inspections...")
                cursor.execute("ALTER TABLE meat_processing_inspections ADD COLUMN critical_score REAL DEFAULT 0")
                conn.commit()
                print("✅ Added critical_score column to meat_processing_inspections")
            else:
                print("✅ meat_processing_inspections already has critical_score column")

            if 'photo_data' not in meat_columns:
                print("Adding photo_data column to meat_processing_inspections...")
                cursor.execute("ALTER TABLE meat_processing_inspections ADD COLUMN photo_data TEXT DEFAULT '[]'")
                conn.commit()
                print("✅ Added photo_data column to meat_processing_inspections")
            else:
                print("✅ meat_processing_inspections already has photo_data column")

        print("\n" + "="*60)
        print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY")
        print("="*60)

    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
