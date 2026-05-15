from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Annotated, List, Optional
import psycopg2
import psycopg2.extras
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.gap_analyzer import analyze_gap, get_all_jobs
from core.readiness_scorer import compute_and_save
from db.database import get_connection
from api.deps import require_same_student

router = APIRouter(prefix="/api/students", tags=["students"])

# Shorthand: path param that also verifies the caller owns this student_id
OwnStudent = Annotated[int, Depends(require_same_student)]


class StudentCreate(BaseModel):
    name: str
    email: str
    major: str
    year_of_study: int
    university: str = "King Khalid University"

class CourseAdd(BaseModel):
    course_codes: List[str]

class SkillAdd(BaseModel):
    skill_name: str
    proficiency: int
    source: str

class BulkSkillAdd(BaseModel):
    skill_ids: List[int]
    proficiency: int = 4
    source: str = "self_reported"


# ── Unprotected: registration still goes through /api/auth/register.
# This endpoint is kept for backward compat only.
@router.post("/")
def create_student(student: StudentCreate):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id FROM students WHERE email = %s", (student.email,))
    existing = cursor.fetchone()
    if existing:
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    cursor.execute("""
        INSERT INTO students (name, email, major, year_of_study, university)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (student.name, student.email, student.major, student.year_of_study, student.university))

    student_id = cursor.fetchone()["id"]
    conn.commit()
    cursor.close(); conn.close()
    return {"id": student_id, "message": "Student created successfully"}


@router.get("/{student_id}")
def get_student(student_id: OwnStudent):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close(); conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    row = dict(student)
    row.pop("password_hash", None)
    return row


@router.post("/{student_id}/courses")
def add_student_courses(student_id: OwnStudent, data: CourseAdd):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    added = []
    not_found = []

    if data.course_codes:
        cursor.execute(
            "SELECT id, course_code FROM courses WHERE course_code = ANY(%s)",
            (data.course_codes,)
        )
        found = {row["course_code"]: row["id"] for row in cursor.fetchall()}

        for code in data.course_codes:
            if code in found:
                cursor.execute("""
                    INSERT INTO student_courses (student_id, course_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                """, (student_id, found[code]))
                added.append(code)
            else:
                not_found.append(code)

    if added:
        cursor.execute("DELETE FROM readiness_scores WHERE student_id = %s", (student_id,))

    conn.commit(); cursor.close(); conn.close()
    return {"added_courses": added, "not_found": not_found, "count": len(added)}


@router.get("/{student_id}/skills")
def get_student_skills_route(student_id: OwnStudent):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT DISTINCT s.id, s.name, s.category,
               MAX(cs.confidence) as confidence, 'course' as source
        FROM student_courses sc
        JOIN course_skills cs ON sc.course_id = cs.course_id
        JOIN skills s ON cs.skill_id = s.id
        WHERE sc.student_id = %s
        GROUP BY s.id, s.name, s.category
    """, (student_id,))
    course_skills = cursor.fetchall()

    cursor.execute("""
        SELECT s.id, s.name, s.category,
               (ses.proficiency / 5.0) as confidence, ses.source
        FROM student_extra_skills ses
        JOIN skills s ON ses.skill_id = s.id
        WHERE ses.student_id = %s
    """, (student_id,))
    extra_skills = cursor.fetchall()
    cursor.close(); conn.close()

    all_skills: dict = {}
    for s in course_skills:
        all_skills[s["id"]] = dict(s)
    for s in extra_skills:
        sid = s["id"]
        if sid not in all_skills or s["confidence"] > all_skills[sid]["confidence"]:
            all_skills[sid] = dict(s)

    skills = list(all_skills.values())
    technical = [s for s in skills if s.get("category") == "technical"]
    soft      = [s for s in skills if s.get("category") == "soft"]
    domain    = [s for s in skills if s.get("category") == "domain"]

    def fmt(s):
        return {"id": s["id"], "name": s["name"],
                "confidence": float(s["confidence"] or 0),
                "source": s.get("source") or "course"}

    return {"total_skills": len(skills),
            "technical": [fmt(s) for s in technical],
            "soft": [fmt(s) for s in soft],
            "domain": [fmt(s) for s in domain]}


@router.get("/{student_id}/readiness/{job_id}")
async def get_readiness_score(
    student_id: OwnStudent,
    job_id: int,
    force: bool = False,
    explanation: bool = False,
):
    import asyncio
    result = await asyncio.to_thread(
        compute_and_save, student_id, job_id, force=force, with_explanation=explanation
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{student_id}/dashboard")
def get_dashboard(student_id: OwnStudent):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    if not student:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    cursor.execute("""
        SELECT rs.job_id, rs.score, j.title, j.company
        FROM readiness_scores rs
        JOIN jobs j ON rs.job_id = j.id
        WHERE rs.student_id = %s
        ORDER BY rs.score DESC
    """, (student_id,))
    scores = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT DISTINCT cs.skill_id
            FROM student_courses sc
            JOIN course_skills cs ON sc.course_id = cs.course_id
            WHERE sc.student_id = %s
            UNION
            SELECT skill_id FROM student_extra_skills WHERE student_id = %s
        ) combined
    """, (student_id, student_id))
    skill_count = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT id, title, company, location
        FROM jobs WHERE is_active = TRUE
        ORDER BY id LIMIT 20
    """)
    all_jobs = cursor.fetchall()
    cursor.close(); conn.close()

    scores_dict = {s["job_id"]: s["score"] for s in scores}
    jobs_with_scores = [
        {"job_id": j["id"], "title": j["title"], "company": j["company"],
         "location": j["location"], "readiness_score": scores_dict.get(j["id"])}
        for j in all_jobs
    ]
    jobs_with_scores.sort(
        key=lambda x: (x["readiness_score"] is None, -(x["readiness_score"] or 0))
    )

    student_row = dict(student)
    student_row.pop("password_hash", None)
    return {"student": student_row, "total_skills": skill_count,
            "top_scores": [dict(s) for s in scores[:3]], "jobs": jobs_with_scores}


@router.post("/{student_id}/extra-skills")
def add_extra_skills(student_id: OwnStudent, data: BulkSkillAdd):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    added = []
    if data.skill_ids:
        cursor.execute("SELECT id FROM skills WHERE id = ANY(%s)", (data.skill_ids,))
        valid_ids = {row["id"] for row in cursor.fetchall()}
        added = [sid for sid in data.skill_ids if sid in valid_ids]
        if added:
            psycopg2.extras.execute_values(cursor, """
                INSERT INTO student_extra_skills (student_id, skill_id, proficiency, source)
                VALUES %s
                ON CONFLICT (student_id, skill_id) DO UPDATE
                SET proficiency = EXCLUDED.proficiency, source = EXCLUDED.source
            """, [(student_id, sid, data.proficiency, data.source) for sid in added])

    if added:
        cursor.execute("DELETE FROM readiness_scores WHERE student_id = %s", (student_id,))

    conn.commit(); cursor.close(); conn.close()
    return {"added": len(added), "skill_ids": added}


@router.get("/{student_id}/projects")
def get_student_projects(student_id: OwnStudent, job_id: Optional[int] = None, limit: int = 5):
    from core.recommender import recommend_projects
    return {"projects": recommend_projects(student_id, job_id, limit)}


class ConfirmSkill(BaseModel):
    skill_name: str


@router.post("/{student_id}/confirm-skill")
def confirm_skill(student_id: OwnStudent, data: ConfirmSkill):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id FROM skills WHERE LOWER(name) = LOWER(%s)", (data.skill_name,))
    row = cursor.fetchone()
    if not row:
        cursor.close(); conn.close()
        raise HTTPException(status_code=404, detail="Skill not found")

    skill_id = row["id"]
    cursor.execute("""
        INSERT INTO student_extra_skills (student_id, skill_id, proficiency, source)
        VALUES (%s, %s, 5, 'self_reported')
        ON CONFLICT (student_id, skill_id) DO UPDATE
        SET proficiency = 5, source = 'self_reported'
    """, (student_id, skill_id))
    cursor.execute("DELETE FROM readiness_scores WHERE student_id = %s", (student_id,))
    conn.commit(); cursor.close(); conn.close()
    return {"success": True, "skill_id": skill_id}


class CourseDescriptionExtract(BaseModel):
    course_name: str = ""
    description: str


@router.post("/{student_id}/extract-from-description")
def extract_from_description(student_id: OwnStudent, data: CourseDescriptionExtract):
    from core.skill_extractor import extract_skills_from_text, get_or_create_skill

    text = data.description.strip()
    if data.course_name.strip():
        text = f"Course: {data.course_name.strip()}\n{text}"

    extracted = extract_skills_from_text(text)
    if not extracted:
        return {"skills": [], "added_count": 0}

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    added_skills = []
    for skill in extracted:
        if skill.get("confidence", 0) < 0.5:
            continue
        skill_id = get_or_create_skill(skill["name"], skill["type"], conn)
        if skill_id is None:
            continue
        cursor.execute("""
            INSERT INTO student_extra_skills (student_id, skill_id, proficiency, source)
            VALUES (%s, %s, 4, 'course_description')
            ON CONFLICT (student_id, skill_id) DO NOTHING
        """, (student_id, skill_id))
        cursor.execute("SELECT id, name, category FROM skills WHERE id = %s", (skill_id,))
        row = cursor.fetchone()
        if row:
            added_skills.append(dict(row))

    if added_skills:
        cursor.execute("DELETE FROM readiness_scores WHERE student_id = %s", (student_id,))
    conn.commit(); cursor.close(); conn.close()
    return {"skills": added_skills, "added_count": len(added_skills)}


@router.post("/{student_id}/extract-from-pdf")
async def extract_from_pdf(student_id: OwnStudent, file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    import pdfplumber, io
    from core.skill_extractor import extract_skills_from_text, get_or_create_skill

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages[:20]:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise HTTPException(status_code=422, detail="No readable text found in PDF")

    extracted = extract_skills_from_text(full_text)
    if not extracted:
        return {"skills": [], "added_count": 0, "page_count": len(text_parts)}

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    added_skills = []
    for skill in extracted:
        if skill.get("confidence", 0) < 0.5:
            continue
        skill_id = get_or_create_skill(skill["name"], skill["type"], conn)
        if skill_id is None:
            continue
        cursor.execute("""
            INSERT INTO student_extra_skills (student_id, skill_id, proficiency, source)
            VALUES (%s, %s, 4, 'course_description')
            ON CONFLICT (student_id, skill_id) DO NOTHING
        """, (student_id, skill_id))
        cursor.execute("SELECT id, name, category FROM skills WHERE id = %s", (skill_id,))
        row = cursor.fetchone()
        if row:
            added_skills.append(dict(row))

    if added_skills:
        cursor.execute("DELETE FROM readiness_scores WHERE student_id = %s", (student_id,))
    conn.commit(); cursor.close(); conn.close()
    return {"skills": added_skills, "added_count": len(added_skills), "page_count": len(text_parts)}
