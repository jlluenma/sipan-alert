"""Crea una cuenta administradora inicial. Uso: python scripts/create_admin.py correo@ejemplo.com"""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sipan.auth import AuthService, ROLE_ADMIN

if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/create_admin.py correo@ejemplo.com")

password = getpass.getpass("Contraseña del administrador: ")
service = AuthService()
service.register(sys.argv[1], password)
service.grant_role(sys.argv[1], ROLE_ADMIN)
print("Cuenta administradora creada.")
