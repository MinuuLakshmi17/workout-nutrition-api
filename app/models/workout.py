from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Workout(Base):
    __tablename__ = "workouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    exercise: Mapped[str] = mapped_column(String(120))
    sets: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float] = mapped_column(Float)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user = relationship("User", back_populates="workouts")
    __table_args__ = (Index("ix_workouts_user_performed", "user_id", "performed_at"),)
