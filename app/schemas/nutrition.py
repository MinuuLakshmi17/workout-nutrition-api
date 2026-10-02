from datetime import date as DateType
from pydantic import BaseModel, Field, ConfigDict


class NutritionCreate(BaseModel):
    date: DateType
    calories: int = Field(ge=0, le=10000)
    protein_g: float = Field(ge=0, le=1000)
    carbs_g: float = Field(ge=0, le=2000)
    fat_g: float = Field(ge=0, le=1000)
    notes: str | None = None


class NutritionUpdate(BaseModel):
    date: DateType | None = None
    calories: int | None = Field(default=None, ge=0, le=10000)
    protein_g: float | None = Field(default=None, ge=0, le=1000)
    carbs_g: float | None = Field(default=None, ge=0, le=2000)
    fat_g: float | None = Field(default=None, ge=0, le=1000)
    notes: str | None = None


class NutritionResponse(NutritionCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class NutritionPage(BaseModel):
    items: list[NutritionResponse]
    total: int
    page: int
    page_size: int
