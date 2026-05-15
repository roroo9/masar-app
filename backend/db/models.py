# Data models for Masar platform
# These represent the structure of each table in the database

class Skill:
    """
    Represents a skill in the unified taxonomy.
    Table: skills
    """
    def __init__(self, id, name, category, embedding=None):
        self.id = id
        self.name = name
        self.category = category  # 'technical', 'soft', 'domain'
        self.embedding = embedding  # 768-dim vector from SBERT

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category
        }

class Job:
    """
    Represents a job posting from Saudi market.
    Table: jobs
    """
    def __init__(self, id, title, company, description,
                 location=None, source_url=None):
        self.id = id
        self.title = title
        self.company = company
        self.description = description
        self.location = location
        self.source_url = source_url

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location
        }

class Course:
    """
    Represents a university course.
    Table: courses
    """
    def __init__(self, id, course_code, title,
                 description=None, learning_outcomes=None,
                 department=None):
        self.id = id
        self.course_code = course_code
        self.title = title
        self.description = description
        self.learning_outcomes = learning_outcomes
        self.department = department

    def to_dict(self):
        return {
            "id": self.id,
            "course_code": self.course_code,
            "title": self.title,
            "department": self.department
        }

class Student:
    """
    Represents a university student.
    Table: students
    """
    def __init__(self, id, name, email, major,
                 year_of_study, university=None):
        self.id = id
        self.name = name
        self.email = email
        self.major = major
        self.year_of_study = year_of_study
        self.university = university

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "major": self.major,
            "year_of_study": self.year_of_study,
            "university": self.university
        }

class ReadinessScore:
    """
    Represents a cached readiness score result.
    Table: readiness_scores
    """
    def __init__(self, id, student_id, job_id, score,
                 matched_skills=None, missing_skills=None,
                 partial_skills=None, explanation=None):
        self.id = id
        self.student_id = student_id
        self.job_id = job_id
        self.score = score
        self.matched_skills = matched_skills
        self.missing_skills = missing_skills
        self.partial_skills = partial_skills
        self.explanation = explanation

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "job_id": self.job_id,
            "score": self.score
        }

class Project:
    """
    Represents a company project for students.
    Table: projects
    """
    def __init__(self, id, title, company, description,
                 difficulty, required_skills=None,
                 estimated_hours=None):
        self.id = id
        self.title = title
        self.company = company
        self.description = description
        self.difficulty = difficulty
        self.required_skills = required_skills
        self.estimated_hours = estimated_hours

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "difficulty": self.difficulty,
            "estimated_hours": self.estimated_hours
        }