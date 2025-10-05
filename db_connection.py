"""
Database Connection Helper
Provides a unified interface for database connections
Switch between SQLite and PostgreSQL by changing USE_POSTGRESQL flag
"""

import os
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION: Set to True to use PostgreSQL, False to use SQLite
USE_POSTGRESQL = os.getenv('USE_POSTGRESQL', 'True').lower() == 'true'

if USE_POSTGRESQL:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'inspections_db'),
        'user': os.getenv('DB_USER', 'inspector_app'),
        'password': os.getenv('DB_PASSWORD', 'your_secure_password'),
        'port': os.getenv('DB_PORT', '5432')
    }

    def get_db_connection(timeout=10):
        """Get PostgreSQL database connection"""
        return psycopg2.connect(**DB_CONFIG)

    def get_placeholder():
        """Get SQL placeholder for PostgreSQL"""
        return '%s'

else:
    import sqlite3

    def get_db_connection(timeout=10):
        """Get SQLite database connection"""
        conn = sqlite3.connect('inspections.db', timeout=timeout)
        conn.row_factory = sqlite3.Row
        return conn

    def get_placeholder():
        """Get SQL placeholder for SQLite"""
        return '?'

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with automatic connection handling

    Args:
        query: SQL query string
        params: Query parameters (tuple or list)
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit changes

    Returns:
        Query results or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            conn.commit()
            if USE_POSTGRESQL and 'RETURNING' in query.upper():
                result = cursor.fetchone()

        return result
    except Exception as e:
        print(f"Database error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# Print current database mode on import
if __name__ != "__main__":
    db_type = "PostgreSQL" if USE_POSTGRESQL else "SQLite"
    print(f"Database connection mode: {db_type}")
