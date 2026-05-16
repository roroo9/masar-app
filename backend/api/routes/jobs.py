from fastapi import APIRouter, HTTPException
import psycopg2.extras
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db.database import get_connection, pooled_connection

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/")
def get_all_jobs():
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, title, company, location
                FROM jobs
                WHERE is_active = TRUE
                ORDER BY id
            """)
            jobs = cursor.fetchall()
        finally:
            cursor.close()

    return {"jobs": [dict(j) for j in jobs], "total": len(jobs)}

@router.get("/{job_id}")
def get_job(job_id: int):
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
        finally:
            cursor.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return dict(job)

@router.get("/{job_id}/skills")
def get_job_skills(job_id: int):
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT s.name, s.category, js.weight, js.is_required
                FROM job_skills js
                JOIN skills s ON js.skill_id = s.id
                WHERE js.job_id = %s
                ORDER BY js.weight DESC
            """, (job_id,))
            skills = cursor.fetchall()
        finally:
            cursor.close()

    return {
        "job_id": job_id,
        "skills": [dict(s) for s in skills],
        "total": len(skills)
    }