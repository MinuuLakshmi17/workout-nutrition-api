from celery import group
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.services.summary import build_weekly_summary
from app.tasks.celery_app import celery


def _serialize(summary):
    return {
        "id": summary.id,
        "week_start": summary.week_start.isoformat(),
        "workout_count": summary.workout_count,
        "total_volume_kg": summary.total_volume_kg,
        "avg_calories": summary.avg_calories,
        "avg_protein_g": summary.avg_protein_g,
    }


@celery.task(
    name="weekly_summary",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def weekly_summary(self, user_id):
    """Build (or rebuild) one user's weekly summary.

    Idempotent: build_weekly_summary upserts on (user_id, week_start), so a
    retried or duplicated task never creates a second row.
    """
    db = SessionLocal()
    try:
        return _serialize(build_weekly_summary(db, user_id))
    finally:
        db.close()


@celery.task(name="weekly_summary_all_users")
def weekly_summary_all_users():
    """Fan out one summary task per user. Triggered by celery beat weekly."""
    db = SessionLocal()
    try:
        user_ids = db.scalars(select(User.id)).all()
    finally:
        db.close()
    group(weekly_summary.s(uid) for uid in user_ids).apply_async()
    return {"queued": len(user_ids)}
