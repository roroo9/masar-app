from fastapi import APIRouter
import psycopg2.extras
import os
import json
import sys
import anthropic
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from db.database import get_connection

router = APIRouter(prefix="/api/skills", tags=["skills"])

@router.get("/")
def get_all_skills():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT id, name, category
        FROM skills
        ORDER BY name
    """)

    skills = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        "skills": [dict(s) for s in skills],
        "total": len(skills)
    }

@router.get("/top-demanded")
def get_top_demanded_skills():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 
            s.name,
            s.category,
            COUNT(DISTINCT js.job_id) as job_demand
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        GROUP BY s.id, s.name, s.category
        ORDER BY job_demand DESC
        LIMIT 20
    """)

    skills = cursor.fetchall()
    cursor.close()
    conn.close()

    return {"top_skills": [dict(s) for s in skills]}

@router.get("/university-gaps")
def get_university_gaps():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Skills in market
    cursor.execute("""
        SELECT s.name, COUNT(DISTINCT js.job_id) as demand
        FROM skills s
        JOIN job_skills js ON s.id = js.skill_id
        GROUP BY s.id, s.name
        ORDER BY demand DESC
        LIMIT 30
    """)
    market_skills = {row['name'].lower(): row['demand'] for row in cursor.fetchall()}

    # Skills taught in courses
    cursor.execute("""
        SELECT DISTINCT s.name
        FROM skills s
        JOIN course_skills cs ON s.id = cs.skill_id
    """)
    taught_skills = {row['name'].lower() for row in cursor.fetchall()}

    # Find gaps
    gaps = [
        {"skill": name, "job_demand": demand}
        for name, demand in market_skills.items()
        if name not in taught_skills
    ]

    cursor.close()
    conn.close()

    return {
        "total_market_skills": len(market_skills),
        "total_taught_skills": len(taught_skills),
        "gaps": gaps[:15],
        "alignment_score": round(
            len(taught_skills.intersection(market_skills.keys())) /
            max(len(market_skills), 1) * 100, 1
        )
    }


# ---------------------------------------------------------------------------
# Curated learning resources — top 30 skills
# YouTube/Coursera links are search URLs (always valid).
# Official doc links are known stable URLs.
# ---------------------------------------------------------------------------
_YT   = "YouTube"
_CS   = "Coursera"
_EDX  = "edX"
_FCC  = "freeCodeCamp"
_OFC  = "Official Docs"
_W3   = "W3Schools"
_KC   = "Kaggle"

def _yt(q: str) -> str:
    return f"https://www.youtube.com/results?search_query={q.replace(' ', '+')}"

def _cs(q: str) -> str:
    return f"https://www.coursera.org/search?query={q.replace(' ', '+')}"

def _edx(q: str) -> str:
    return f"https://www.edx.org/search?q={q.replace(' ', '+')}"

CURATED: dict[str, list[dict]] = {
    "Python": [
        {"title": "Python للمبتدئين — شرح عربي", "platform": _YT, "url": _yt("تعلم بايثون عربي"), "type": "video", "language": "ar", "free": True, "duration": "6 ساعات"},
        {"title": "Python for Everybody", "platform": _CS, "url": "https://www.coursera.org/specializations/python", "type": "course", "language": "en", "free": False, "duration": "8 أسابيع"},
        {"title": "Python Official Tutorial", "platform": _OFC, "url": "https://docs.python.org/3/tutorial/", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "SQL": [
        {"title": "SQL للمبتدئين — شرح عربي", "platform": _YT, "url": _yt("تعلم SQL عربي"), "type": "video", "language": "ar", "free": True, "duration": "4 ساعات"},
        {"title": "SQL Tutorial", "platform": _W3, "url": "https://www.w3schools.com/sql/", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Databases and SQL for Data Science", "platform": _CS, "url": "https://www.coursera.org/learn/sql-data-science", "type": "course", "language": "en", "free": False, "duration": "3 أسابيع"},
    ],
    "Machine Learning": [
        {"title": "Machine Learning — Andrew Ng", "platform": _CS, "url": "https://www.coursera.org/specializations/machine-learning-introduction", "type": "course", "language": "en", "free": False, "duration": "3 أشهر"},
        {"title": "تعلم الآلة بالعربي", "platform": _YT, "url": _yt("machine learning arabic"), "type": "video", "language": "ar", "free": True, "duration": "8 ساعات"},
        {"title": "Intro to ML — Kaggle", "platform": _KC, "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "type": "course", "language": "en", "free": True, "duration": "3 ساعات"},
    ],
    "Deep Learning": [
        {"title": "Deep Learning Specialization", "platform": _CS, "url": "https://www.coursera.org/specializations/deep-learning", "type": "course", "language": "en", "free": False, "duration": "4 أشهر"},
        {"title": "شرح Deep Learning بالعربي", "platform": _YT, "url": _yt("deep learning arabic"), "type": "video", "language": "ar", "free": True, "duration": "6 ساعات"},
        {"title": "Practical Deep Learning — fast.ai", "platform": _OFC, "url": "https://course.fast.ai/", "type": "course", "language": "en", "free": True, "duration": "7 أسابيع"},
    ],
    "TensorFlow": [
        {"title": "TensorFlow للمبتدئين", "platform": _YT, "url": _yt("TensorFlow tutorial arabic"), "type": "video", "language": "ar", "free": True, "duration": "4 ساعات"},
        {"title": "TensorFlow Developer Certificate", "platform": _CS, "url": _cs("TensorFlow developer"), "type": "course", "language": "en", "free": False, "duration": "4 أشهر"},
        {"title": "TensorFlow Official Tutorials", "platform": _OFC, "url": "https://www.tensorflow.org/tutorials", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "Scikit-learn": [
        {"title": "Scikit-learn بالعربي", "platform": _YT, "url": _yt("scikit-learn arabic tutorial"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "Scikit-learn User Guide", "platform": _OFC, "url": "https://scikit-learn.org/stable/user_guide.html", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "ML with Python", "platform": _CS, "url": _cs("machine learning python scikit"), "type": "course", "language": "en", "free": False, "duration": "5 أسابيع"},
    ],
    "Pandas": [
        {"title": "Pandas للمبتدئين", "platform": _YT, "url": _yt("pandas python arabic"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "Pandas — Kaggle", "platform": _KC, "url": "https://www.kaggle.com/learn/pandas", "type": "course", "language": "en", "free": True, "duration": "4 ساعات"},
        {"title": "Pandas Documentation", "platform": _OFC, "url": "https://pandas.pydata.org/docs/getting_started/", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "NLP": [
        {"title": "NLP بالعربي", "platform": _YT, "url": _yt("NLP natural language processing arabic"), "type": "video", "language": "ar", "free": True, "duration": "5 ساعات"},
        {"title": "NLP Specialization", "platform": _CS, "url": "https://www.coursera.org/specializations/natural-language-processing", "type": "course", "language": "en", "free": False, "duration": "4 أشهر"},
        {"title": "Hugging Face NLP Course", "platform": _OFC, "url": "https://huggingface.co/learn/nlp-course/", "type": "course", "language": "en", "free": True, "duration": "4 أسابيع"},
    ],
    "Statistics": [
        {"title": "إحصاء بالعربي", "platform": _YT, "url": _yt("احصاء statistics arabic"), "type": "video", "language": "ar", "free": True, "duration": "6 ساعات"},
        {"title": "Statistics with Python", "platform": _CS, "url": _cs("statistics python"), "type": "course", "language": "en", "free": False, "duration": "5 أسابيع"},
        {"title": "Khan Academy Statistics", "platform": _OFC, "url": "https://www.khanacademy.org/math/statistics-probability", "type": "course", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "JavaScript": [
        {"title": "JavaScript بالعربي من الصفر", "platform": _YT, "url": _yt("تعلم جافاسكريبت عربي"), "type": "video", "language": "ar", "free": True, "duration": "8 ساعات"},
        {"title": "JavaScript — freeCodeCamp", "platform": _FCC, "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "type": "course", "language": "en", "free": True, "duration": "300 ساعة"},
        {"title": "MDN JavaScript Guide", "platform": _OFC, "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "React": [
        {"title": "React بالعربي", "platform": _YT, "url": _yt("تعلم ريأكت عربي"), "type": "video", "language": "ar", "free": True, "duration": "6 ساعات"},
        {"title": "React Official Tutorial", "platform": _OFC, "url": "https://react.dev/learn", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Meta React Specialization", "platform": _CS, "url": _cs("Meta React"), "type": "course", "language": "en", "free": False, "duration": "5 أشهر"},
    ],
    "Node.js": [
        {"title": "Node.js بالعربي", "platform": _YT, "url": _yt("node.js arabic tutorial"), "type": "video", "language": "ar", "free": True, "duration": "5 ساعات"},
        {"title": "Node.js Docs", "platform": _OFC, "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Backend with Node.js", "platform": _CS, "url": _cs("node.js backend"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
    ],
    "Docker": [
        {"title": "Docker بالعربي", "platform": _YT, "url": _yt("docker arabic tutorial"), "type": "video", "language": "ar", "free": True, "duration": "4 ساعات"},
        {"title": "Docker Getting Started", "platform": _OFC, "url": "https://docs.docker.com/get-started/", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Docker & Kubernetes", "platform": _CS, "url": _cs("docker kubernetes"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
    ],
    "Git": [
        {"title": "Git بالعربي", "platform": _YT, "url": _yt("تعلم git عربي"), "type": "video", "language": "ar", "free": True, "duration": "2 ساعة"},
        {"title": "Pro Git Book", "platform": _OFC, "url": "https://git-scm.com/book/en/v2", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Git & GitHub — freeCodeCamp", "platform": _FCC, "url": "https://www.freecodecamp.org/news/gitting-things-done-book/", "type": "course", "language": "en", "free": True, "duration": "5 ساعات"},
    ],
    "Data Analysis": [
        {"title": "تحليل البيانات بالعربي", "platform": _YT, "url": _yt("data analysis arabic python"), "type": "video", "language": "ar", "free": True, "duration": "5 ساعات"},
        {"title": "Data Analysis with Python", "platform": _CS, "url": _cs("data analysis python"), "type": "course", "language": "en", "free": False, "duration": "5 أسابيع"},
        {"title": "Data Analysis — Kaggle", "platform": _KC, "url": "https://www.kaggle.com/learn/data-visualization", "type": "course", "language": "en", "free": True, "duration": "4 ساعات"},
    ],
    "Power BI": [
        {"title": "Power BI بالعربي", "platform": _YT, "url": _yt("power bi arabic tutorial"), "type": "video", "language": "ar", "free": True, "duration": "5 ساعات"},
        {"title": "Microsoft Power BI Docs", "platform": _OFC, "url": "https://learn.microsoft.com/en-us/power-bi/fundamentals/power-bi-overview", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "Power BI — edX", "platform": _EDX, "url": _edx("power bi"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
    ],
    "Communication": [
        {"title": "مهارات التواصل الفعّال", "platform": _YT, "url": _yt("مهارات التواصل عربي"), "type": "video", "language": "ar", "free": True, "duration": "2 ساعة"},
        {"title": "Improving Communication Skills", "platform": _CS, "url": "https://www.coursera.org/learn/wharton-communication-skills", "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
        {"title": "Business Communication", "platform": _EDX, "url": _edx("business communication"), "type": "course", "language": "en", "free": False, "duration": "3 أسابيع"},
    ],
    "Problem Solving": [
        {"title": "حل المشكلات وتنمية التفكير", "platform": _YT, "url": _yt("problem solving skills arabic"), "type": "video", "language": "ar", "free": True, "duration": "2 ساعة"},
        {"title": "Critical Thinking & Problem Solving", "platform": _CS, "url": _cs("critical thinking problem solving"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
        {"title": "LeetCode Practice", "platform": _OFC, "url": "https://leetcode.com/problemset/", "type": "practice", "language": "en", "free": True, "duration": "ذاتي"},
    ],
    "Cloud Computing": [
        {"title": "Cloud Computing بالعربي", "platform": _YT, "url": _yt("cloud computing arabic"), "type": "video", "language": "ar", "free": True, "duration": "4 ساعات"},
        {"title": "Google Cloud Fundamentals", "platform": _CS, "url": _cs("google cloud fundamentals"), "type": "course", "language": "en", "free": False, "duration": "3 أسابيع"},
        {"title": "AWS Cloud Practitioner", "platform": _OFC, "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/", "type": "course", "language": "en", "free": True, "duration": "6 ساعات"},
    ],
    "Cybersecurity": [
        {"title": "Cybersecurity بالعربي", "platform": _YT, "url": _yt("cybersecurity arabic"), "type": "video", "language": "ar", "free": True, "duration": "5 ساعات"},
        {"title": "Google Cybersecurity Certificate", "platform": _CS, "url": _cs("google cybersecurity"), "type": "course", "language": "en", "free": False, "duration": "6 أشهر"},
        {"title": "Cybersecurity Fundamentals — edX", "platform": _EDX, "url": _edx("cybersecurity fundamentals"), "type": "course", "language": "en", "free": False, "duration": "3 أسابيع"},
    ],
    "FastAPI": [
        {"title": "FastAPI بالعربي", "platform": _YT, "url": _yt("fastapi arabic tutorial"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "FastAPI Official Docs", "platform": _OFC, "url": "https://fastapi.tiangolo.com/tutorial/", "type": "docs", "language": "en", "free": True, "duration": "ذاتي"},
        {"title": "FastAPI Full Course", "platform": _YT, "url": _yt("fastapi full course"), "type": "video", "language": "en", "free": True, "duration": "4 ساعات"},
    ],
    "Project Management": [
        {"title": "إدارة المشاريع بالعربي", "platform": _YT, "url": _yt("project management arabic"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "Google Project Management Certificate", "platform": _CS, "url": _cs("google project management"), "type": "course", "language": "en", "free": False, "duration": "6 أشهر"},
        {"title": "Project Management Fundamentals — edX", "platform": _EDX, "url": _edx("project management fundamentals"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
    ],
    "Leadership": [
        {"title": "القيادة وتطوير الذات", "platform": _YT, "url": _yt("leadership skills arabic"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "Inspiring and Motivating Individuals", "platform": _CS, "url": _cs("leadership inspire motivate"), "type": "course", "language": "en", "free": False, "duration": "4 أسابيع"},
    ],
    "Data Visualization": [
        {"title": "تصوير البيانات بالعربي", "platform": _YT, "url": _yt("data visualization python arabic"), "type": "video", "language": "ar", "free": True, "duration": "3 ساعات"},
        {"title": "Data Visualization — Kaggle", "platform": _KC, "url": "https://www.kaggle.com/learn/data-visualization", "type": "course", "language": "en", "free": True, "duration": "4 ساعات"},
        {"title": "Data Visualization with Python", "platform": _CS, "url": _cs("data visualization python"), "type": "course", "language": "en", "free": False, "duration": "3 أسابيع"},
    ],
}

# Normalise keys for case-insensitive lookup
_CURATED_LOWER: dict[str, list[dict]] = {k.lower(): v for k, v in CURATED.items()}


def _claude_resources(skill: str) -> list[dict]:
    """Ask Claude to suggest 3 learning resources for a skill not in the curated list."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        prompt = f"""Suggest exactly 3 of the best online learning resources for the skill: "{skill}".
Return ONLY valid JSON — no markdown, no explanation:
{{
  "resources": [
    {{
      "title": "resource title",
      "platform": "platform name",
      "url": "https://...",
      "type": "video|course|docs|practice",
      "language": "ar|en",
      "free": true,
      "duration": "X ساعات or X أسابيع"
    }}
  ]
}}
Rules:
- Prefer one Arabic YouTube resource (search URL ok: https://www.youtube.com/results?search_query=...)
- Prefer one free resource
- Prefer well-known platforms: YouTube, Coursera, edX, freeCodeCamp, Kaggle, official docs
- Only use real, stable URLs you are certain exist"""
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text).get("resources", [])
    except Exception:
        return []


@router.get("/resources")
def get_skill_resources(skill: str):
    resources = _CURATED_LOWER.get(skill.lower())
    source = "curated"
    if not resources:
        resources = _claude_resources(skill)
        source = "ai"
    return {"skill": skill, "resources": resources or [], "source": source}