from __future__ import annotations

from ratsight_api.infrastructure.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

engine: Engine = create_engine(get_settings().database_url, pool_pre_ping=True)


def postgis_status() -> tuple[bool, str | None]:
    """Return availability without exposing connection errors to API clients."""
    try:
        with engine.connect() as connection:
            version = connection.execute(text("SELECT PostGIS_Version()")).scalar_one()
        return True, str(version)
    except SQLAlchemyError:
        return False, None
