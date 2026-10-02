from redis import Redis

from app.core.config import settings


class RefreshTokenStore:
    """Server-side allowlist for refresh-token JTIs, backed by Redis.

    A refresh token is only honored when its JTI is present here. Rotation
    deletes the old JTI and logout deletes it, so stolen or logged-out
    tokens stop working immediately instead of living out their 7-day TTL.
    """

    def __init__(self, redis_url: str | None = None):
        self.redis = Redis.from_url(
            redis_url or settings.redis_url, decode_responses=True
        )
        self.ttl = settings.refresh_token_expire_days * 24 * 3600

    def _key(self, jti: str) -> str:
        return f"refresh:{jti}"

    def store(self, jti: str, user_id: int) -> None:
        self.redis.setex(self._key(jti), self.ttl, str(user_id))

    def is_valid(self, jti: str, user_id: int) -> bool:
        return self.redis.get(self._key(jti)) == str(user_id)

    def revoke(self, jti: str) -> None:
        self.redis.delete(self._key(jti))
