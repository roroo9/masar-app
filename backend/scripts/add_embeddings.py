import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.env'
))

import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer

print("Loading SBERT model...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Model loaded!")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def add_embeddings():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get all skills without embeddings
    cursor.execute("""
        SELECT id, name FROM skills
        WHERE embedding IS NULL
    """)
    skills = cursor.fetchall()
    print(f"\nFound {len(skills)} skills without embeddings")

    updated = 0
    for skill in skills:
        embedding = model.encode(skill['name']).tolist()
        embedding_str = str(embedding)

        cursor.execute("""
            UPDATE skills
            SET embedding = %s::vector
            WHERE id = %s
        """, (embedding_str, skill['id']))

        updated += 1
        print(f"  ✓ {skill['name']}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n✅ Added embeddings to {updated} skills!")

def verify():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT COUNT(*) as c FROM skills WHERE embedding IS NOT NULL")
    with_emb = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM skills")
    total = cursor.fetchone()['c']

    cursor.close()
    conn.close()

    print(f"\n--- Verification ---")
    print(f"✅ Skills with embeddings: {with_emb}/{total}")

if __name__ == "__main__":
    print("=== Adding Embeddings to Skills ===")
    add_embeddings()
    verify()