import os

os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-bytes-minimum-1234"

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import db_session
from app.db.base import Base
from app.main import app


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_session] = override
    # Real Redis behavior against a fake server (no network needed). Patched on
    # the class so every module (cache, refresh store) shares the same fake.
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr("redis.Redis.from_url", lambda *a, **k: fake)
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def auth_headers(client):
    assert (
        client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "StrongPass123!"},
        ).status_code
        == 201
    )
    t = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "StrongPass123!"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {t}"}
