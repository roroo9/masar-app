-- Enable pgvector extension (allows storing AI embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================
-- SKILLS TABLE
-- Central skill taxonomy — every skill in the system lives here
-- =====================
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    category VARCHAR(100),        -- 'technical', 'soft', 'domain'
    embedding vector(384),        -- 384-dim from paraphrase-multilingual-MiniLM-L12-v2
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================
-- COURSES TABLE
-- University course information
-- =====================
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,   -- e.g. 'CS340'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    learning_outcomes TEXT,
    department VARCHAR(100),
    raw_text TEXT
);

-- =====================
-- COURSE_SKILLS TABLE
-- Which skills does each course teach?
-- =====================
CREATE TABLE IF NOT EXISTS course_skills (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 1.0,
    extraction_method VARCHAR(50),   -- 'llm', 'manual'
    UNIQUE(course_id, skill_id)
);

-- =====================
-- JOBS TABLE
-- Job postings from Saudi market
-- =====================
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    company VARCHAR(200),
    description TEXT,
    location VARCHAR(200) DEFAULT 'Saudi Arabia',
    source_url VARCHAR(500),
    collected_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================
-- JOB_SKILLS TABLE
-- Which skills does each job require?
-- =====================
CREATE TABLE IF NOT EXISTS job_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    weight FLOAT DEFAULT 1.0,
    is_required BOOLEAN DEFAULT TRUE,
    UNIQUE(job_id, skill_id)
);

-- =====================
-- STUDENTS TABLE
-- =====================
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    university VARCHAR(200) DEFAULT 'King Khalid University',
    major VARCHAR(200),
    year_of_study INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================
-- STUDENT_COURSES TABLE
-- Which courses has the student completed?
-- =====================
CREATE TABLE IF NOT EXISTS student_courses (
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    grade VARCHAR(5),
    semester VARCHAR(20),
    PRIMARY KEY (student_id, course_id)
);

-- =====================
-- STUDENT_EXTRA_SKILLS TABLE
-- Skills from internships, projects, self-study
-- =====================
CREATE TABLE IF NOT EXISTS student_extra_skills (
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    proficiency INTEGER CHECK (proficiency BETWEEN 1 AND 5),
    source VARCHAR(100),    -- 'internship', 'project', 'self-study'
    PRIMARY KEY (student_id, skill_id)
);

-- =====================
-- READINESS_SCORES TABLE
-- Cached results of gap analysis (so we don't recompute every time)
-- =====================
CREATE TABLE IF NOT EXISTS readiness_scores (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,
    matched_skills JSONB,
    missing_skills JSONB,
    partial_skills JSONB,
    explanation TEXT,
    computed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, job_id)
);

-- =====================
-- PROJECTS TABLE
-- Real projects from companies
-- =====================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    company VARCHAR(200),
    description TEXT,
    difficulty VARCHAR(20),         -- 'beginner', 'intermediate', 'advanced'
    required_skills JSONB,          -- ["Python", "SQL", "Machine Learning"]
    estimated_hours INTEGER,
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================
-- INDEXES
-- Speed up the most common queries
-- =====================
CREATE INDEX IF NOT EXISTS idx_course_skills_course ON course_skills(course_id);
CREATE INDEX IF NOT EXISTS idx_course_skills_skill ON course_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_job ON job_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_student_courses_student ON student_courses(student_id);
CREATE INDEX IF NOT EXISTS idx_readiness_student ON readiness_scores(student_id);

-- Vector similarity search index (for semantic skill matching)
-- NOTE: Run migrate_vector_dim.sql first if upgrading an existing DB
CREATE INDEX IF NOT EXISTS idx_skills_embedding
ON skills USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);