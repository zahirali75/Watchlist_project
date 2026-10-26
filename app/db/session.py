"""Direct PostgreSQL connectivity using SQLAlchemy Core.

The active FastAPI application accesses PostgreSQL directly; no Supabase SDK or
PostgREST API is used by this module. Set DATABASE_URL to a PostgreSQL DSN,
for example postgresql+psycopg://user:password@localhost:5432/cinelist.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )


def dispose_engine() -> None:
    """Tutup pool koneksi saat server dimatikan (aman bila belum pernah dibuat)."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()


@contextmanager
def get_connection(*, write: bool = False) -> Iterator[Connection]:
    """Yield a short-lived connection; commit writes and roll back on errors."""
    engine = get_engine()
    context = engine.begin() if write else engine.connect()
    with context as connection:
        yield connection
