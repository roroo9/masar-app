from fastapi import APIRouter
import psycopg2.extras
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db.database import get_connection, pooled_connection

router = APIRouter(prefix="/api/courses", tags=["courses"])

@router.get("/")
def list_courses():
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT c.id, c.course_code, c.title, c.department,
                       COUNT(cs.skill_id) as skill_count
                FROM courses c
                LEFT JOIN course_skills cs ON c.id = cs.course_id
                GROUP BY c.id, c.course_code, c.title, c.department
                ORDER BY c.course_code
            """)
            courses = cursor.fetchall()
        finally:
            cursor.close()
    return {"courses": [dict(c) for c in courses], "total": len(courses)}
