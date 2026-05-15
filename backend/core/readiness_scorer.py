import json
import anthropic
import os
import psycopg2
import psycopg2.extras
from core.gap_analyzer import analyze_gap

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

EXPLANATION_PROMPT = """You are a career advisor for a university student in Saudi Arabia.

Based on this skill gap analysis, write a clear, motivating, and actionable explanation.

Student readiness score: {score}%
Job title: {job_title}

Matched skills ({matched_count}): {matched_skills}
Partially matched skills ({partial_count}): {partial_skills}
Missing skills ({missing_count}): {missing_skills}

Return ONLY a valid JSON object with this exact structure:
{{
  "summary": "One encouraging sentence mentioning the score and job title",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "improvement_areas": [
    {{
      "skill": "skill name",
      "why_it_matters": "why this skill is important for this job",
      "how_to_learn": "specific free resource (Coursera, YouTube, freeCodeCamp, etc.)",
      "time_estimate": "e.g. 2-3 weeks"
    }}
  ],
  "next_steps": ["concrete action 1", "concrete action 2", "concrete action 3"],
  "motivational_close": "One final motivating sentence"
}}

Be specific. Mention real platforms. Keep tone warm and encouraging.
Limit improvement_areas to top 3 most important missing skills only.
"""

def generate_explanation(gap_data: dict, job_title: str) -> dict:
    """Use Claude to generate a human-readable explanation of the gap analysis."""
    try:
        client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        
        matched_names = [s['skill'] for s in gap_data.get('matched_skills', [])[:6]]
        partial_names = [s['skill'] for s in gap_data.get('partial_skills', [])[:4]]
        missing_names = [s['skill'] for s in gap_data.get('missing_skills', [])[:6]]
        
        prompt = EXPLANATION_PROMPT.format(
            score=gap_data['readiness_score'],
            job_title=job_title,
            matched_count=gap_data['matched_count'],
            matched_skills=", ".join(matched_names) if matched_names else "None yet",
            partial_count=gap_data['partial_count'],
            partial_skills=", ".join(partial_names) if partial_names else "None",
            missing_count=gap_data['missing_count'],
            missing_skills=", ".join(missing_names) if missing_names else "None"
        )
        
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            timeout=15.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        
        # Clean and parse JSON
        result_text = result_text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        return json.loads(result_text)
        
    except Exception as e:
        print(f"LLM explanation error: {e}")
        # Fallback explanation
        return {
            "summary": f"You are {gap_data['readiness_score']}% ready for {job_title}.",
            "strengths": [s['skill'] for s in gap_data.get('matched_skills', [])[:3]],
            "improvement_areas": [
                {
                    "skill": s['skill'],
                    "why_it_matters": "Required for this role",
                    "how_to_learn": "Search on Coursera or YouTube",
                    "time_estimate": "2-4 weeks"
                }
                for s in gap_data.get('missing_skills', [])[:3]
            ],
            "next_steps": [
                "Focus on the top missing skills",
                "Work on a real project to practice",
                "Update your profile with new skills"
            ],
            "motivational_close": "Keep going — you are closer than you think!"
        }

def compute_and_save(student_id: int, job_id: int, force: bool = False, with_explanation: bool = True) -> dict:
    """
    Gap analysis pipeline. with_explanation=False skips the Claude call (~200ms vs ~20s).
    Plan page passes with_explanation=True; all other pages use the default False.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if not force:
        # For plan page: only use cache when explanation is already stored
        # For all others: any cached row is fine
        extra = "AND rs.explanation IS NOT NULL AND rs.explanation::text != '{}'" if with_explanation else ""
        cursor.execute(f"""
            SELECT rs.*, j.title, j.company
            FROM readiness_scores rs
            JOIN jobs j ON rs.job_id = j.id
            WHERE rs.student_id = %s AND rs.job_id = %s
            AND rs.computed_at > NOW() - INTERVAL '24 hours'
            {extra}
        """, (student_id, job_id))

        cached = cursor.fetchone()
        if cached:
            cursor.close()
            conn.close()
            return {
                "score": cached['score'],
                "job_title": f"{cached['title']} at {cached['company']}",
                "matched_skills": cached['matched_skills'],
                "missing_skills": cached['missing_skills'],
                "partial_skills": cached['partial_skills'],
                "explanation": json.loads(cached['explanation']) if cached['explanation'] else {},
                "cached": True
            }
    
    # Get job title
    cursor.execute("SELECT title, company FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()
    if not job:
        cursor.close()
        conn.close()
        return {"error": "Job not found"}
    
    job_title = f"{job['title']} at {job['company']}"
    
    # Run gap analysis
    gap_data = analyze_gap(student_id, job_id)
    
    if "error" in gap_data:
        cursor.close()
        conn.close()
        return gap_data
    
    # Generate explanation only when requested (plan page)
    if with_explanation:
        print("Generating AI explanation...")
        explanation = generate_explanation(gap_data, job_title)
    else:
        explanation = None  # stored as NULL; plan page will trigger Claude on first visit

    # Save to database — never overwrite a real explanation with NULL
    try:
        cursor.execute("""
            INSERT INTO readiness_scores
            (student_id, job_id, score, matched_skills, missing_skills, partial_skills, explanation)
            VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
            ON CONFLICT (student_id, job_id) DO UPDATE SET
                score = EXCLUDED.score,
                matched_skills = EXCLUDED.matched_skills,
                missing_skills = EXCLUDED.missing_skills,
                partial_skills = EXCLUDED.partial_skills,
                explanation = COALESCE(EXCLUDED.explanation, readiness_scores.explanation),
                computed_at = NOW()
        """, (
            student_id,
            job_id,
            gap_data['readiness_score'],
            json.dumps(gap_data['matched_skills']),
            json.dumps(gap_data['missing_skills']),
            json.dumps(gap_data['partial_skills']),
            json.dumps(explanation) if explanation else None
        ))
        conn.commit()
        print(f"✅ Saved score: {gap_data['readiness_score']}%")
    except Exception as e:
        print(f"Error saving score: {e}")
    
    cursor.close()
    conn.close()
    
    return {
        "score": gap_data['readiness_score'],
        "job_title": job_title,
        "matched_skills": gap_data['matched_skills'],
        "missing_skills": gap_data['missing_skills'],
        "partial_skills": gap_data['partial_skills'],
        "breakdown": gap_data['score_breakdown'],
        "explanation": explanation or {},
        "cached": False
    }