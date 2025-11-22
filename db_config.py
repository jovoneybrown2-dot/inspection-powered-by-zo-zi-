"""
Database Abstraction Layer
Supports both SQLite (development) and PostgreSQL (production)
Switch between databases using the DATABASE_URL environment variable
"""
import os
import sqlite3
from urllib.parse import urlparse


class HybridRow:
    """Row class that supports both numeric indexing and dictionary access"""
    def __init__(self, cursor, row):
        self._row = row
        self._columns = [desc[0] for desc in cursor.description]

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        elif isinstance(key, str):
            try:
                index = self._columns.index(key)
                return self._row[index]
            except ValueError:
                raise KeyError(key)
        else:
            raise TypeError(f"indices must be integers or strings, not {type(key).__name__}")

    def __len__(self):
        return len(self._row)

    def keys(self):
        return self._columns

    def values(self):
        return list(self._row)

    def items(self):
        return zip(self._columns, self._row)

    def __iter__(self):
        return iter(self._row)


def get_db_connection():
    """
    Get database connection based on DATABASE_URL environment variable.

    Returns:
        Database connection object (SQLite or PostgreSQL)

    Examples:
        # SQLite (default for development)
        DATABASE_URL not set → uses inspections.db

        # PostgreSQL (production)
        DATABASE_URL=postgresql://user:pass@host:5432/dbname
    """
    database_url = os.getenv('DATABASE_URL', '')

    # Check if PostgreSQL is configured
    if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
        # Use PostgreSQL
        try:
            import psycopg2
            import psycopg2.extras

            # Custom cursor class that uses HybridRow
            class HybridCursor(psycopg2.extensions.cursor):
                def fetchone(self):
                    row = super().fetchone()
                    return HybridRow(self, row) if row else None

                def fetchmany(self, size=None):
                    rows = super().fetchmany(size) if size else super().fetchmany()
                    return [HybridRow(self, row) for row in rows]

                def fetchall(self):
                    rows = super().fetchall()
                    return [HybridRow(self, row) for row in rows]

            # Parse the DATABASE_URL
            parsed = urlparse(database_url)

            # Handle both postgres:// and postgresql:// schemes
            # Some providers (like Heroku) use postgres:// but psycopg2 needs postgresql://
            if parsed.scheme == 'postgres':
                database_url = database_url.replace('postgres://', 'postgresql://', 1)

            # Connect to PostgreSQL with custom cursor
            print(f"🔌 Connecting to PostgreSQL: {parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}")
            conn = psycopg2.connect(database_url, cursor_factory=HybridCursor)
            conn.autocommit = False  # Enable transaction control

            print("✅ PostgreSQL connection successful!")
            return conn

        except ImportError as e:
            print(f"⚠️  PostgreSQL import failed: {e}")
            print("   Falling back to SQLite.")
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}")
            print(f"   Database URL format: {parsed.hostname if 'parsed' in locals() else 'Could not parse'}")
            print("   Falling back to SQLite.")

    # Use SQLite (default)
    db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Make rows accessible by column name
    return conn


def dict_factory(cursor, row):
    """
    Convert PostgreSQL row to dictionary (similar to sqlite3.Row)
    """
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def get_db_type():
    """
    Returns the current database type being used.

    Returns:
        str: 'postgresql' or 'sqlite'
    """
    database_url = os.getenv('DATABASE_URL', '')
    if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
        return 'postgresql'
    return 'sqlite'


def get_placeholder():
    """
    Returns the correct parameter placeholder for the current database.

    SQLite uses: ?
    PostgreSQL uses: %s

    Returns:
        str: '?' for SQLite, '%s' for PostgreSQL

    Example:
        placeholder = get_placeholder()
        query = f"SELECT * FROM users WHERE id = {placeholder}"
    """
    return '%s' if get_db_type() == 'postgresql' else '?'


def execute_query(conn, query, params=None):
    """
    Execute a query with automatic placeholder conversion.

    Args:
        conn: Database connection
        query: SQL query with ? or %s placeholders
        params: Query parameters (tuple or list)

    Returns:
        Cursor object with results

    Example:
        conn = get_db_connection()
        results = execute_query(conn, "SELECT * FROM users WHERE id = ?", (user_id,))
    """
    db_type = get_db_type()

    # Convert placeholders based on database type
    if db_type == 'postgresql' and '?' in query:
        # Convert SQLite placeholders (?) to PostgreSQL (%s)
        query = query.replace('?', '%s')
    elif db_type == 'sqlite' and '%s' in query:
        # Convert PostgreSQL placeholders (%s) to SQLite (?)
        query = query.replace('%s', '?')

    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    return cursor


def init_database():
    """
    Initialize database schema.
    Should be run on first startup or after database reset.
    """
    from database import init_db

    print(f"🗄️  Initializing {get_db_type().upper()} database...")
    init_db()
    print("✅ Database initialized successfully!")


# Display database info on import
if __name__ != "__main__":
    db_type = get_db_type()
    if db_type == 'postgresql':
        db_url = os.getenv('DATABASE_URL', '')
        parsed = urlparse(db_url)
        print(f"🐘 Using PostgreSQL: {parsed.hostname}:{parsed.port}/{parsed.path.lstrip('/')}")
    else:
        db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')
        print(f"📁 Using SQLite: {db_path}")
