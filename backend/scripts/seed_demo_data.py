"""
Self-contained seed script — no JSON files required.
Seeds jobs, courses, skills, job_skills, course_skills, students, projects.
Run once, then run add_embeddings.py to generate SBERT vectors.
"""
import json
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "masar", "user": "masar_user", "password": "masar_pass"
}

def conn():
    return psycopg2.connect(**DB_CONFIG)

# ── JOBS ──────────────────────────────────────────────────────────────────────
JOBS = [
    {"title": "Data Analyst", "company": "STC",
     "description": "Analyze large datasets to extract business insights. Use Python, SQL, Power BI and Excel to build dashboards and reports. Communicate findings to stakeholders.", "location": "Riyadh"},
    {"title": "Software Engineer", "company": "Elm",
     "description": "Design and develop backend services using Python and FastAPI. Work with PostgreSQL, Redis, and Docker. Write clean code, conduct code reviews, collaborate with cross-functional teams.", "location": "Riyadh"},
    {"title": "Data Scientist", "company": "Saudi Aramco",
     "description": "Build machine learning models for predictive analytics. Use Python, Scikit-learn, TensorFlow and Pandas. Strong statistics background required. Present insights to senior management.", "location": "Dhahran"},
    {"title": "Web Developer", "company": "Noon",
     "description": "Develop responsive web applications with React and TypeScript. Collaborate with UX designers. Optimize for performance and SEO. Work with REST APIs and GraphQL.", "location": "Riyadh"},
    {"title": "Cloud Engineer", "company": "Accenture",
     "description": "Design and maintain AWS cloud infrastructure. Use Terraform for IaC, manage Kubernetes clusters, set up CI/CD pipelines with GitHub Actions. Monitor with CloudWatch.", "location": "Jeddah"},
    {"title": "Machine Learning Engineer", "company": "SDAIA",
     "description": "Productionize ML models using MLflow and Docker. Build data pipelines with Apache Spark. Work closely with data scientists to deploy scalable NLP and computer vision solutions.", "location": "Riyadh"},
    {"title": "Business Intelligence Developer", "company": "Al-Rajhi Bank",
     "description": "Develop BI solutions using Power BI and Tableau. Write complex SQL queries on data warehouses. Define KPIs and design reporting dashboards for executive leadership.", "location": "Riyadh"},
    {"title": "DevOps Engineer", "company": "Zain",
     "description": "Build and maintain CI/CD pipelines. Manage Linux servers, containerized apps with Docker and Kubernetes. Automate infrastructure with Ansible and Terraform. Ensure high availability.", "location": "Riyadh"},
    {"title": "Full Stack Developer", "company": "Foodics",
     "description": "Build features across the stack: React frontend, Node.js / Python backend, PostgreSQL database. Participate in agile sprints. Write unit and integration tests.", "location": "Riyadh"},
    {"title": "Product Manager", "company": "NEOM Tech",
     "description": "Define product roadmap and write detailed PRDs. Coordinate between engineering, design and business teams. Analyze user feedback and market data. Strong communication and leadership skills.", "location": "Riyadh"},
]

# ── SKILLS ───────────────────────────────────────────────────────────────────
SKILLS = [
    # technical
    ("Python", "technical"), ("SQL", "technical"), ("Machine Learning", "technical"),
    ("Data Analysis", "technical"), ("Power BI", "technical"), ("Tableau", "technical"),
    ("FastAPI", "technical"), ("PostgreSQL", "technical"), ("Docker", "technical"),
    ("React", "technical"), ("TypeScript", "technical"), ("REST APIs", "technical"),
    ("AWS", "technical"), ("Kubernetes", "technical"), ("Terraform", "technical"),
    ("TensorFlow", "technical"), ("Scikit-learn", "technical"), ("NLP", "technical"),
    ("Pandas", "technical"), ("Git", "technical"), ("Linux", "technical"),
    ("Node.js", "technical"), ("Statistics", "technical"), ("Deep Learning", "technical"),
    ("CI/CD", "technical"), ("GraphQL", "technical"), ("ETL", "technical"),
    ("Excel", "technical"), ("Java", "technical"), ("C++", "technical"),
    # soft
    ("Communication", "soft"), ("Problem Solving", "soft"), ("Teamwork", "soft"),
    ("Leadership", "soft"), ("Critical Thinking", "soft"), ("Time Management", "soft"),
    # domain
    ("Data Engineering", "domain"), ("Cloud Computing", "domain"),
    ("Software Architecture", "domain"), ("Business Intelligence", "domain"),
    ("Agile", "domain"), ("Product Management", "domain"),
]

# ── JOB → SKILLS (job index → [(skill name, weight, is_required)]) ───────────
JOB_SKILLS = {
    0: [("Python", 0.9, True), ("SQL", 0.9, True), ("Data Analysis", 0.95, True),
        ("Power BI", 0.8, True), ("Excel", 0.7, False), ("Statistics", 0.75, True),
        ("Communication", 0.6, False), ("Problem Solving", 0.65, False)],
    1: [("Python", 0.95, True), ("FastAPI", 0.85, True), ("PostgreSQL", 0.8, True),
        ("Docker", 0.8, True), ("REST APIs", 0.85, True), ("Git", 0.7, False),
        ("Teamwork", 0.6, False), ("Problem Solving", 0.65, False)],
    2: [("Python", 0.95, True), ("Machine Learning", 0.95, True), ("TensorFlow", 0.85, True),
        ("Scikit-learn", 0.85, True), ("Pandas", 0.8, True), ("Statistics", 0.9, True),
        ("NLP", 0.7, False), ("Deep Learning", 0.8, True), ("Communication", 0.6, False)],
    3: [("React", 0.9, True), ("TypeScript", 0.85, True), ("REST APIs", 0.8, True),
        ("GraphQL", 0.7, False), ("Git", 0.7, False), ("Problem Solving", 0.65, False)],
    4: [("AWS", 0.95, True), ("Kubernetes", 0.9, True), ("Terraform", 0.85, True),
        ("Docker", 0.85, True), ("Linux", 0.8, True), ("CI/CD", 0.85, True),
        ("Cloud Computing", 0.9, True)],
    5: [("Python", 0.9, True), ("Machine Learning", 0.9, True), ("Docker", 0.85, True),
        ("NLP", 0.8, True), ("Deep Learning", 0.8, True), ("ETL", 0.7, False),
        ("Data Engineering", 0.85, True)],
    6: [("SQL", 0.95, True), ("Power BI", 0.9, True), ("Tableau", 0.85, True),
        ("Data Analysis", 0.85, True), ("Business Intelligence", 0.9, True),
        ("Statistics", 0.7, False), ("Communication", 0.65, False)],
    7: [("Docker", 0.9, True), ("Kubernetes", 0.9, True), ("Linux", 0.85, True),
        ("Terraform", 0.85, True), ("CI/CD", 0.95, True), ("AWS", 0.8, False),
        ("Cloud Computing", 0.8, True)],
    8: [("React", 0.9, True), ("Python", 0.8, True), ("PostgreSQL", 0.75, True),
        ("Node.js", 0.8, True), ("REST APIs", 0.85, True), ("Git", 0.7, False),
        ("Teamwork", 0.6, False), ("Agile", 0.7, False)],
    9: [("Communication", 0.9, True), ("Leadership", 0.9, True), ("Product Management", 0.95, True),
        ("Agile", 0.85, True), ("Critical Thinking", 0.8, True), ("Data Analysis", 0.7, False)],
}

# ── COURSES ──────────────────────────────────────────────────────────────────
COURSES = [
    ("CS101", "Introduction to Programming", "Fundamentals of programming using Python. Variables, loops, functions, OOP basics.", "Write Python programs, understand control flow, work with data structures.", "CS"),
    ("CS201", "Data Structures and Algorithms", "Arrays, linked lists, trees, graphs, sorting and searching algorithms. Complexity analysis.", "Implement and analyze data structures. Apply algorithms to solve problems.", "CS"),
    ("CS301", "Database Systems", "Relational database design, SQL, normalization, transactions, indexing, PostgreSQL.", "Write complex SQL queries, design normalized schemas, optimize database performance.", "CS"),
    ("CS340", "Machine Learning", "Supervised and unsupervised learning, regression, classification, clustering. Scikit-learn and Python.", "Build ML models, evaluate performance, apply feature engineering.", "CS"),
    ("CS350", "Web Development", "HTML, CSS, JavaScript, React. REST API design. Frontend frameworks and responsive design.", "Build full-stack web applications, work with APIs, create responsive UIs.", "CS"),
    ("CS360", "Cloud Computing", "AWS services, IaaS/PaaS/SaaS, Terraform, Kubernetes, Docker, cloud security.", "Deploy applications on AWS, manage containers, write infrastructure as code.", "CS"),
    ("CS401", "Deep Learning", "Neural networks, CNNs, RNNs, transformers. TensorFlow and PyTorch. NLP fundamentals.", "Build and train deep learning models, apply to image and text tasks.", "CS"),
    ("CS410", "Software Engineering", "Agile methodologies, design patterns, testing, CI/CD, Git, Docker, code review.", "Apply software engineering best practices, work in agile teams, write testable code.", "CS"),
    ("CS420", "Data Engineering", "ETL pipelines, Apache Spark, data warehouses, SQL optimization, Pandas.", "Build scalable data pipelines, work with large datasets, design data architectures.", "CS"),
    ("CS430", "DevOps", "Linux, CI/CD with GitHub Actions, Docker, Kubernetes, monitoring, Ansible.", "Automate deployment pipelines, manage infrastructure, containerize applications.", "CS"),
    ("STAT201", "Statistics for Data Science", "Probability, hypothesis testing, regression, distributions. Python and Excel.", "Apply statistical methods to data analysis, interpret results, use statistical software.", "STAT"),
    ("CS211", "Object-Oriented Programming", "Java OOP: classes, inheritance, polymorphism, design patterns, unit testing.", "Design and implement OOP solutions in Java, write unit tests.", "CS"),
    ("CS320", "Operating Systems", "Linux internals, processes, memory management, file systems, shell scripting.", "Understand OS principles, write shell scripts, work with Linux systems.", "CS"),
    ("CS450", "Natural Language Processing", "Text preprocessing, word embeddings, transformers, Arabic NLP, BERT.", "Build NLP pipelines, work with Arabic text, apply transformer models.", "CS"),
    ("BUS301", "Product Management", "Product roadmaps, user research, agile, OKRs, stakeholder communication, analytics.", "Define product strategy, write PRDs, manage product lifecycle, communicate with teams.", "BUS"),
]

# ── COURSE → SKILLS (course code → [(skill name, confidence)]) ───────────────
COURSE_SKILLS = {
    "CS101":  [("Python", 0.95), ("Problem Solving", 0.8), ("Git", 0.6)],
    "CS201":  [("Python", 0.85), ("Problem Solving", 0.9), ("C++", 0.7), ("Critical Thinking", 0.75)],
    "CS301":  [("SQL", 0.95), ("PostgreSQL", 0.85), ("Data Analysis", 0.7), ("ETL", 0.6)],
    "CS340":  [("Machine Learning", 0.95), ("Python", 0.9), ("Scikit-learn", 0.9),
               ("Pandas", 0.85), ("Statistics", 0.8)],
    "CS350":  [("React", 0.9), ("TypeScript", 0.75), ("REST APIs", 0.85),
               ("GraphQL", 0.6), ("Git", 0.7)],
    "CS360":  [("AWS", 0.9), ("Docker", 0.85), ("Kubernetes", 0.8),
               ("Terraform", 0.8), ("Cloud Computing", 0.9)],
    "CS401":  [("Deep Learning", 0.95), ("TensorFlow", 0.9), ("Python", 0.85),
               ("NLP", 0.7), ("Statistics", 0.75)],
    "CS410":  [("Git", 0.85), ("Docker", 0.75), ("CI/CD", 0.7),
               ("Agile", 0.8), ("Teamwork", 0.75), ("Python", 0.7)],
    "CS420":  [("Python", 0.85), ("SQL", 0.8), ("ETL", 0.9),
               ("Pandas", 0.85), ("Data Engineering", 0.9)],
    "CS430":  [("Linux", 0.9), ("Docker", 0.9), ("Kubernetes", 0.85),
               ("CI/CD", 0.9), ("AWS", 0.7), ("Terraform", 0.75)],
    "STAT201": [("Statistics", 0.95), ("Python", 0.7), ("Excel", 0.75), ("Data Analysis", 0.8)],
    "CS211":  [("Java", 0.95), ("Problem Solving", 0.8), ("Critical Thinking", 0.7)],
    "CS320":  [("Linux", 0.85), ("C++", 0.7), ("Problem Solving", 0.75)],
    "CS450":  [("NLP", 0.95), ("Python", 0.85), ("Deep Learning", 0.8), ("TensorFlow", 0.7)],
    "BUS301": [("Product Management", 0.95), ("Communication", 0.85),
               ("Leadership", 0.8), ("Agile", 0.85), ("Critical Thinking", 0.75)],
}

# ── STUDENTS + COURSE ENROLLMENTS ────────────────────────────────────────────
STUDENTS = [
    {"name": "سلمى الغامدي", "email": "salma@masar.demo", "major": "Computer Science", "year": 2,
     "courses": ["CS101", "CS201", "CS301", "STAT201", "CS211"]},
    {"name": "خالد العمري",  "email": "khalid@masar.demo", "major": "Computer Science", "year": 3,
     "courses": ["CS101", "CS201", "CS301", "CS340", "CS350", "CS410", "STAT201", "CS211"]},
    {"name": "نورة الزهراني", "email": "nora@masar.demo",  "major": "Computer Science", "year": 4,
     "courses": ["CS101", "CS201", "CS301", "CS340", "CS350", "CS360", "CS401", "CS410",
                 "CS420", "CS430", "STAT201", "CS211", "CS320"]},
]

# ── PROJECTS (same as ingest_data.py) ─────────────────────────────────────────
PROJECTS = [
    {"title": "Customer Churn Prediction Dashboard", "company": "STC Analytics",
     "description": "Build a machine learning model to predict customer churn and create an interactive dashboard.",
     "difficulty": "intermediate",
     "required_skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "Power BI"], "hours": 40},
    {"title": "REST API for E-commerce Platform", "company": "Noon Tech",
     "description": "Design and implement a RESTful API with authentication, search, and filtering capabilities.",
     "difficulty": "intermediate",
     "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs"], "hours": 35},
    {"title": "Arabic Sentiment Analysis Tool", "company": "Takamol",
     "description": "Build an NLP model that classifies Arabic social media text into positive, negative, or neutral.",
     "difficulty": "advanced",
     "required_skills": ["Python", "NLP", "Deep Learning", "TensorFlow"], "hours": 60},
    {"title": "Sales Data Pipeline", "company": "SABB Bank",
     "description": "Build an ETL pipeline collecting sales data from multiple sources into a data warehouse.",
     "difficulty": "beginner",
     "required_skills": ["Python", "SQL", "ETL", "Data Engineering", "Excel"], "hours": 25},
    {"title": "Mobile App UI Prototype", "company": "Foodics",
     "description": "Design and implement a React Native UI for restaurant management with real-time order tracking.",
     "difficulty": "intermediate",
     "required_skills": ["React", "TypeScript", "REST APIs"], "hours": 45},
    {"title": "Network Intrusion Detection System", "company": "ZATCA",
     "description": "Build a machine learning based system to detect network intrusions in real time.",
     "difficulty": "advanced",
     "required_skills": ["Python", "Machine Learning", "Scikit-learn", "Statistics"], "hours": 55},
    {"title": "Cloud Cost Optimization Dashboard", "company": "Accenture Saudi Arabia",
     "description": "Build a dashboard monitoring AWS cloud resource usage and suggesting optimizations.",
     "difficulty": "intermediate",
     "required_skills": ["AWS", "Python", "Cloud Computing", "Docker"], "hours": 38},
]


def seed(c):
    cur = c.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ── Skills ────────────────────────────────────────────────────────────────
    print("\n--- Skills ---")
    skill_id: dict[str, int] = {}
    for name, cat in SKILLS:
        cur.execute("""
            INSERT INTO skills (name, category)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category
            RETURNING id
        """, (name, cat))
        skill_id[name] = cur.fetchone()["id"]
    c.commit()
    print(f"  ✅ {len(skill_id)} skills")

    # ── Jobs ──────────────────────────────────────────────────────────────────
    print("\n--- Jobs ---")
    job_ids: list[int] = []
    for j in JOBS:
        cur.execute("""
            INSERT INTO jobs (title, company, description, location)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (j["title"], j["company"], j["description"], j["location"]))
        row = cur.fetchone()
        if row:
            job_ids.append(row["id"])
            print(f"  ✓ {j['title']} @ {j['company']}")
        else:
            cur.execute("SELECT id FROM jobs WHERE title=%s AND company=%s",
                        (j["title"], j["company"]))
            job_ids.append(cur.fetchone()["id"])
    c.commit()

    # ── Job skills ────────────────────────────────────────────────────────────
    print("\n--- Job skills ---")
    for idx, entries in JOB_SKILLS.items():
        jid = job_ids[idx]
        for sname, weight, required in entries:
            sid = skill_id.get(sname)
            if sid:
                cur.execute("""
                    INSERT INTO job_skills (job_id, skill_id, weight, is_required)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
                """, (jid, sid, weight, required))
    c.commit()
    print("  ✅ linked")

    # ── Courses ───────────────────────────────────────────────────────────────
    print("\n--- Courses ---")
    for code, title, desc, outcomes, dept in COURSES:
        cur.execute("""
            INSERT INTO courses (course_code, title, description, learning_outcomes, department)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (course_code) DO UPDATE SET title = EXCLUDED.title
        """, (code, title, desc, outcomes, dept))
        print(f"  ✓ {code}")
    c.commit()

    # ── Course skills ─────────────────────────────────────────────────────────
    print("\n--- Course skills ---")
    for code, entries in COURSE_SKILLS.items():
        cur.execute("SELECT id FROM courses WHERE course_code=%s", (code,))
        row = cur.fetchone()
        if not row:
            continue
        cid = row["id"]
        for sname, conf in entries:
            sid = skill_id.get(sname)
            if sid:
                cur.execute("""
                    INSERT INTO course_skills (course_id, skill_id, confidence, extraction_method)
                    VALUES (%s, %s, %s, 'manual') ON CONFLICT DO NOTHING
                """, (cid, sid, conf))
    c.commit()
    print("  ✅ linked")

    # ── Students + enrollments ────────────────────────────────────────────────
    print("\n--- Students ---")
    for s in STUDENTS:
        cur.execute("""
            INSERT INTO students (name, email, major, year_of_study, university)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        """, (s["name"], s["email"], s["major"], s["year"], "King Khalid University"))
        row = cur.fetchone()
        if row:
            sid = row["id"]
        else:
            cur.execute("SELECT id FROM students WHERE email=%s", (s["email"],))
            sid = cur.fetchone()["id"]
        for code in s["courses"]:
            cur.execute("SELECT id FROM courses WHERE course_code=%s", (code,))
            crow = cur.fetchone()
            if crow:
                cur.execute("""
                    INSERT INTO student_courses (student_id, course_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                """, (sid, crow["id"]))
        print(f"  ✓ {s['name']} (id={sid}, year={s['year']}, {len(s['courses'])} courses)")
    c.commit()

    # ── Projects ─────────────────────────────────────────────────────────────
    print("\n--- Projects ---")
    for p in PROJECTS:
        cur.execute("""
            INSERT INTO projects (title, company, description, difficulty, required_skills, estimated_hours)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s) ON CONFLICT DO NOTHING
        """, (p["title"], p["company"], p["description"],
              p["difficulty"], json.dumps(p["required_skills"]), p["hours"]))
        print(f"  ✓ {p['title']}")
    c.commit()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n--- Verification ---")
    for table in ["skills", "jobs", "job_skills", "courses", "course_skills",
                  "students", "student_courses", "projects"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        n = cur.fetchone()["count"]
        print(f"  {'✅' if n > 0 else '❌'} {table}: {n}")

    cur.close()


if __name__ == "__main__":
    c = psycopg2.connect(**DB_CONFIG)
    seed(c)
    c.close()
    print("\n✅ Seed complete — now run: python3 scripts/add_embeddings.py")
