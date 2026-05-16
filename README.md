# Masar — AI Career Readiness Platform

Masar (مسار) helps Saudi university students discover how ready they are for their dream jobs, identifies skill gaps, and generates a personalized AI-powered learning plan to close them.

**Live demo:** [masar-app-pi.vercel.app](https://masar-app-pi.vercel.app)

---

## Features

- **Readiness scoring** — semantic skill-gap analysis comparing a student's coursework against real job requirements using sentence embeddings + TF-IDF weighting
- **AI learning plans** — Claude generates a personalized study plan with specific resources, time estimates, and motivational guidance
- **Job matching** — browse Saudi tech jobs and see your fit score for each one instantly
- **Course tracking** — log university courses; skills are extracted automatically
- **Project recommendations** — get project ideas matched to your missing skills and year of study
- **Dashboard** — visual overview of top skills, matched jobs, and progress over time

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router, TypeScript) |
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 + pgvector |
| AI / NLP | Anthropic Claude (`claude-sonnet-4-6`) + Sentence Transformers |
| Task queue | Celery + Redis |
| Auth | JWT (python-jose + bcrypt) |
| Frontend hosting | Vercel |
| Backend hosting | Railway |

---

## Project Structure

```
masar/
├── backend/                  FastAPI application
│   ├── api/routes/           REST endpoints (auth, jobs, courses, skills, student)
│   ├── core/                 Business logic
│   │   ├── gap_analyzer.py   Semantic skill-gap scoring engine
│   │   ├── readiness_scorer.py  AI explanation generator (Claude)
│   │   ├── recommender.py    Project recommendation engine
│   │   ├── skill_extractor.py   LLM skill extraction from job/course text
│   │   └── tasks.py          Celery async tasks
│   ├── db/                   Connection pool & models
│   ├── database/schema.sql   Full DB schema
│   ├── scripts/              Seed data & utilities
│   ├── tests/                Pytest test suite (46 tests)
│   ├── Dockerfile
│   └── requirements.txt
├── masar-app/                Next.js frontend
│   └── src/app/
│       ├── dashboard/        Student overview page
│       ├── plan/             AI-powered learning plan
│       ├── skills/           Skills breakdown
│       ├── courses/          Course catalog & enrollment
│       ├── recommended/      Project recommendations
│       └── login/ onboarding/  Auth flow
├── data/                     Source data (jobs, courses)
├── docker-compose.yml        Local Postgres + Redis
└── .env.example              Environment variable template
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### 1. Clone & configure environment

```bash
git clone https://github.com/roroo9/masar-app.git
cd masar-app
cp .env.example .env
```

Open `.env` and fill in your values:

```env
ANTHROPIC_API_KEY=sk-ant-...          # get from console.anthropic.com
DATABASE_URL=postgresql://masar_user:masar_pass@localhost:5432/masar
JWT_SECRET_KEY=<run: openssl rand -hex 32>
ALLOWED_ORIGINS=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Start the database

```bash
docker compose up -d
```

This starts PostgreSQL (with pgvector) and Redis. The schema at `backend/database/schema.sql` is loaded automatically on first start.

### 3. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start the frontend

```bash
cd masar-app
npm install

# Create a local env file for the frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 5. (Optional) Seed demo data

```bash
cd backend
python scripts/seed_demo_data.py
python scripts/seed_skills.py
```

---

## Running Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

All 46 tests run without a database or API key — external dependencies are mocked.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new student |
| `POST` | `/api/auth/login` | Login and receive JWT |
| `GET` | `/api/students/{id}/dashboard` | Student overview & top scores |
| `GET` | `/api/students/{id}/skills` | Student's confirmed skills |
| `GET` | `/api/students/{id}/readiness/{job_id}` | Readiness score for a job |
| `GET` | `/api/students/{id}/plan/{job_id}` | AI learning plan for a job |
| `GET` | `/api/jobs/` | List all jobs |
| `GET` | `/api/courses/` | List all courses |
| `GET` | `/api/skills/top-demanded` | Most in-demand skills |
| `POST` | `/api/students/{id}/courses` | Enroll in courses |

Full interactive docs: [masar-backend-production-3ff4.up.railway.app/docs](https://masar-backend-production-3ff4.up.railway.app/docs)

---

## Deployment

### Backend → Railway

1. Create a Railway project and add a PostgreSQL plugin
2. Link your repo and set environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`
   - `JWT_SECRET_KEY`
   - `ALLOWED_ORIGINS` (your Vercel URL)
   - Railway injects `DATABASE_URL` automatically
3. Railway builds and deploys from `backend/Dockerfile`

### Frontend → Vercel

1. Import the repo into Vercel and set the root directory to `masar-app`
2. Add environment variable:
   - `NEXT_PUBLIC_API_URL` → your Railway backend URL
3. Deploy

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | Claude API key from [console.anthropic.com](https://console.anthropic.com) |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `JWT_SECRET_KEY` | ✅ | Random secret for signing tokens (`openssl rand -hex 32`) |
| `ALLOWED_ORIGINS` | ✅ | Comma-separated CORS origins |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (frontend only) |

---

## License

MIT
