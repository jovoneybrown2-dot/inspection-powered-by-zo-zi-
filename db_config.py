"""
Database Abstraction Layer
Supports both SQLite (development) and PostgreSQL (production)
Switch between databases using the DATABASE_URL environment variable
Includes connection pooling for PostgreSQL to handle concurrent users
"""
import os
import sqlite3
from urllib.parse import urlparse
from contextlib import contextmanager

# Global connection pool (initialized on first use)
_connection_pool = None


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


def _init_connection_pool():
    """
    Initialize PostgreSQL connection pool (called once on first connection).

    Pool configuration:
    - minconn: Minimum connections kept alive (5)
    - maxconn: Maximum connections allowed (20)
    - These limits prevent overwhelming PostgreSQL server
    """
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    database_url = os.getenv('DATABASE_URL', '')

    if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
        try:
            import psycopg2.pool
            from psycopg2.extensions import cursor as BaseCursor

            # Parse the DATABASE_URL
            parsed = urlparse(database_url)

            # Handle both postgres:// and postgresql:// schemes
            if parsed.scheme == 'postgres':
                database_url = database_url.replace('postgres://', 'postgresql://', 1)

            # Create threaded connection pool
            print(f"🔌 Initializing PostgreSQL connection pool...")
            print(f"   Host: {parsed.hostname}:{parsed.port}")
            print(f"   Database: {parsed.path.lstrip('/')}")

            _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,   # Keep 5 connections always ready
                maxconn=20,  # Allow up to 20 concurrent connections
                dsn=database_url
            )

            print("✅ PostgreSQL connection pool initialized (5-20 connections)")
            return _connection_pool

        except ImportError as e:
            print(f"⚠️  PostgreSQL pool import failed: {e}")
            return None
        except Exception as e:
            print(f"⚠️  PostgreSQL pool initialization failed: {e}")
            return None

    return None


def get_db_connection():
    """
    Get database connection from pool (PostgreSQL) or direct connection (SQLite).

    For PostgreSQL: Returns a connection from the pool (fast, reusable)
    For SQLite: Returns a new connection (suitable for development)

    Returns:
        Database connection object (SQLite or PostgreSQL)

    IMPORTANT: For PostgreSQL, you MUST return the connection using
    release_db_connection() or use the get_db_context() context manager.

    Examples:
        # SQLite (default for development)
        DATABASE_URL not set → uses inspections.db

        # PostgreSQL (production)
        DATABASE_URL=postgresql://user:pass@host:5432/dbname
    """
    database_url = os.getenv('DATABASE_URL', '')

    # Check if PostgreSQL is configured
    if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
        # Use PostgreSQL with connection pooling
        try:
            import psycopg2
            import psycopg2.extras

            # Initialize pool if not already done
            pool = _init_connection_pool()

            if pool is None:
                raise Exception("Connection pool not available")

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

            # Get connection from pool
            conn = pool.getconn()

            # Set custom cursor factory
            conn.cursor_factory = HybridCursor
            conn.autocommit = False  # Enable transaction control

            return conn

        except ImportError as e:
            print(f"⚠️  PostgreSQL import failed: {e}")
            print("   Falling back to SQLite.")
        except Exception as e:
            print(f"⚠️  PostgreSQL connection failed: {e}")
            print("   Falling back to SQLite.")

    # Use SQLite (default)
    db_path = os.getenv('SQLITE_DB_PATH', 'inspections.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Make rows accessible by column name
    return conn


def release_db_connection(conn, error=False):
    """
    Return a PostgreSQL connection to the pool, or close SQLite connection.

    If there was an error, the connection is closed instead of returned to pool
    to prevent bad connections from contaminating the pool.

    Args:
        conn: Database connection to release
        error: True if connection had an error (will be discarded)

    Example:
        conn = get_db_connection()
        try:
            # ... use connection ...
        except Exception as e:
            release_db_connection(conn, error=True)
            raise
        finally:
            release_db_connection(conn)
    """
    if conn is None:
        return

    database_url = os.getenv('DATABASE_URL', '')

    if database_url and (database_url.startswith('postgres://') or database_url.startswith('postgresql://')):
        # Return PostgreSQL connection to pool (or close if errored)
        if _connection_pool is not None:
            try:
                if error:
                    # Connection had an error - close it instead of returning to pool
                    print(f"⚠️ Discarding bad connection from pool")
                    conn.close()
                    # Don't putconn - let pool create a fresh one
                else:
                    # Connection is good - return to pool
                    _connection_pool.putconn(conn)
            except Exception as e:
                # If putconn fails, just close the connection
                print(f"⚠️ Error returning connection to pool: {e}")
                try:
                    conn.close()
                except:
                    pass
    else:
        # Close SQLite connection
        try:
            conn.close()
        except:
            pass


@contextmanager
def get_db_context():
    """
    Context manager for safe database connection handling.
    Automatically returns connection to pool or closes it.

    Usage:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            conn.commit()
        # Connection automatically returned to pool

    This is the RECOMMENDED way to get database connections.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()  # Auto-commit on success
    except Exception as e:
        conn.rollback()  # Auto-rollback on error
        raise e
    finally:
        release_db_connection(conn)


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
