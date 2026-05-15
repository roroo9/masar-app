import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "masar"),
    "user": os.environ.get("DB_USER", "masar_user"),
    "password": os.environ.get("DB_PASSWORD", "masar_pass")
}

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