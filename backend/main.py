import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'))
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import student, jobs, skills, courses

app = FastAPI(
    title="Masar API",
    description="AI-powered career readiness platform for Saudi university students",
    version="1.0.0"
)

_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(student.router)
app.include_router(jobs.router)
app.include_router(skills.router)
app.include_router(courses.router)

@app.get("/")
def root():
    return {"message": "Masar API is running!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}