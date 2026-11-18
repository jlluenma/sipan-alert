"""Pruebas del módulo de autenticación (US-AUTH).

Usan un SQLite temporal por test para no tocar data/users.db.
"""

from __future__ import annotations

import sqlite3

import pytest

from sipan.auth import (
    AuthError,
    AuthUser,
    authenticate,
    hash_password,
    list_usernames,
    upsert_user,
    verify_password,
)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "users.db"


def test_hash_and_verify_password_roundtrip():
    hashed = hash_password("clave-secreta-123")
    assert hashed != "clave-secreta-123"
    assert verify_password("clave-secreta-123", hashed)


def test_verify_password_wrong():
    hashed = hash_password("clave-secreta-123")
    assert not verify_password("otra-cosa", hashed)


def test_verify_password_handles_invalid_hash():
    assert not verify_password("cualquier", "no-es-un-hash-bcrypt")


def test_hash_password_rejects_empty():
    with pytest.raises(AuthError):
        hash_password("")


def test_upsert_rejects_empty_username(db):
    with pytest.raises(AuthError):
        upsert_user("", "clave", path=db)
    with pytest.raises(AuthError):
        upsert_user("   ", "clave", path=db)


def test_upsert_rejects_username_with_spaces(db):
    with pytest.raises(AuthError):
        upsert_user("usuario con espacio", "clave", path=db)


def test_authenticate_success(db):
    upsert_user("usr1", "clave-abc", path=db)
    user = authenticate("usr1", "clave-abc", path=db)
    assert user == AuthUser(username="usr1")


def test_authenticate_wrong_password(db):
    upsert_user("usr1", "clave-abc", path=db)
    assert authenticate("usr1", "otra-clave", path=db) is None


def test_authenticate_unknown_user(db):
    upsert_user("usr1", "clave-abc", path=db)
    assert authenticate("usr2", "clave-abc", path=db) is None


def test_authenticate_rejects_empty_input(db):
    upsert_user("usr1", "clave-abc", path=db)
    assert authenticate("", "clave-abc", path=db) is None
    assert authenticate("usr1", "", path=db) is None


def test_upsert_replaces_existing_hash(db):
    upsert_user("usr1", "clave-vieja", path=db)
    upsert_user("usr1", "clave-nueva", path=db)
    assert authenticate("usr1", "clave-vieja", path=db) is None
    assert authenticate("usr1", "clave-nueva", path=db) is not None


def test_password_is_never_stored_in_plain_text(db):
    plain = "contraseña-muy-identificable-xyz"
    upsert_user("usr1", plain, path=db)
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT username, password_hash FROM users").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    username, stored = rows[0]
    assert username == "usr1"
    assert plain not in stored
    assert stored.startswith("$2b$") or stored.startswith("$2a$")


def test_list_usernames_sorted(db):
    for name in ("usr3", "usr1", "usr2"):
        upsert_user(name, "clave", path=db)
    assert list_usernames(path=db) == ["usr1", "usr2", "usr3"]


def test_authenticate_strips_whitespace_in_username(db):
    upsert_user("usr1", "clave", path=db)
    assert authenticate("  usr1  ", "clave", path=db) is not None
