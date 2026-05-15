import psycopg2
import psycopg2.extras
import numpy as np
from typing import List, Dict

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors."""
    if isinstance(vec1, str):
        import ast
        vec1 = ast.literal_eval(vec1)
    if isinstance(vec2, str):
        import ast
        vec2 = ast.literal_eval(vec2)

    vec1 = np.array(vec1, dtype=float)
    vec2 = np.array(vec2, dtype=float)

    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def _parse_embedding(emb) -> np.ndarray:
    if isinstance(emb, str):
        import ast
        return np.array(ast.literal_eval(emb), dtype=float)
    return np.array(emb, dtype=float)

def get_student_skills(student_id: int) -> List[Dict]:
    """Get all skills a student has from completed courses and extra skills."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Skills from completed courses
    cursor.execute("""
        SELECT DISTINCT 
            s.id,
            s.name,
            s.category,
            s.embedding,
            MAX(cs.confidence) as confidence,
            'course' as source
        FROM student_courses sc
        JOIN course_skills cs ON sc.course_id = cs.course_id
        JOIN skills s ON cs.skill_id = s.id
        WHERE sc.student_id = %s
        AND s.embedding IS NOT NULL
        GROUP BY s.id, s.name, s.category, s.embedding
    """, (student_id,))
    course_skills = cursor.fetchall()
    
    # Skills from extra experience
    cursor.execute("""
        SELECT 
            s.id,
            s.name,
            s.category,
            s.embedding,
            (ses.proficiency::float / 5.0) as confidence,
            ses.source
        FROM student_extra_skills ses
        JOIN skills s ON ses.skill_id = s.id
        WHERE ses.student_id = %s
        AND s.embedding IS NOT NULL
    """, (student_id,))
    extra_skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Combine and deduplicate
    all_skills = {}
    for skill in list(course_skills) + list(extra_skills):
        sid = skill['id']
        if sid not in all_skills or skill['confidence'] > all_skills[sid]['confidence']:
            all_skills[sid] = dict(skill)
    
    return list(all_skills.values())

def get_job_skills(job_id: int) -> List[Dict]:
    """Get all skills required for a specific job."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT 
            s.id,
            s.name,
            s.category,
            s.embedding,
            js.weight,
            js.is_required
        FROM job_skills js
        JOIN skills s ON js.skill_id = s.id
        WHERE js.job_id = %s
        AND s.embedding IS NOT NULL
        ORDER BY js.weight DESC
    """, (job_id,))
    
    skills = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(s) for s in skills]

def get_tfidf_weights() -> Dict[int, float]:
    """Calculate TF-IDF weights for all skills based on job frequency."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("SELECT COUNT(*) as total FROM jobs")
    total_jobs = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT skill_id, COUNT(DISTINCT job_id) as job_count
        FROM job_skills
        GROUP BY skill_id
    """)
    skill_counts = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    weights = {}
    for row in skill_counts:
        idf = np.log(total_jobs / (row['job_count'] + 1)) + 1
        weights[row['skill_id']] = float(idf)
    
    return weights

def analyze_gap(student_id: int, job_id: int) -> Dict:
    """
    Core function: compare student skills vs job requirements.
    Returns detailed gap analysis.
    """
    from concurrent.futures import ThreadPoolExecutor

    print(f"Analyzing gap for student {student_id} vs job {job_id}...")

    # Fetch student skills, job skills, and TF-IDF weights in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_student = pool.submit(get_student_skills, student_id)
        f_job = pool.submit(get_job_skills, job_id)
        f_tfidf = pool.submit(get_tfidf_weights)
        student_skills = f_student.result()
        job_skills = f_job.result()
        tfidf_weights = f_tfidf.result()

    if not job_skills:
        return {
            "readiness_score": 0,
            "total_job_skills": 0,
            "matched_count": 0,
            "partial_count": 0,
            "missing_count": 0,
            "matched_skills": [],
            "partial_skills": [],
            "missing_skills": [],
            "score_breakdown": {
                "achieved_weight": 0,
                "total_weight": 0,
                "percentage": 0
            },
            "note": "No skills extracted for this job yet"
        }

    if not student_skills:
        return {
            "error": "No skills found for this student",
            "readiness_score": 0,
            "missing_skills": [{"skill": s['name'], "weight": s['weight']} for s in job_skills]
        }

    # Pre-parse and normalise all student embeddings once (avoids repeated ast.literal_eval)
    valid_student = [
        (s, _parse_embedding(s['embedding']))
        for s in student_skills if s['embedding']
    ]

    if not valid_student:
        return {
            "error": "No skills found for this student",
            "readiness_score": 0,
            "missing_skills": [{"skill": s['name'], "weight": s['weight']} for s in job_skills]
        }

    s_metas, s_vecs = zip(*valid_student)
    S = np.array(s_vecs, dtype=float)                      # (n_student, dim)
    s_norms = np.linalg.norm(S, axis=1, keepdims=True)
    s_norms[s_norms == 0] = 1.0
    S_norm = S / s_norms                                    # row-normalised matrix

    matched = []
    missing = []
    partial = []
    total_weight = 0
    achieved_weight = 0

    for job_skill in job_skills:
        if not job_skill['embedding']:
            continue

        j_emb = _parse_embedding(job_skill['embedding'])
        j_norm = np.linalg.norm(j_emb)
        if j_norm == 0:
            continue
        j_unit = j_emb / j_norm

        skill_weight = tfidf_weights.get(job_skill['id'], 1.0)
        if job_skill['is_required']:
            skill_weight *= 1.5
        total_weight += skill_weight

        # One matrix-vector multiply replaces the inner Python loop
        sims = S_norm @ j_unit                              # (n_student,)
        best_idx = int(np.argmax(sims))
        best_similarity = float(sims[best_idx])
        best_match = s_metas[best_idx]

        if best_similarity >= 0.87:
            contribution = skill_weight * min(best_match['confidence'], 1.0)
            achieved_weight += contribution
            matched.append({
                "skill": job_skill['name'],
                "matched_with": best_match['name'],
                "similarity": round(best_similarity, 3),
                "source": best_match.get('source', 'course'),
                "weight": round(skill_weight, 3)
            })
        elif best_similarity >= 0.65:
            contribution = skill_weight * best_similarity * 0.4
            achieved_weight += contribution
            partial.append({
                "skill": job_skill['name'],
                "closest_match": best_match['name'] if best_match else None,
                "similarity": round(best_similarity, 3),
                "weight": round(skill_weight, 3),
                "gap_description": f"You have related knowledge in '{best_match['name']}' but need to develop '{job_skill['name']}' specifically"
            })
        else:
            missing.append({
                "skill": job_skill['name'],
                "category": job_skill['category'],
                "weight": round(skill_weight, 3),
                "is_required": job_skill['is_required'],
                "priority": "high" if job_skill['is_required'] else "medium"
            })

    if total_weight > 0:
        raw_score = (achieved_weight / total_weight) * 100
    else:
        raw_score = 0

    readiness_score = min(round(raw_score, 1), 75.0)

    return {
        "student_id": student_id,
        "job_id": job_id,
        "readiness_score": readiness_score,
        "total_job_skills": len(job_skills),
        "matched_count": len(matched),
        "partial_count": len(partial),
        "missing_count": len(missing),
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": sorted(missing, key=lambda x: x['weight'], reverse=True),
        "score_breakdown": {
            "achieved_weight": round(achieved_weight, 3),
            "total_weight": round(total_weight, 3),
            "percentage": readiness_score
        }
    }

def get_all_jobs() -> List[Dict]:
    """Get all active jobs."""
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
    
    return [dict(j) for j in jobs]

def get_student_dashboard_scores(student_id: int) -> List[Dict]:
    """Get cached readiness scores for all jobs for a student."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute("""
        SELECT 
            rs.job_id,
            rs.score,
            j.title,
            j.company
        FROM readiness_scores rs
        JOIN jobs j ON rs.job_id = j.id
        WHERE rs.student_id = %s
        ORDER BY rs.score DESC
    """, (student_id,))
    
    scores = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [dict(s) for s in scores]