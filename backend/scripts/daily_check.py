import psycopg2
import psycopg2.extras
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def check_database():
    print("--- Database Check ---")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        checks = {
            "jobs": (72, "SELECT COUNT(*) as c FROM jobs"),
            "courses": (53, "SELECT COUNT(*) as c FROM courses"),
            "students": (3, "SELECT COUNT(*) as c FROM students"),
            "skills": (334, "SELECT COUNT(*) as c FROM skills"),
            "embeddings": (334, "SELECT COUNT(*) as c FROM skills WHERE embedding IS NOT NULL"),
            "job_skills": (353, "SELECT COUNT(*) as c FROM job_skills"),
            "projects": (7, "SELECT COUNT(*) as c FROM projects"),
        }

        all_good = True
        for name, (expected, query) in checks.items():
            cursor.execute(query)
            count = cursor.fetchone()['c']
            status = "✅" if count >= expected else "❌"
            if count < expected:
                all_good = False
            print(f"  {status} {name}: {count}")

        cursor.close()
        conn.close()
        return all_good

    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_api():
    print("\n--- API Check ---")
    try:
        endpoints = [
            ("GET", "http://localhost:8000/", "root"),
            ("GET", "http://localhost:8000/api/jobs/", "jobs"),
            ("GET", "http://localhost:8000/api/students/1", "student"),
            ("GET", "http://localhost:8000/api/skills/", "skills"),
        ]

        all_good = True
        for method, url, name in endpoints:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {name}: {url}")
                else:
                    print(f"  ❌ {name}: status {response.status_code}")
                    all_good = False
            except Exception as e:
                print(f"  ❌ {name}: API not running - start uvicorn first")
                all_good = False

        return all_good

    except Exception as e:
        print(f"  ❌ API check failed: {e}")
        return False

def check_gap_analyzer():
    print("\n--- Gap Analyzer Check ---")
    try:
        from core.gap_analyzer import analyze_gap
        result = analyze_gap(3, 4)
        if "error" not in result:
            print(f"  ✅ Gap analyzer working: {result['readiness_score']}% for نورة vs ML Engineer")
            return True
        else:
            print(f"  ❌ Gap analyzer error: {result['error']}")
            return False
    except Exception as e:
        print(f"  ❌ Gap analyzer failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Masar Daily System Check ===\n")

    db_ok = check_database()
    api_ok = check_api()
    gap_ok = check_gap_analyzer()

    print("\n=== Summary ===")
    print(f"  {'✅' if db_ok else '❌'} Database")
    print(f"  {'✅' if api_ok else '❌'} API Server")
    print(f"  {'✅' if gap_ok else '❌'} Gap Analyzer")

    if db_ok and api_ok and gap_ok:
        print("\n✅ All systems go! Ready for demo.")
    else:
        print("\n❌ Some systems need attention.")