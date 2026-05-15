import psycopg2
import psycopg2.extras
import json

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

SKILLS = [
    {"name": "Python", "category": "technical"},
    {"name": "SQL", "category": "technical"},
    {"name": "Java", "category": "technical"},
    {"name": "JavaScript", "category": "technical"},
    {"name": "React.js", "category": "technical"},
    {"name": "Node.js", "category": "technical"},
    {"name": "Machine Learning", "category": "technical"},
    {"name": "Deep Learning", "category": "technical"},
    {"name": "Data Analysis", "category": "technical"},
    {"name": "Data Science", "category": "technical"},
    {"name": "Docker", "category": "technical"},
    {"name": "AWS", "category": "technical"},
    {"name": "Linux", "category": "technical"},
    {"name": "Git", "category": "technical"},
    {"name": "REST APIs", "category": "technical"},
    {"name": "PostgreSQL", "category": "technical"},
    {"name": "MongoDB", "category": "technical"},
    {"name": "Power BI", "category": "technical"},
    {"name": "Tableau", "category": "technical"},
    {"name": "TensorFlow", "category": "technical"},
    {"name": "PyTorch", "category": "technical"},
    {"name": "Scikit-learn", "category": "technical"},
    {"name": "NLP", "category": "technical"},
    {"name": "Computer Vision", "category": "technical"},
    {"name": "Cybersecurity", "category": "technical"},
    {"name": "Network Security", "category": "technical"},
    {"name": "Cloud Computing", "category": "technical"},
    {"name": "Kubernetes", "category": "technical"},
    {"name": "FastAPI", "category": "technical"},
    {"name": "Django", "category": "technical"},
    {"name": "TypeScript", "category": "technical"},
    {"name": "HTML", "category": "technical"},
    {"name": "CSS", "category": "technical"},
    {"name": "ETL", "category": "technical"},
    {"name": "Data Engineering", "category": "technical"},
    {"name": "Excel", "category": "technical"},
    {"name": "C++", "category": "technical"},
    {"name": "Algorithms", "category": "technical"},
    {"name": "Data Structures", "category": "technical"},
    {"name": "Object-Oriented Programming", "category": "technical"},
    {"name": "Linear Algebra", "category": "technical"},
    {"name": "Statistics", "category": "technical"},
    {"name": "Probability", "category": "technical"},
    {"name": "Database Design", "category": "technical"},
    {"name": "Software Engineering", "category": "technical"},
    {"name": "Agile", "category": "technical"},
    {"name": "Mobile Development", "category": "technical"},
    {"name": "React Native", "category": "technical"},
    {"name": "Artificial Intelligence", "category": "technical"},
    {"name": "Computer Networks", "category": "technical"},
    {"name": "Communication", "category": "soft"},
    {"name": "Teamwork", "category": "soft"},
    {"name": "Problem Solving", "category": "soft"},
    {"name": "Critical Thinking", "category": "soft"},
    {"name": "Project Management", "category": "soft"},
    {"name": "Leadership", "category": "soft"},
    {"name": "Time Management", "category": "soft"},
    {"name": "Presentation Skills", "category": "soft"},
]

JOB_SKILLS_MAP = {
    "Data Analyst": ["Python", "SQL", "Data Analysis", "Power BI",
                     "Excel", "Statistics", "Tableau", "Communication"],
    "Backend Developer": ["Python", "REST APIs", "PostgreSQL",
                          "Docker", "Git", "Linux", "FastAPI", "Django"],
    "Frontend Developer": ["JavaScript", "React.js", "HTML",
                           "CSS", "TypeScript", "Git", "Communication"],
    "Machine Learning Engineer": ["Python", "Machine Learning", "Deep Learning",
                                   "TensorFlow", "PyTorch", "Scikit-learn",
                                   "Linear Algebra", "Statistics"],
    "Cybersecurity Analyst": ["Cybersecurity", "Network Security",
                               "Linux", "Python", "Communication",
                               "Problem Solving"],
    "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Linux",
                        "Git", "Cloud Computing", "Python"],
    "Full Stack Developer": ["JavaScript", "React.js", "Node.js",
                              "Python", "PostgreSQL", "Docker",
                              "REST APIs", "Git"],
    "Data Engineer": ["Python", "SQL", "ETL", "Data Engineering",
                      "AWS", "PostgreSQL", "Statistics"],
    "AI Engineer": ["Python", "Artificial Intelligence", "Machine Learning",
                    "NLP", "Deep Learning", "FastAPI", "Docker"],
    "Data Scientist": ["Python", "Machine Learning", "Statistics",
                       "Data Analysis", "SQL", "Scikit-learn",
                       "Communication", "Presentation Skills"],
    "Mobile Developer": ["Mobile Development", "React Native",
                         "JavaScript", "Git", "REST APIs"],
    "Network Engineer": ["Computer Networks", "Linux",
                         "Network Security", "Problem Solving",
                         "Communication"],
    "Database Administrator": ["SQL", "PostgreSQL", "Database Design",
                                "Linux", "Problem Solving"],
    "Software Engineer": ["Python", "Algorithms", "Data Structures",
                          "Object-Oriented Programming", "Git",
                          "Software Engineering"],
    "Cloud Solutions Architect": ["AWS", "Cloud Computing", "Docker",
                                   "Kubernetes", "Communication", "Leadership"],
}

COURSE_SKILLS_MAP = {
    "CS10001": ["Communication", "Critical Thinking", "Problem Solving"],
    "CS1002": ["Python", "Algorithms", "Data Structures",
               "HTML", "SQL", "Problem Solving"],
    "CS1003": ["Algorithms", "Critical Thinking",
               "Problem Solving", "Linear Algebra"],
    "CS1251": ["Object-Oriented Programming", "Java",
               "Software Engineering", "Problem Solving"],
    "CS10403": ["Probability", "Statistics", "Linear Algebra"],
    "CS1253": ["Linear Algebra", "Algorithms", "Problem Solving"],
    "CS1007": ["SQL", "Database Design", "PostgreSQL", "Data Analysis"],
    "CS1006": ["Computer Networks", "Network Security", "Communication"],
    "CS1008": ["HTML", "CSS", "JavaScript", "React.js"],
    "CS1255": ["Algorithms", "Data Structures", "C++"],
    "CS1256": ["Data Structures", "Algorithms",
               "Python", "Object-Oriented Programming"],
    "CS1009": ["Software Engineering", "Agile",
               "Git", "Communication", "Teamwork"],
    "CS1502": ["Linux", "Computer Networks", "Problem Solving"],
    "CS1503": ["Software Engineering", "Agile",
               "Project Management", "Teamwork"],
    "CS1505": ["Artificial Intelligence", "Python",
               "Problem Solving", "Algorithms"],
    "CS1506": ["Algorithms", "Data Structures",
               "Problem Solving", "Critical Thinking"],
    "CS1759": ["Machine Learning", "Python", "Statistics",
               "Scikit-learn", "Data Analysis"],
    "CS1510": ["Mobile Development", "React Native", "JavaScript"],
    "CS1763": ["NLP", "Python", "Machine Learning", "Deep Learning"],
    "CS1769": ["Data Science", "Python", "Machine Learning",
               "Statistics", "Data Analysis"],
}

def seed_skills():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("--- Seeding Skills ---")
    skill_id_map = {}

    for skill in SKILLS:
        cursor.execute("""
            INSERT INTO skills (name, category)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE
            SET category = EXCLUDED.category
            RETURNING id
        """, (skill['name'], skill['category']))
        skill_id = cursor.fetchone()['id']
        skill_id_map[skill['name']] = skill_id

    conn.commit()
    print(f"✅ {len(SKILLS)} skills seeded")
    cursor.close()
    conn.close()
    return skill_id_map

def seed_job_skills(skill_id_map):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n--- Linking Skills to Jobs ---")
    linked = 0

    cursor.execute("SELECT id, title FROM jobs")
    jobs = cursor.fetchall()

    for job in jobs:
        job_title = job['title']
        job_id = job['id']

        matched_skills = None
        for title_key, skills in JOB_SKILLS_MAP.items():
            if (title_key.lower() in job_title.lower() or
                    job_title.lower() in title_key.lower()):
                matched_skills = skills
                break

        if not matched_skills:
            matched_skills = ["Problem Solving", "Communication",
                              "Python", "SQL"]

        for skill_name in matched_skills:
            skill_id = skill_id_map.get(skill_name)
            if skill_id:
                cursor.execute("""
                    INSERT INTO job_skills
                    (job_id, skill_id, weight, is_required)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (job_id, skill_id, 1.0, True))
                linked += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {linked} job-skill links created")

def seed_course_skills(skill_id_map):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("\n--- Linking Skills to Courses ---")
    linked = 0

    for course_code, skills in COURSE_SKILLS_MAP.items():
        cursor.execute(
            "SELECT id FROM courses WHERE course_code = %s",
            (course_code,)
        )
        course = cursor.fetchone()

        if not course:
            continue

        for skill_name in skills:
            skill_id = skill_id_map.get(skill_name)
            if skill_id:
                cursor.execute("""
                    INSERT INTO course_skills
                    (course_id, skill_id, confidence, extraction_method)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (course['id'], skill_id, 0.9, 'manual'))
                linked += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {linked} course-skill links created")

def verify():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT COUNT(*) as c FROM skills")
    skills = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM job_skills")
    job_skills = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM course_skills")
    course_skills = cursor.fetchone()['c']

    cursor.close()
    conn.close()

    print(f"\n--- Verification ---")
    print(f"✅ Skills: {skills}")
    print(f"✅ Job Skills: {job_skills}")
    print(f"✅ Course Skills: {course_skills}")

if __name__ == "__main__":
    print("=== Seeding Skills Manually ===\n")
    skill_id_map = seed_skills()
    seed_job_skills(skill_id_map)
    seed_course_skills(skill_id_map)
    verify()
    print("\n✅ Skills seeded! Gap analyzer can now produce real scores!")