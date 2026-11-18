"""Reinicia la BD local con el dump de demostracion y fija contrasenas conocidas.

Uso: python scripts/seed_demo.py [--dump ruta]

Por defecto usa fixtures/demo.dump. Requiere DATABASE_URL en .env, pg_restore en PATH
y permisos de propietario sobre el schema public. DESTRUYE todos los datos del schema.

Credenciales que fija (solo para desarrollo local):
  admin.demo@sipanalert.local   / sipan_demo_2026 (administrador + usuario)
  revisor.demo@sipanalert.local / sipan_demo_2026 (revisor + usuario)
  usuario.demo@sipanalert.local / sipan_demo_2026 (usuario)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from sipan import config  # noqa: E402
from sipan.auth import _hash_password  # noqa: E402
from sipan.persistence.database import get_session_factory, session_scope  # noqa: E402

DEMO_PASSWORD = "sipan_demo_2026"
DEMO_EMAILS = (
    "admin.demo@sipanalert.local",
    "revisor.demo@sipanalert.local",
    "usuario.demo@sipanalert.local",
)


def _parse_url(url: str) -> dict[str, str]:
    parsed = urlparse(url.replace("postgresql+psycopg", "postgresql"))
    return {
        "user": parsed.username or "",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "db": parsed.path.lstrip("/"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", default=str(ROOT / "fixtures" / "demo.dump"))
    args = parser.parse_args()

    dump_path = Path(args.dump)
    if not dump_path.exists():
        print(f"ERROR: no existe el dump {dump_path}", file=sys.stderr)
        return 2

    if not config.DATABASE_URL:
        print("ERROR: DATABASE_URL no configurado en .env", file=sys.stderr)
        return 2

    pg_restore = shutil.which("pg_restore")
    if pg_restore is None:
        print("ERROR: pg_restore no esta en PATH", file=sys.stderr)
        return 2

    parts = _parse_url(config.DATABASE_URL)
    print(f"Destino: {parts['user']}@{parts['host']}:{parts['port']}/{parts['db']}")

    # 1) Limpiar schema para evitar conflictos de primary key.
    get_session_factory.cache_clear()
    with session_scope() as s:
        s.execute(text("DROP SCHEMA public CASCADE"))
        s.execute(text("CREATE SCHEMA public"))
    print("Schema public reiniciado.")

    # 2) Restaurar dump (schema + data).
    import os as _os
    env = dict(_os.environ)
    env["PGPASSWORD"] = parts["password"]
    cmd = [
        pg_restore,
        "--no-owner",
        "--no-privileges",
        "--dbname",
        f"postgresql://{parts['user']}@{parts['host']}:{parts['port']}/{parts['db']}",
        str(dump_path),
    ]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    print(f"Dump restaurado desde {dump_path}.")

    # 3) Fijar contrasenas conocidas para los tres usuarios demo.
    get_session_factory.cache_clear()
    with session_scope() as s:
        new_hash = _hash_password(DEMO_PASSWORD)
        for email in DEMO_EMAILS:
            s.execute(
                text("UPDATE users SET password_hash = :hash WHERE email = :email"),
                {"hash": _hash_password(DEMO_PASSWORD), "email": email},
            )
    print(f"Contrasena comun fijada: {DEMO_PASSWORD}")
    for email in DEMO_EMAILS:
        print(f"  {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
