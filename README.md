# Masar — Career Readiness Platform

Monorepo for the Masar app: FastAPI backend + Next.js frontend, wired together.

```
claude-playground/
├── backend/           FastAPI app (Python)
├── masar-app/         Next.js frontend
├── data/              Source data (courses, jobs, processed)
├── docker-compose.yml Postgres (pgvector) + Redis
└── .env               Shared secrets (ANTHROPIC_API_KEY, DB creds)
```

## Run it

1. Start Postgres + Redis:

   ```sh
   docker compose up -d
   ```

   On first start, `backend/database/schema.sql` is auto-loaded into the `masar` DB.

2. Start the backend (port 8000):

   ```sh
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

3. Start the frontend (port 3000):

   ```sh
   cd masar-app
   npm install
   npm run dev
   ```

The frontend reads `NEXT_PUBLIC_API_URL` from `masar-app/.env.local` (already set to `http://localhost:8000`).

## API contract

Endpoints used by `masar-app/src/lib/api.ts`:

- `GET /api/students/{id}/dashboard`
- `GET /api/students/{id}/skills`
- `GET /api/students/{id}/readiness/{job_id}`
- `GET /api/skills/top-demanded`
- `GET /api/jobs/`
