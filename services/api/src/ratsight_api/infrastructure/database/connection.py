from __future__ import annotations

from collections.abc import Iterator

from ratsight_api.infrastructure.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

engine: Engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a short-lived database session."""
    with SessionLocal() as session:
        yield session


def postgis_status() -> tuple[bool, str | None]:
    """Return availability without exposing connection errors to API clients."""
    try:
        with engine.connect() as connection:
            version = connection.execute(text("SELECT PostGIS_Version()")).scalar_one()
        return True, str(version)
    except SQLAlchemyError:
        return False, None
