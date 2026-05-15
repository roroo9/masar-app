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

def get_university_analytics():
    """
    Show university where their curriculum gaps are.
    This is the unique feature no competitor has.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Skills taught in courses
    cursor.execute("""
        SELECT 
            s.name,
            s.category,
            COUNT(DISTINCT cs.course_id) as course_count
        FROM skills s
        JOIN course_skills cs ON s.id = cs.skill_id
        GROUP BY s.id, s.name, s.category
        ORDER BY course_count DESC
    """)
    taught_skills = cursor.fetchall()
    taught_names = {s['name'].lower() for s in taught_skills}

    # Top demanded skills in market
    cursor.execute("""
        SELECT 
            s.name,
            s.category,
            COUNT(DISTINCT js.job_id) as job_demand,
            AVG(js.weight) as avg_weight
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        GROUP BY s.id, s.name, s.category
        ORDER BY job_demand DESC
        LIMIT 30
    """)
    market_skills = cursor.fetchall()
    market_names = {s['name'].lower() for s in market_skills}

    # Curriculum gaps — skills market wants but university doesn't teach
    gaps = [
        {
            "skill": s['name'],
            "category": s['category'],
            "job_demand": s['job_demand']
        }
        for s in market_skills
        if s['name'].lower() not in taught_names
    ]

    # Alignment score
    aligned = len(taught_names.intersection(market_names))
    total_market = len(market_names)
    alignment_score = round(aligned / max(total_market, 1) * 100, 1)

    cursor.close()
    conn.close()

    return {
        "total_skills_taught": len(taught_skills),
        "total_market_skills": len(market_skills),
        "alignment_score": alignment_score,
        "top_taught_skills": [dict(s) for s in taught_skills[:10]],
        "top_market_demands": [dict(s) for s in market_skills[:10]],
        "curriculum_gaps": gaps[:10]
    }

def print_analytics():
    print("=== University Analytics ===\n")
    data = get_university_analytics()

    print(f"Alignment Score: {data['alignment_score']}%")
    print(f"Skills Taught: {data['total_skills_taught']}")
    print(f"Market Skills: {data['total_market_skills']}")

    print("\nTop Market Demands:")
    for s in data['top_market_demands'][:5]:
        print(f"  - {s['name']} ({s['job_demand']} jobs)")

    print("\nCurriculum Gaps (market wants but not taught):")
    for s in data['curriculum_gaps'][:5]:
        print(f"  ✗ {s['skill']} ({s['job_demand']} jobs demand it)")

if __name__ == "__main__":
    print_analytics()