import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gap_analyzer import analyze_gap, get_student_skills, get_all_jobs

def test_all_students():
    print("=== Testing All 3 Demo Students ===\n")

    students = [
        {"id": 1, "name": "سلمى الغامدي", "year": 2},
        {"id": 2, "name": "خالد العمري", "year": 3},
        {"id": 3, "name": "نورة الزهراني", "year": 4},
    ]

    jobs = [
        {"id": 1, "title": "Data Analyst at STC"},
        {"id": 2, "title": "Backend Developer at Careem"},
        {"id": 4, "title": "Machine Learning Engineer at Aramco"},
    ]

    for student in students:
        skills = get_student_skills(student['id'])
        print(f"--- {student['name']} (Year {student['year']}) ---")
        print(f"Total skills: {len(skills)}")

        for job in jobs:
            result = analyze_gap(student['id'], job['id'])
            if "error" not in result:
                print(f"  vs {job['title']}: {result['readiness_score']}% ready")
                print(f"     Matched: {result['matched_count']} | Missing: {result['missing_count']} | Partial: {result['partial_count']}")
        print()

if __name__ == "__main__":
    test_all_students()