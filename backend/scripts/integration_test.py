import psycopg2
import psycopg2.extras
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

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_integration_test():
    print("=== Masar Integration Test ===\n")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    passed = 0
    failed = 0

    # Test 1: Database connection
    try:
        cursor.execute("SELECT 1")
        print("✅ Test 1: Database connection")
        passed += 1
    except:
        print("❌ Test 1: Database connection")
        failed += 1

    # Test 2: Jobs exist
    try:
        cursor.execute("SELECT COUNT(*) as count FROM jobs")
        count = cursor.fetchone()['count']
        assert count > 0
        print(f"✅ Test 2: Jobs exist ({count} jobs)")
        passed += 1
    except:
        print("❌ Test 2: Jobs exist")
        failed += 1

    # Test 3: Courses exist
    try:
        cursor.execute("SELECT COUNT(*) as count FROM courses")
        count = cursor.fetchone()['count']
        assert count > 0
        print(f"✅ Test 3: Courses exist ({count} courses)")
        passed += 1
    except:
        print("❌ Test 3: Courses exist")
        failed += 1

    # Test 4: Students exist
    try:
        cursor.execute("SELECT COUNT(*) as count FROM students")
        count = cursor.fetchone()['count']
        assert count == 3
        print(f"✅ Test 4: Demo students exist ({count} students)")
        passed += 1
    except:
        print("❌ Test 4: Demo students exist")
        failed += 1

    # Test 5: Student courses linked
    try:
        cursor.execute("SELECT COUNT(*) as count FROM student_courses")
        count = cursor.fetchone()['count']
        assert count > 0
        print(f"✅ Test 5: Student courses linked ({count} links)")
        passed += 1
    except:
        print("❌ Test 5: Student courses linked")
        failed += 1

    # Test 6: Projects exist
    try:
        cursor.execute("SELECT COUNT(*) as count FROM projects")
        count = cursor.fetchone()['count']
        assert count > 0
        print(f"✅ Test 6: Projects exist ({count} projects)")
        passed += 1
    except:
        print("❌ Test 6: Projects exist")
        failed += 1

    # Test 7: Skills extracted (waiting for Reham)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM skills")
        count = cursor.fetchone()['count']
        if count > 0:
            print(f"✅ Test 7: Skills extracted ({count} skills)")
            passed += 1
        else:
            print(f"⏳ Test 7: Skills not yet extracted")
    except:
        print("❌ Test 7: Skills table error")
        failed += 1

    # Test 8: Job skills linked (waiting for Reham)
    try:
        cursor.execute("SELECT COUNT(*) as count FROM job_skills")
        count = cursor.fetchone()['count']
        if count > 0:
            print(f"✅ Test 8: Job skills linked ({count} links)")
            passed += 1
        else:
            print(f"⏳ Test 8: Job skills not yet linked")
    except:
        print("❌ Test 8: Job skills table error")
        failed += 1

    # Test 9: pgvector working
    try:
        cursor.execute("""
            SELECT COUNT(*) as count FROM skills
            WHERE embedding IS NOT NULL
        """)
        count = cursor.fetchone()['count']
        if count > 0:
            print(f"✅ Test 9: Embeddings stored ({count} skills with vectors)")
            passed += 1
        else:
            print(f"⏳ Test 9: No embeddings yet")
    except:
        print("❌ Test 9: pgvector error")
        failed += 1

    cursor.close()
    conn.close()

    print(f"\n=== Results: {passed} passed, {failed} failed ===")

    if failed == 0:
        print("✅ All critical tests passed!")
    else:
        print("❌ Some tests failed — check above")

if __name__ == "__main__":
    run_integration_test()