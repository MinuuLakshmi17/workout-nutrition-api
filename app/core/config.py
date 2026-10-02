from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Workout & Nutrition API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/workout_api"
    )
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    rate_limit_per_minute: int = 60
    cors_origins: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
