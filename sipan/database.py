"""Punto único de conexión PostgreSQL para SipánAlert."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from sipan import config


class DatabaseNotConfiguredError(RuntimeError):
    """No existe una URL de base de datos configurada."""


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Devuelve el motor SQLAlchemy configurado mediante DATABASE_URL."""
    if not config.DATABASE_URL:
        raise DatabaseNotConfiguredError("Configura DATABASE_URL para usar PostgreSQL.")
    return create_engine(config.DATABASE_URL, pool_pre_ping=True)


def test_connection() -> tuple[bool, str]:
    """Comprueba la conexión sin crear ni modificar datos."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Conexión a PostgreSQL establecida."
    except DatabaseNotConfiguredError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"No se pudo conectar a PostgreSQL: {exc}"
