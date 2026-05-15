import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '.env'
))

import psycopg2
import psycopg2.extras
from core.skill_extractor import process_job, process_course

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_job_extraction(limit: int = 72):
    print(f"\n--- Extracting Skills from Jobs ---")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT j.id, j.title, j.description
        FROM jobs j
        WHERE NOT EXISTS (
            SELECT 1 FROM job_skills js WHERE js.job_id = j.id
        )
        LIMIT %s
    """, (limit,))
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Found {len(jobs)} unprocessed jobs")

    for i, job in enumerate(jobs):
        print(f"  [{i+1}/{len(jobs)}] {job['title'][:50]}")
        saved = process_job(job['id'], job['title'], job['description'])
        print(f"    → {saved} skills saved")

def run_course_extraction(limit: int = 53):
    print(f"\n--- Extracting Skills from Courses ---")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT c.id, c.course_code, c.title,
               c.description, c.learning_outcomes
        FROM courses c
        WHERE NOT EXISTS (
            SELECT 1 FROM course_skills cs WHERE cs.course_id = c.id
        )
        LIMIT %s
    """, (limit,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Found {len(courses)} unprocessed courses")

    for i, course in enumerate(courses):
        print(f"  [{i+1}/{len(courses)}] {course['course_code']}: {course['title'][:40]}")
        saved = process_course(
            course['id'],
            course['course_code'],
            course['title'],
            course['description'] or '',
            course['learning_outcomes'] or ''
        )
        print(f"    → {saved} skills saved")

def verify():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT COUNT(*) as c FROM skills")
    skills = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM skills WHERE embedding IS NOT NULL")
    with_emb = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM job_skills")
    job_skills = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) as c FROM course_skills")
    course_skills = cursor.fetchone()['c']

    cursor.close()
    conn.close()

    print(f"\n--- Final Verification ---")
    print(f"✅ Skills: {skills}")
    print(f"✅ Skills with embeddings: {with_emb}")
    print(f"✅ Job skill links: {job_skills}")
    print(f"✅ Course skill links: {course_skills}")

if __name__ == "__main__":
    print("=== Masar Skill Extraction Pipeline ===")
    print("Using Claude AI — takes 10-15 minutes\n")
    run_job_extraction(limit=72)
    run_course_extraction(limit=53)
    verify()
    print("\n✅ Done! Gap analyzer can now produce real scores!")