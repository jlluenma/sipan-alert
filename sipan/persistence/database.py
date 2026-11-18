"""Motores y sesiones SQLAlchemy. Cada operación abre su propia sesión."""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from sipan import config
from sipan.database import DatabaseNotConfiguredError, get_engine


class Base(DeclarativeBase):
    pass


DatabaseNotConfigured = DatabaseNotConfiguredError


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    if not config.DATABASE_URL:
        raise DatabaseNotConfigured("Configura DATABASE_URL para usar PostgreSQL.")
    return sessionmaker(get_engine(), expire_on_commit=False)


@contextmanager
def session_scope():
    session = get_session_factory()()
    try:
        with session.begin():
            yield session
    finally:
        session.close()
