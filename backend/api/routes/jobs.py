from fastapi import APIRouter, HTTPException
import psycopg2
import psycopg2.extras

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

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
def get_all_jobs():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT id, title, company, location
        FROM jobs
        WHERE is_active = TRUE
        ORDER BY id
    """)

    jobs = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"jobs": [dict(j) for j in jobs], "total": len(jobs)}

@router.get("/{job_id}")
def get_job(job_id: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()

    cursor.close()
    conn.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return dict(job)

@router.get("/{job_id}/skills")
def get_job_skills(job_id: int):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT s.name, s.category, js.weight, js.is_required
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.id
        WHERE js.job_id = %s
        ORDER BY js.weight DESC
    """, (job_id,))

    skills = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "job_id": job_id,
        "skills": [dict(s) for s in skills],
        "total": len(skills)
    }