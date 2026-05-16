import json
import psycopg2
import psycopg2.extras
import os

# Database connection
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def ingest_jobs(conn):
    """Load all jobs from JSON into the database."""
    print("\n--- Ingesting Jobs ---")
    
    with open("data/jobs/saudi_tech_jobs.json", encoding="utf-8") as f:
        jobs = json.load(f)
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for job in jobs:
        title = job.get("title", "").strip()
        company = job.get("company", "").strip()
        description = job.get("description", "").strip()
        location = job.get("location", "Saudi Arabia").strip()
        source_url = job.get("source_url", "").strip()
        
        # Skip if missing essential fields
        if not title or not description:
            skipped += 1
            continue
        
        # Skip if description too short
        if len(description) < 50:
            skipped += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO jobs (title, company, description, location, source_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (title, company, description, location, source_url))
            
            if cursor.rowcount > 0:
                inserted += 1
                print(f"  ✓ {title} at {company}")
            else:
                skipped += 1
                
        except Exception as e:
            print(f"  ✗ Error inserting {title}: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    print(f"\nJobs: {inserted} inserted, {skipped} skipped")
    return inserted

def ingest_courses(conn):
    """Load all courses from JSON into the database."""
    print("\n--- Ingesting Courses ---")
    
    with open("data/courses/kku_cs_courses.json", encoding="utf-8") as f:
        courses = json.load(f)
    
    cursor = conn.cursor()
    inserted = 0
    skipped = 0
    
    for course in courses:
        code = course.get("code", "").strip()
        title = course.get("title", "").strip()
        description = course.get("description", "").strip()
        learning_outcomes = course.get("learning_outcomes", "").strip()
        department = course.get("department", "CS").strip()
        
        # Skip if missing essential fields
        if not code or not title:
            skipped += 1
            continue
        
        # Combine description and outcomes as raw text
        raw_text = f"{title}. {description}. {learning_outcomes}"
        
        try:
            cursor.execute("""
                INSERT INTO courses 
                (course_code, title, description, learning_outcomes, department, raw_text)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (course_code) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    learning_outcomes = EXCLUDED.learning_outcomes,
                    raw_text = EXCLUDED.raw_text
            """, (code, title, description, learning_outcomes, department, raw_text))
            
            inserted += 1
            print(f"  ✓ {code}: {title}")
            
        except Exception as e:
            print(f"  ✗ Error inserting {code}: {e}")
            skipped += 1
    
    conn.commit()
    cursor.close()
    print(f"\nCourses: {inserted} inserted, {skipped} skipped")
    return inserted

def seed_demo_students(conn):
    """Create 3 demo students for testing."""
    print("\n--- Seeding Demo Students ---")
    
    cursor = conn.cursor()
    
    students = [
        {
            "name": "سلمى الغامدي",
            "email": "salma@masar.demo",
            "major": "Computer Science",
            "year": 2
        },
        {
            "name": "خالد العمري",
            "email": "khalid@masar.demo",
            "major": "Computer Science",
            "year": 3
        },
        {
            "name": "نورة الزهراني",
            "email": "nora@masar.demo",
            "major": "Computer Science",
            "year": 4
        }
    ]
    
    for student in students:
        try:
            cursor.execute("""
                INSERT INTO students (name, email, major, year_of_study, university)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                student["name"],
                student["email"],
                student["major"],
                student["year"],
                "Al Baha University"
            ))
            print(f"  ✓ {student['name']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    conn.commit()
    cursor.close()

def seed_demo_projects(conn):
    """Add sample company projects."""
    print("\n--- Seeding Demo Projects ---")
    
    cursor = conn.cursor()
    
    projects = [
        {
            "title": "Customer Churn Prediction Dashboard",
            "company": "STC Analytics",
            "description": "Build a machine learning model to predict customer churn and create an interactive dashboard to visualize results and key factors.",
            "difficulty": "intermediate",
            "required_skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "Power BI"],
            "hours": 40
        },
        {
            "title": "REST API for E-commerce Platform",
            "company": "Noon Tech",
            "description": "Design and implement a RESTful API for a product catalog with authentication, search, and filtering capabilities.",
            "difficulty": "intermediate",
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs"],
            "hours": 35
        },
        {
            "title": "Arabic Sentiment Analysis Tool",
            "company": "Takamol",
            "description": "Build an NLP model that classifies Arabic social media text into positive, negative, or neutral sentiment.",
            "difficulty": "advanced",
            "required_skills": ["Python", "NLP", "Deep Learning", "Arabic NLP", "PyTorch"],
            "hours": 60
        },
        {
            "title": "Sales Data Pipeline",
            "company": "SABB Bank",
            "description": "Build an ETL pipeline that collects sales data from multiple sources, cleans it, and loads it into a data warehouse.",
            "difficulty": "beginner",
            "required_skills": ["Python", "SQL", "ETL", "Data Engineering", "Excel"],
            "hours": 25
        },
        {
            "title": "Mobile App UI Prototype",
            "company": "Foodics",
            "description": "Design and implement a React Native UI for a restaurant management mobile app with real-time order tracking.",
            "difficulty": "intermediate",
            "required_skills": ["React Native", "JavaScript", "UI/UX", "Mobile Development", "Figma"],
            "hours": 45
        },
        {
            "title": "Network Intrusion Detection System",
            "company": "ZATCA",
            "description": "Build a machine learning based system to detect network intrusions and anomalies in real time.",
            "difficulty": "advanced",
            "required_skills": ["Python", "Machine Learning", "Cybersecurity", "Network Security", "Scikit-learn"],
            "hours": 55
        },
        {
            "title": "Cloud Cost Optimization Dashboard",
            "company": "Accenture Saudi Arabia",
            "description": "Build a dashboard that monitors AWS cloud resource usage and suggests cost optimization strategies.",
            "difficulty": "intermediate",
            "required_skills": ["AWS", "Python", "Cloud Computing", "Data Visualization", "Docker"],
            "hours": 38
        }
    ]
    
    for project in projects:
        try:
            cursor.execute("""
                INSERT INTO projects 
                (title, company, description, difficulty, required_skills, estimated_hours)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT DO NOTHING
            """, (
                project["title"],
                project["company"],
                project["description"],
                project["difficulty"],
                json.dumps(project["required_skills"]),
                project["hours"]
            ))
            print(f"  ✓ {project['title']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    conn.commit()
    cursor.close()

def verify_ingestion(conn):
    """Verify everything was inserted correctly."""
    print("\n--- Verification ---")
    
    cursor = conn.cursor()
    
    tables = ["jobs", "courses", "students", "projects"]
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {table}: {count} records")
    
    cursor.close()

if __name__ == "__main__":
    print("Starting Masar data ingestion...")
    print("Connecting to database...")
    
    try:
        conn = get_connection()
        print("✅ Connected to database!")
        
        ingest_jobs(conn)
        ingest_courses(conn)
        seed_demo_students(conn)
        seed_demo_projects(conn)
        verify_ingestion(conn)
        
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure Docker is running and database is up.")