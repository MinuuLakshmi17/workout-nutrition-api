import json

from redis import Redis

from app.core.config import settings


class StatsCache:
    """Redis-backed cache for per-user workout statistics."""

    def __init__(self, redis_url: str | None = None):
        self.redis = Redis.from_url(
            redis_url or settings.redis_url, decode_responses=True
        )
        self.ttl = 120

    def get(self, user_id: int):
        raw = self.redis.get(f"workout_stats:{user_id}")
        return json.loads(raw) if raw else None

    def set(self, user_id: int, value: dict):
        self.redis.setex(f"workout_stats:{user_id}", self.ttl, json.dumps(value))

    def invalidate(self, user_id: int):
        self.redis.delete(f"workout_stats:{user_id}")
