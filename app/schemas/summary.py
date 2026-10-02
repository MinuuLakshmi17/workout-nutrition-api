from datetime import date
from pydantic import BaseModel


class WeeklySummaryResponse(BaseModel):
    id: int
    week_start: date
    workout_count: int
    total_volume_kg: float
    avg_calories: float
    avg_protein_g: float
