from datetime import date, datetime, timezone
from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    week_start: Mapped[date] = mapped_column(Date)
    workout_count: Mapped[int] = mapped_column(Integer)
    total_volume_kg: Mapped[float] = mapped_column(Float)
    avg_calories: Mapped[float] = mapped_column(Float)
    avg_protein_g: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_summary_user_week"),
        Index("ix_summary_user_week", "user_id", "week_start"),
    )
