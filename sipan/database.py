"""Punto único de conexión a base de datos para SipánAlert IA.

La base de datos todavía no está definida. Cuando el equipo la elija,
se configurará DATABASE_URL y se instalará el controlador correspondiente.
Este módulo no crea tablas ni abre conexiones al importar la aplicación.
"""

import os
from functools import lru_cache
from typing import Any


class DatabaseNotConfiguredError(RuntimeError):
    """Se intenta usar la base de datos antes de configurarla."""


@lru_cache(maxsize=1)
def get_engine() -> Any:
    """Devuelve el motor SQLAlchemy configurado mediante DATABASE_URL.

    Ejemplos de URL (solo como referencia; aún no se ha elegido un motor):
      PostgreSQL: postgresql+psycopg://usuario:clave@host:5432/base
      MySQL:      mysql+pymysql://usuario:clave@host:3306/base
      SQLite:     sqlite:///./sipan_alert.db

    Instala SQLAlchemy y el driver del motor elegido cuando corresponda.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseNotConfiguredError(
            "La base de datos aún no está configurada. "
            "Define DATABASE_URL cuando se decida qué motor utilizar."
        )

    try:
        from sqlalchemy import create_engine
    except ImportError as exc:
        raise RuntimeError(
            "Falta SQLAlchemy. Instálalo cuando se defina la base de datos."
        ) from exc

    return create_engine(database_url, pool_pre_ping=True)


def test_connection() -> tuple[bool, str]:
    """Comprueba la conexión sin ejecutarse automáticamente al iniciar."""
    try:
        from sqlalchemy import text

        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Conexión a la base de datos establecida."
    except DatabaseNotConfiguredError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"No se pudo conectar a la base de datos: {exc}"
