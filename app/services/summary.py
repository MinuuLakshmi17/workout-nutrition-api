from datetime import date, timedelta
from sqlalchemy import func, select
from app.models.workout import Workout
from app.models.nutrition import NutritionEntry
from app.models.summary import WeeklySummary


def week_start(day):
    return day - timedelta(days=day.weekday())


def build_weekly_summary(db, user_id, start=None):
    start = start or week_start(date.today())
    end = start + timedelta(days=7)
    wc = (
        db.scalar(
            select(func.count(Workout.id)).where(
                Workout.user_id == user_id,
                Workout.performed_at >= start,
                Workout.performed_at < end,
            )
        )
        or 0
    )
    vol = (
        db.scalar(
            select(
                func.coalesce(
                    func.sum(Workout.sets * Workout.reps * Workout.weight_kg), 0.0
                )
            ).where(
                Workout.user_id == user_id,
                Workout.performed_at >= start,
                Workout.performed_at < end,
            )
        )
        or 0
    )
    cal = (
        db.scalar(
            select(func.coalesce(func.avg(NutritionEntry.calories), 0.0)).where(
                NutritionEntry.user_id == user_id,
                NutritionEntry.date >= start,
                NutritionEntry.date < end,
            )
        )
        or 0
    )
    prot = (
        db.scalar(
            select(func.coalesce(func.avg(NutritionEntry.protein_g), 0.0)).where(
                NutritionEntry.user_id == user_id,
                NutritionEntry.date >= start,
                NutritionEntry.date < end,
            )
        )
        or 0
    )
    item = db.scalar(
        select(WeeklySummary).where(
            WeeklySummary.user_id == user_id, WeeklySummary.week_start == start
        )
    )
    if not item:
        item = WeeklySummary(
            user_id=user_id,
            week_start=start,
            workout_count=wc,
            total_volume_kg=float(vol),
            avg_calories=float(cal),
            avg_protein_g=float(prot),
        )
        db.add(item)
    else:
        item.workout_count = wc
        item.total_volume_kg = float(vol)
        item.avg_calories = float(cal)
        item.avg_protein_g = float(prot)
    db.commit()
    db.refresh(item)
    return item
