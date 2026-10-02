from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.deps import current_user_id, db_session
from app.models.summary import WeeklySummary
from app.schemas.summary import WeeklySummaryResponse
from app.services.summary import build_weekly_summary
from app.tasks.summary import weekly_summary

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.post("/weekly")
def queue(uid=Depends(current_user_id)):
    return {"task_id": weekly_summary.delay(uid).id, "status": "queued"}


@router.get("/weekly/latest", response_model=WeeklySummaryResponse)
def latest(uid=Depends(current_user_id), db: Session = Depends(db_session)):
    x = db.scalar(
        select(WeeklySummary)
        .where(WeeklySummary.user_id == uid)
        .order_by(WeeklySummary.week_start.desc())
    )
    return x or build_weekly_summary(db, uid)
