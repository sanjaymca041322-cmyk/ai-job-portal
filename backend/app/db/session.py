from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine: Engine | None = (
    create_engine(settings.database_url, pool_pre_ping=True)
    if settings.database_url
    else None
)

SessionLocal: sessionmaker[Session] | None = (
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
    if engine
    else None
)


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL must be configured before using the database")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()