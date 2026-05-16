import json
import os
import anthropic
import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# Initialize Claude client
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Load multilingual SBERT model (Arabic + English)
print("Loading Sentence-BERT model...")
sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("✅ Model loaded!")

from db.database import get_connection

EXTRACTION_PROMPT = """You are a skill extraction expert for an AI career platform in Saudi Arabia.

Given the following text (either a job description or a university course description), extract ALL skills mentioned or implied.

Classify each skill as:
- "technical": programming languages, tools, frameworks, platforms, technical concepts
- "soft": communication, teamwork, problem-solving, leadership, etc.
- "domain": business knowledge, industry-specific knowledge

Return ONLY a valid JSON object with this exact structure:
{{
  "skills": [
    {{
      "name": "Python",
      "type": "technical",
      "confidence": 0.95
    }}
  ]
}}

Rules:
- Be specific: "React.js" not just "framework"
- Include implied skills: a course on "Database Systems" implies SQL, data modeling
- Normalize names: "ML", "Machine Learning", "تعلم الآلة" should all become "Machine Learning"
- Include soft skills when clearly mentioned
- Confidence: 1.0 = explicitly stated, 0.7-0.9 = strongly implied, 0.5-0.7 = loosely implied
- Return 5-15 skills maximum
- ONLY return the JSON object, nothing else

TEXT TO ANALYZE:
{text}
"""

def extract_skills_from_text(text: str) -> List[Dict]:
    """Extract skills from any text using Claude."""
    try:
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(text=text[:3000])
                }
            ]
        )

        result_text = response.content[0].text.strip()

        # Clean JSON if wrapped in markdown
        if "```" in result_text:
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)
        skills = result.get("skills", [])

        # Deduplicate
        seen = set()
        unique_skills = []
        for skill in skills:
            name_lower = skill["name"].lower().strip()
            if name_lower not in seen and len(skill["name"]) > 1:
                seen.add(name_lower)
                skill["name"] = skill["name"].strip()
                unique_skills.append(skill)

        return unique_skills

    except Exception as e:
        print(f"  Extraction error: {e}")
        return []

def get_embedding(text: str) -> List[float]:
    """Generate SBERT embedding for a skill name."""
    return sbert_model.encode(text).tolist()

def get_or_create_skill(skill_name: str, skill_type: str, conn) -> int:
    """
    Get skill ID from DB or create it with embedding.
    Uses semantic similarity to avoid duplicates.
    ML = Machine Learning = تعلم الآلة → same skill ID
    """
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Generate embedding
    embedding = get_embedding(skill_name)
    embedding_str = str(embedding)

    # Search for semantically similar existing skills
    try:
        cursor.execute("""
            SELECT id, name,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM skills
            WHERE embedding IS NOT NULL
            AND 1 - (embedding <=> %s::vector) > 0.88
            ORDER BY similarity DESC
            LIMIT 1
        """, (embedding_str, embedding_str))

        similar = cursor.fetchone()
        if similar:
            cursor.close()
            return similar['id']

    except Exception as e:
        pass

    # Create new skill with embedding
    try:
        cursor.execute("""
            INSERT INTO skills (name, category, embedding)
            VALUES (%s, %s, %s::vector)
            ON CONFLICT (name) DO UPDATE
            SET category = EXCLUDED.category,
                embedding = EXCLUDED.embedding
            RETURNING id
        """, (skill_name, skill_type, embedding_str))

        skill_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        return skill_id

    except Exception as e:
        conn.rollback()
        cursor.close()

        # Try to get existing by name
        cursor2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor2.execute(
            "SELECT id FROM skills WHERE name = %s", (skill_name,)
        )
        existing = cursor2.fetchone()
        cursor2.close()
        return existing['id'] if existing else None

def process_job(job_id: int, job_title: str, job_description: str) -> int:
    """Extract and save skills from a job posting."""
    conn = get_connection()
    cursor = conn.cursor()

    text = f"Job Title: {job_title}\nDescription: {job_description}"
    skills = extract_skills_from_text(text)

    saved = 0
    for skill in skills:
        if skill.get('confidence', 0) >= 0.6:
            skill_id = get_or_create_skill(
                skill['name'], skill['type'], conn
            )
            if skill_id:
                cursor.execute("""
                    INSERT INTO job_skills
                    (job_id, skill_id, weight, is_required)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (job_id, skill_id, skill['confidence'], True))
                saved += 1
    conn.commit()

    cursor.close()
    conn.close()
    return saved

def process_course(course_id: int, course_code: str, course_title: str,
                   description: str, outcomes: str) -> int:
    """Extract and save skills from a course."""
    conn = get_connection()
    cursor = conn.cursor()

    text = f"""
    Course: {course_title}
    Description: {description}
    Learning Outcomes: {outcomes}
    """

    skills = extract_skills_from_text(text)

    saved = 0
    for skill in skills:
        if skill.get('confidence', 0) >= 0.5:
            skill_id = get_or_create_skill(
                skill['name'], skill['type'], conn
            )
            if skill_id:
                cursor.execute("""
                    INSERT INTO course_skills
                    (course_id, skill_id, confidence, extraction_method)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (course_id, skill_id, skill['confidence'], 'llm'))
                saved += 1
    conn.commit()

    cursor.close()
    conn.close()
    return saved