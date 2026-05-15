from fastapi import APIRouter
import psycopg2
import psycopg2.extras

router = APIRouter(prefix="/api/courses", tags=["courses"])

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@router.get("/")
def list_courses():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT c.id, c.course_code, c.title, c.department,
               COUNT(cs.skill_id) as skill_count
        FROM courses c
        LEFT JOIN course_skills cs ON c.id = cs.course_id
        GROUP BY c.id, c.course_code, c.title, c.department
        ORDER BY c.course_code
    """)
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"courses": [dict(c) for c in courses], "total": len(courses)}
