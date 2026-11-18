"""Otorga un rol. Uso: python scripts/grant_role.py correo@ejemplo.com revisor"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sipan.auth import AuthService, ROLE_ADMIN, ROLE_REVIEWER, ROLE_USER

if len(sys.argv) != 3 or sys.argv[2] not in {ROLE_USER, ROLE_REVIEWER, ROLE_ADMIN}:
    raise SystemExit("Uso: python scripts/grant_role.py correo@ejemplo.com usuario|revisor|administrador")

AuthService().grant_role(sys.argv[1], sys.argv[2])
print("Rol asignado.")
