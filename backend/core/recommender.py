import psycopg2.extras
import json
import sys
import os
from typing import List, Dict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection, pooled_connection

def get_student_missing_skills(student_id: int, job_id: int = None) -> List[str]:
    """Get list of skills the student is missing."""
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            if job_id:
                cursor.execute("""
                    SELECT missing_skills
                    FROM readiness_scores
                    WHERE student_id = %s AND job_id = %s
                """, (student_id, job_id))

                result = cursor.fetchone()
                if result and result['missing_skills']:
                    missing = result['missing_skills']
                    if isinstance(missing, str):
                        missing = json.loads(missing)
                    return [s['skill'] for s in missing]

            # Get most in-demand skills student doesn't have
            cursor.execute("""
                SELECT DISTINCT cs.skill_id
                FROM student_courses sc
                JOIN course_skills cs ON sc.course_id = cs.course_id
                WHERE sc.student_id = %s
            """, (student_id,))

            student_skill_ids = [row['skill_id'] for row in cursor.fetchall()]

            if student_skill_ids:
                cursor.execute("""
                    SELECT s.name
                    FROM skills s
                    JOIN job_skills js ON s.id = js.skill_id
                    WHERE s.id NOT IN %s
                    GROUP BY s.id, s.name
                    ORDER BY COUNT(DISTINCT js.job_id) DESC
                    LIMIT 10
                """, (tuple(student_skill_ids),))
            else:
                cursor.execute("""
                    SELECT s.name
                    FROM skills s
                    JOIN job_skills js ON s.id = js.skill_id
                    GROUP BY s.id, s.name
                    ORDER BY COUNT(DISTINCT js.job_id) DESC
                    LIMIT 10
                """)

            missing = [row['name'] for row in cursor.fetchall()]
        finally:
            cursor.close()
    return missing

def get_student_info(student_id: int) -> Dict:
    """Get student major and year."""
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT major, year_of_study
                FROM students WHERE id = %s
            """, (student_id,))
            student = cursor.fetchone()
        finally:
            cursor.close()
    return dict(student) if student else {}

def recommend_projects(student_id: int, job_id: int = None, limit: int = 5) -> List[Dict]:
    """Recommend projects based on student missing skills."""
    with pooled_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, title, company, description,
                       difficulty, required_skills, estimated_hours
                FROM projects WHERE is_active = TRUE
            """)
            all_projects = cursor.fetchall()
        finally:
            cursor.close()

    if not all_projects:
        return []

    missing_skills = get_student_missing_skills(student_id, job_id)
    student_info = get_student_info(student_id)
    year = student_info.get('year_of_study', 2)

    scored_projects = []

    for project in all_projects:
        required = project['required_skills']
        if isinstance(required, str):
            required = json.loads(required)
        if not required:
            required = []

        overlap = 0
        covered_skills = []

        normalized_missing = [m.lower() for m in missing_skills]
        for req in required:
            req_lower = req.lower()
            if any(m in req_lower or req_lower in m for m in normalized_missing):
                overlap += 1
                covered_skills.append(req)

        difficulty_score = 1.0
        difficulty = project['difficulty']

        if year <= 2 and difficulty == 'beginner':
            difficulty_score = 1.3
        elif year == 3 and difficulty == 'intermediate':
            difficulty_score = 1.3
        elif year >= 4 and difficulty == 'advanced':
            difficulty_score = 1.3
        elif difficulty == 'beginner' and year >= 4:
            difficulty_score = 0.7

        final_score = overlap * difficulty_score

        if overlap > 0:
            scored_projects.append({
                "id": project['id'],
                "title": project['title'],
                "company": project['company'],
                "description": project['description'],
                "difficulty": project['difficulty'],
                "required_skills": required,
                "estimated_hours": project['estimated_hours'],
                "relevance_score": round(final_score, 2),
                "skills_you_will_learn": covered_skills[:5]
            })

    scored_projects.sort(key=lambda x: x['relevance_score'], reverse=True)

    if not scored_projects:
        if year <= 2:
            diff = 'beginner'
        elif year == 3:
            diff = 'intermediate'
        else:
            diff = 'advanced'

        with pooled_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            try:
                cursor.execute("""
                    SELECT id, title, company, description,
                           difficulty, required_skills, estimated_hours
                    FROM projects
                    WHERE difficulty = %s AND is_active = TRUE
                    LIMIT %s
                """, (diff, limit))
                projects = cursor.fetchall()
            finally:
                cursor.close()
        return [{**dict(p), "skills_you_will_learn": [], "relevance_score": 0} for p in projects]

    return scored_projects[:limit]