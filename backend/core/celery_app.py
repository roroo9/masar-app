from celery import Celery
import os

# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Create Celery app
celery_app = Celery(
    "masar",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["core.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Riyadh",
    enable_utc=True,
    task_track_started=True,
)