from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

try:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
except ModuleNotFoundError:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
