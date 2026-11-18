"""Autenticación básica para SipánAlert (US-AUTH, Sprint 2).

Alcance acordado: prototipo académico, sin recuperación de contraseña, sin 2FA,
sin registro público. Los usuarios se crean con scripts/add_user.py.

Reglas no negociables:
- Las contraseñas se almacenan solo como hash bcrypt, nunca en texto plano.
- Este módulo no emite logs ni devuelve la contraseña en claro en excepciones.
- El archivo data/users.db está en .gitignore.
"""

from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import bcrypt

from sipan import config


class AuthError(Exception):
    """Falla de autenticación. Mensaje apto para mostrar al usuario."""


@dataclass(frozen=True)
class AuthUser:
    username: str


DB_PATH = config.DATA_DIR / "users.db"


def _schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
        )"""
    )


@contextmanager
def _connect(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    db = path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    try:
        _schema(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise AuthError("La contraseña no puede estar vacía.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def upsert_user(username: str, password: str, *, path: Path | None = None) -> None:
    """Crea o reemplaza el hash de un usuario. Levanta AuthError si el nombre es inválido."""
    username = (username or "").strip()
    if not username:
        raise AuthError("El nombre de usuario no puede estar vacío.")
    if len(username) > 60 or any(c.isspace() for c in username):
        raise AuthError("El nombre de usuario debe tener hasta 60 caracteres sin espacios.")
    password_hash = hash_password(password)
    with _connect(path) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)"
            " ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash",
            (username, password_hash),
        )


def authenticate(username: str, password: str, *, path: Path | None = None) -> AuthUser | None:
    """Devuelve AuthUser si coincide, None en cualquier otro caso.

    Nunca lanza excepción con información sensible y nunca filtra si el usuario existe.
    Aplica una pausa de 0,3 s como mitigación básica de bruteforce.
    """
    time.sleep(0.3)
    username = (username or "").strip()
    if not username or not password:
        return None
    with _connect(path) as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return None
    return AuthUser(username=username) if verify_password(password, row[0]) else None


def list_usernames(*, path: Path | None = None) -> list[str]:
    """Nombres registrados, en orden alfabético. Útil para diagnóstico, nunca devuelve hashes."""
    with _connect(path) as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
    return [r[0] for r in rows]
