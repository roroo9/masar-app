import psycopg2
import psycopg2.extras
import psycopg2.pool
import os
import urllib.parse
from contextlib import contextmanager
from typing import Optional


def _build_db_config() -> dict:
    """Prefer DATABASE_URL (Railway/Render), fall back to individual env vars."""
    url = os.environ.get("DATABASE_URL")
    if url:
        parsed = urllib.parse.urlparse(url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/"),
            "user": parsed.username,
            "password": parsed.password,
        }
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "database": os.environ.get("DB_NAME", "masar"),
        "user": os.environ.get("DB_USER", "masar_user"),
        "password": os.environ.get("DB_PASSWORD", "masar_pass"),
    }


DB_CONFIG = _build_db_config()

_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=20, **DB_CONFIG)
    return _pool

@contextmanager
def pooled_connection():
    """Context manager that checks out a connection from the pool and returns it on exit."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        pool.putconn(conn)

def get_connection():
    """Get a database connection."""
    return psycopg2.connect(**DB_CONFIG)

def get_dict_connection():
    """Get a database connection that returns dicts."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

def test_connection():
    """Test database connection."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Database connected: {version[:50]}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
