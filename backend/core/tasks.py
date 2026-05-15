from core.celery_app import celery_app
from core.skill_extractor import process_job, process_course
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@celery_app.task(bind=True, max_retries=3)
def extract_job_skills_task(self, job_id: int):
    """Async task to extract skills from a job."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            "SELECT id, title, description FROM jobs WHERE id = %s",
            (job_id,)
        )
        job = cursor.fetchone()
        cursor.close()
        conn.close()

        if not job:
            return {"error": "Job not found"}

        saved = process_job(job['id'], job['title'], job['description'])
        return {"job_id": job_id, "skills_saved": saved}

    except Exception as e:
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def extract_course_skills_task(self, course_id: int):
    """Async task to extract skills from a course."""
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT id, course_code, title, description, learning_outcomes
            FROM courses WHERE id = %s
        """, (course_id,))
        course = cursor.fetchone()
        cursor.close()
        conn.close()

        if not course:
            return {"error": "Course not found"}

        saved = process_course(
            course['id'],
            course['course_code'],
            course['title'],
            course['description'] or '',
            course['learning_outcomes'] or ''
        )
        return {"course_id": course_id, "skills_saved": saved}

    except Exception as e:
        raise self.retry(exc=e, countdown=60)

@celery_app.task
def extract_all_jobs_task():
    """Extract skills from all unprocessed jobs."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id FROM jobs
        WHERE NOT EXISTS (
            SELECT 1 FROM job_skills WHERE job_id = jobs.id
        )
    """)
    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    for job in jobs:
        extract_job_skills_task.delay(job['id'])

    return {"queued": len(jobs)}

@celery_app.task
def extract_all_courses_task():
    """Extract skills from all unprocessed courses."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id FROM courses
        WHERE NOT EXISTS (
            SELECT 1 FROM course_skills WHERE course_id = courses.id
        )
    """)
    courses = cursor.fetchall()
    cursor.close()
    conn.close()

    for course in courses:
        extract_course_skills_task.delay(course['id'])

    return {"queued": len(courses)}