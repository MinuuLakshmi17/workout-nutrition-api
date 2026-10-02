from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery("workout_api", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Every Monday at 00:00 UTC, queue a summary for every user.
        "weekly-summaries": {
            "task": "weekly_summary_all_users",
            "schedule": crontab(hour=0, minute=0, day_of_week="monday"),
        },
    },
)
