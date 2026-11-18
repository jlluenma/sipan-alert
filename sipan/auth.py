"""Autenticación y roles para la interfaz Streamlit."""
from __future__ import annotations

import base64
import hashlib
import secrets

import streamlit as st

from sipan.persistence.database import session_scope
from sipan.persistence.models import User
from sipan.persistence.repositories import UserRepository

SESSION_USER_KEY = "authenticated_user"
ROLE_USER = "usuario"
ROLE_REVIEWER = "revisor"
ROLE_ADMIN = "administrador"


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _password_matches(password: str, stored: str) -> bool:
    salt_value, digest_value = stored.split("$", 1)
    candidate = _hash_password(password, base64.b64decode(salt_value)).split("$", 1)[1]
    return secrets.compare_digest(candidate, digest_value)


def _public_user(user: User) -> dict:
    return {"id": str(user.id), "email": user.email, "name": user.display_name, "is_active": user.is_active, "roles": sorted(role.name for role in user.roles)}


class AuthService:
    def update_account(self, email: str, roles: list[str], active: bool, actor_id: str) -> None:
        if not roles or not set(roles).issubset({ROLE_USER, ROLE_REVIEWER, ROLE_ADMIN}):
            raise ValueError("Selecciona al menos un rol válido.")
        with session_scope() as session:
            repo = UserRepository(session)
            user = repo.find_by_email(email)
            if user is None:
                raise ValueError("La cuenta no existe.")
            if str(user.id) == actor_id and (not active or ROLE_ADMIN not in roles):
                raise ValueError("No puedes desactivar tu cuenta ni retirar tu propio rol administrador.")
            user.roles = [repo.role(name) for name in set(roles)]
            user.is_active = active

    def register(self, email: str, password: str, name: str | None = None) -> dict:
        address = email.strip().lower()
        if "@" not in address or len(address) > 254:
            raise ValueError("Ingresa un correo válido.")
        if len(password) < 10:
            raise ValueError("La contraseña debe tener al menos 10 caracteres.")
        with session_scope() as session:
            repo = UserRepository(session)
            if repo.find_by_email(address):
                raise ValueError("Ya existe una cuenta con ese correo.")
            role = repo.role(ROLE_USER)
            if role is None:
                raise RuntimeError("No se encontraron los roles iniciales. Ejecuta las migraciones.")
            return _public_user(repo.save(User(email=address, display_name=name.strip()[:80] if name else None, password_hash=_hash_password(password), roles=[role])))

    def authenticate(self, email: str, password: str) -> dict | None:
        with session_scope() as session:
            user = UserRepository(session).find_by_email(email.strip().lower())
            if user is None or not user.is_active or not _password_matches(password, user.password_hash):
                return None
            return _public_user(user)

    def grant_role(self, email: str, role_name: str) -> None:
        with session_scope() as session:
            repo = UserRepository(session)
            user, role = repo.find_by_email(email.strip().lower()), repo.role(role_name)
            if user is None or role is None:
                raise ValueError("No se encontró el usuario o el rol.")
            if role not in user.roles:
                user.roles.append(role)

    def users(self) -> list[dict]:
        with session_scope() as session:
            return [_public_user(user) for user in UserRepository(session).find_all()]


def current_user() -> dict | None:
    return st.session_state.get(SESSION_USER_KEY)


def sign_in(user: dict) -> None:
    st.session_state[SESSION_USER_KEY] = user


def sign_out() -> None:
    st.session_state.pop(SESSION_USER_KEY, None)


def require_role(*roles: str) -> dict:
    user = current_user()
    if user is None or not set(user["roles"]).intersection(roles):
        raise PermissionError("Inicia sesión con una cuenta autorizada para acceder a este panel.")
    return user
