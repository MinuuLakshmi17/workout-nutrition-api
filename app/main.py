from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis

from app.core.config import settings
from app.core.logging import configure_logging, logger, request_id_ctx
from app.routers import auth, nutrition, summaries, workouts

configure_logging()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level client: redis-py connects lazily, so this is safe at import time
# and avoids opening a new connection on every request.
_redis = Redis.from_url(settings.redis_url, decode_responses=True)
_RATE_LIMIT_EXEMPT = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid4().hex[:16])
    request_id_ctx.set(rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


@app.middleware("http")
async def limit(request: Request, call_next):
    if request.url.path in _RATE_LIMIT_EXEMPT:
        return await call_next(request)
    try:
        key = f"rate:{request.client.host if request.client else 'unknown'}"
        n = _redis.incr(key)
        if n == 1:
            _redis.expire(key, 60)
        if n > settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429, content={"detail": "Rate limit exceeded"}
            )
    except Exception:
        pass  # fail open: never take the API down because Redis is unreachable
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "healthy", "service": settings.app_name}


@app.get("/ready")
def ready():
    checks = {}
    try:
        from sqlalchemy import text

        from app.db.session import engine

        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        _redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "degraded", "checks": checks},
    )


app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(nutrition.router)
app.include_router(summaries.router)
