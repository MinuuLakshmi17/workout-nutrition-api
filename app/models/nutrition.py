from datetime import date, datetime, timezone
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class NutritionEntry(Base):
    __tablename__ = "nutrition_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    calories: Mapped[int] = mapped_column(Integer)
    protein_g: Mapped[float] = mapped_column(Float)
    carbs_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    user = relationship("User", back_populates="nutrition_entries")
    __table_args__ = (Index("ix_nutrition_user_date", "user_id", "date"),)
