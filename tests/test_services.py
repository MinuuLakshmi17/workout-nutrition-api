from datetime import datetime, timezone, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.models.user import User
from app.models.workout import Workout
from app.models.nutrition import NutritionEntry
from app.services.summary import build_weekly_summary
from app.services.cache import StatsCache
from app.core.security import hash_password, verify_password


def test_password_is_hashed():
    raw = "StrongPass123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong", hashed)


def test_weekly_summary_calculation():
    e = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(e)
    S = sessionmaker(bind=e, expire_on_commit=False)
    db = S()
    u = User(email="summary@example.com", password_hash="x")
    db.add(u)
    db.commit()
    db.refresh(u)
    db.add(
        Workout(
            user_id=u.id,
            name="Push",
            exercise="Bench",
            sets=3,
            reps=10,
            weight_kg=50,
            performed_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
    )
    db.add(
        NutritionEntry(
            user_id=u.id,
            date=date(2026, 10, 1),
            calories=2200,
            protein_g=160,
            carbs_g=200,
            fat_g=70,
        )
    )
    db.commit()
    s = build_weekly_summary(db, u.id, date(2026, 9, 28))
    assert (
        s.workout_count == 1
        and s.total_volume_kg == 1500
        and s.avg_calories == 2200
        and s.avg_protein_g == 160
    )


def test_cache_round_trip(monkeypatch):
    import fakeredis

    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr("redis.Redis.from_url", lambda *a, **k: fake)
    c = StatsCache()
    c.invalidate(42)
    assert c.get(42) is None
    c.set(42, {"total_workouts": 3, "total_volume_kg": 123.0})
    assert c.get(42)["total_workouts"] == 3
    c.invalidate(42)
    assert c.get(42) is None
