from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class WorkoutCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    exercise: str = Field(min_length=1, max_length=120)
    sets: int = Field(ge=1, le=100)
    reps: int = Field(ge=1, le=1000)
    weight_kg: float = Field(ge=0, le=1000)
    performed_at: datetime


class WorkoutUpdate(BaseModel):
    name: str | None = None
    exercise: str | None = None
    sets: int | None = Field(default=None, ge=1, le=100)
    reps: int | None = Field(default=None, ge=1, le=1000)
    weight_kg: float | None = Field(default=None, ge=0, le=1000)
    performed_at: datetime | None = None


class WorkoutResponse(WorkoutCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class WorkoutPage(BaseModel):
    items: list[WorkoutResponse]
    total: int
    page: int
    page_size: int


class WorkoutStats(BaseModel):
    total_workouts: int
    total_volume_kg: float
    cache_hit: bool
