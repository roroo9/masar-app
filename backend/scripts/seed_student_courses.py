import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "masar",
    "user": "masar_user",
    "password": "masar_pass"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def seed_student_courses():
    """Link demo students to courses based on their year."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get course IDs
    cursor.execute("SELECT id, course_code FROM courses ORDER BY id")
    courses = {row[1]: row[0] for row in cursor.fetchall()}

    # Get student IDs
    cursor.execute("SELECT id, name, year_of_study FROM students")
    students = cursor.fetchall()

    # Define which courses each student completed
    student_courses = {
        # سلمى - Year 2 - beginner courses
        1: [
            "CS10001", "CS1002", "CS1003",
            "CS1251", "CS1253", "CS10403"
        ],
        # خالد - Year 3 - intermediate courses
        2: [
            "CS10001", "CS1002", "CS1003",
            "CS1251", "CS1253", "CS10403",
            "CS1007", "CS1006", "CS1008",
            "CS1255", "CS1256", "CS1009"
        ],
        # نورة - Year 4 - advanced courses
        3: [
            "CS10001", "CS1002", "CS1003",
            "CS1251", "CS1253", "CS10403",
            "CS1007", "CS1006", "CS1008",
            "CS1255", "CS1256", "CS1009",
            "CS1502", "CS1503", "CS1505",
            "CS1506", "CS1759", "CS1510",
            "CS1763", "CS1769"
        ]
    }

    for student in students:
        student_id = student[0]
        student_name = student[1]
        year = student[2]

        course_codes = student_courses.get(student_id, [])
        linked = 0

        for code in course_codes:
            course_id = courses.get(code)
            if course_id:
                try:
                    cursor.execute("""
                        INSERT INTO student_courses (student_id, course_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (student_id, course_id))
                    linked += 1
                except Exception as e:
                    print(f"Error: {e}")

        conn.commit()
        print(f"✓ {student_name} (Year {year}): linked to {linked} courses")

    cursor.close()
    conn.close()
    print("\n✅ Student courses seeded!")

if __name__ == "__main__":
    seed_student_courses()