"""Crea o actualiza usuarios en data/users.db.

Las contraseñas NUNCA viajan por argumentos de línea de comandos ni por variables
de entorno: se piden interactivamente con getpass para que no queden en el
historial del shell ni en logs.

Ejemplos:
    # Crear 7 usuarios con la misma contraseña (la pide una sola vez):
    python scripts/add_user.py --users usr1,usr2,usr3,usr4,usr5,usr6,usr7 --same-password

    # Crear usuarios con contraseñas distintas (la pide una por una):
    python scripts/add_user.py --users usr1,usr2
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sipan.auth import AuthError, list_usernames, upsert_user  # noqa: E402


def _ask_password(prompt: str = "Contraseña: ") -> str | None:
    pw = getpass.getpass(prompt)
    confirm = getpass.getpass("Confirma: ")
    if pw != confirm:
        print("Las contraseñas no coinciden.", file=sys.stderr)
        return None
    if len(pw) < 4:
        print("La contraseña debe tener al menos 4 caracteres.", file=sys.stderr)
        return None
    return pw


def main() -> int:
    parser = argparse.ArgumentParser(description="Agrega o actualiza usuarios en data/users.db.")
    parser.add_argument("--users", required=True,
                        help="Nombres separados por coma, p. ej. usr1,usr2,usr3")
    parser.add_argument("--same-password", action="store_true",
                        help="Pide una sola contraseña y la aplica a todos los usuarios.")
    parser.add_argument("--list", action="store_true",
                        help="Lista los usuarios registrados después de crear/actualizar.")
    args = parser.parse_args()

    usernames = [u.strip() for u in args.users.split(",") if u.strip()]
    if not usernames:
        print("No se proporcionaron nombres de usuario.", file=sys.stderr)
        return 1

    if args.same_password:
        password = _ask_password("Contraseña compartida: ")
        if password is None:
            return 2
        for name in usernames:
            try:
                upsert_user(name, password)
                print(f"[ok] {name}")
            except AuthError as exc:
                print(f"[error] {name}: {exc}", file=sys.stderr)
    else:
        for name in usernames:
            password = _ask_password(f"Contraseña para {name}: ")
            if password is None:
                print(f"[skip] {name}", file=sys.stderr)
                continue
            try:
                upsert_user(name, password)
                print(f"[ok] {name}")
            except AuthError as exc:
                print(f"[error] {name}: {exc}", file=sys.stderr)

    if args.list:
        print("\nUsuarios registrados:")
        for name in list_usernames():
            print(f"  - {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
