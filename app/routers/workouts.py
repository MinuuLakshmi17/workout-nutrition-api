from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.deps import current_user_id, db_session
from app.models.workout import Workout
from app.schemas.workout import *
from app.services.cache import StatsCache

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutResponse, status_code=201)
def create(
    p: WorkoutCreate, uid=Depends(current_user_id), db: Session = Depends(db_session)
):
    w = Workout(user_id=uid, **p.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    StatsCache().invalidate(uid)
    return w


@router.get("", response_model=WorkoutPage)
def listing(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    exercise: str | None = Query(None, min_length=1, max_length=120),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    uid=Depends(current_user_id),
    db: Session = Depends(db_session),
):
    q = select(Workout).where(Workout.user_id == uid)
    if exercise:
        q = q.where(Workout.exercise.ilike(f"%{exercise}%"))
    if date_from:
        q = q.where(Workout.performed_at >= date_from)
    if date_to:
        q = q.where(Workout.performed_at < date_to + timedelta(days=1))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(
        q.order_by(Workout.performed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return WorkoutPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=WorkoutStats)
def stats(uid=Depends(current_user_id), db: Session = Depends(db_session)):
    c = StatsCache()
    hit = c.get(uid)
    if hit:
        return WorkoutStats(**hit, cache_hit=True)
    n = db.scalar(select(func.count(Workout.id)).where(Workout.user_id == uid)) or 0
    v = (
        db.scalar(
            select(
                func.coalesce(
                    func.sum(Workout.sets * Workout.reps * Workout.weight_kg), 0.0
                )
            ).where(Workout.user_id == uid)
        )
        or 0.0
    )
    data = {"total_workouts": int(n), "total_volume_kg": float(v)}
    c.set(uid, data)
    return WorkoutStats(**data, cache_hit=False)


@router.get("/{wid}", response_model=WorkoutResponse)
def get(wid: int, uid=Depends(current_user_id), db: Session = Depends(db_session)):
    w = db.scalar(select(Workout).where(Workout.id == wid, Workout.user_id == uid))
    if not w:
        raise HTTPException(404, "Workout not found")
    return w


@router.patch("/{wid}", response_model=WorkoutResponse)
def update(
    wid: int,
    p: WorkoutUpdate,
    uid=Depends(current_user_id),
    db: Session = Depends(db_session),
):
    w = db.scalar(select(Workout).where(Workout.id == wid, Workout.user_id == uid))
    if not w:
        raise HTTPException(404, "Workout not found")
    for k, v in p.model_dump(exclude_unset=True).items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    StatsCache().invalidate(uid)
    return w


@router.delete("/{wid}", status_code=204)
def delete(wid: int, uid=Depends(current_user_id), db: Session = Depends(db_session)):
    w = db.scalar(select(Workout).where(Workout.id == wid, Workout.user_id == uid))
    if not w:
        raise HTTPException(404, "Workout not found")
    db.delete(w)
    db.commit()
    StatsCache().invalidate(uid)
