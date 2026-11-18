"""Almacenamiento local de aportes voluntarios revisados por personas.

El analizador normal no usa este módulo. Solo se persiste el texto anonimizado
que una persona confirma compartir desde la interfaz.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sipan import config


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _connection(path: Path = config.CONTINUAL_DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize(path: Path = config.CONTINUAL_DB_PATH) -> None:
    with _connection(path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                content TEXT,
                content_hash TEXT,
                source TEXT NOT NULL,
                consented_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                model_version TEXT,
                prediction_json TEXT NOT NULL,
                confidence_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pendiente',
                labels_json TEXT,
                reviewer_note TEXT,
                reviewed_at TEXT,
                duplicate_of TEXT REFERENCES reports(id),
                deleted_at TEXT
            );
            CREATE INDEX IF NOT EXISTS reports_status_idx ON reports(status);
            CREATE INDEX IF NOT EXISTS reports_hash_idx ON reports(content_hash);
            CREATE TABLE IF NOT EXISTS deletion_tokens (
                report_id TEXT PRIMARY KEY REFERENCES reports(id),
                token_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS review_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL REFERENCES reports(id),
                action TEXT NOT NULL,
                labels_json TEXT,
                note TEXT,
                created_at TEXT NOT NULL
            );
        """)


def submit_report(content: str, predictions: dict[str, float], model_version: str | None,
                  source: str = config.VOLUNTARY_SOURCE,
                  path: Path = config.CONTINUAL_DB_PATH) -> tuple[str, str, str | None]:
    """Guarda un aporte consentido y devuelve id, código de eliminación y duplicado."""
    if not content.strip():
        raise ValueError("El aporte no puede estar vacío.")
    initialize(path)
    report_id = f"REP-{secrets.token_hex(6).upper()}"
    deletion_code = secrets.token_urlsafe(18)
    content_hash = _hash(content)
    now = _now()
    with _connection(path) as conn:
        duplicate = conn.execute(
            "SELECT id FROM reports WHERE content_hash = ? AND deleted_at IS NULL ORDER BY received_at LIMIT 1",
            (content_hash,),
        ).fetchone()
        duplicate_of = duplicate["id"] if duplicate else None
        conn.execute(
            """INSERT INTO reports (id, content, content_hash, source, consented_at, received_at,
               model_version, prediction_json, confidence_json, duplicate_of)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (report_id, content, content_hash, source, now, now, model_version,
             json.dumps(predictions, ensure_ascii=False), json.dumps(predictions, ensure_ascii=False), duplicate_of),
        )
        conn.execute("INSERT INTO deletion_tokens (report_id, token_hash) VALUES (?, ?)",
                     (report_id, _hash(deletion_code)))
        conn.execute("INSERT INTO review_events (report_id, action, created_at) VALUES (?, 'recibido', ?)",
                     (report_id, now))
    return report_id, deletion_code, duplicate_of


def _row_to_report(row: sqlite3.Row) -> dict[str, Any]:
    report = dict(row)
    for name in ("prediction_json", "confidence_json", "labels_json"):
        report[name.removesuffix("_json")] = json.loads(report.pop(name) or "{}")
    return report


def list_reports(status: str | None = None, path: Path = config.CONTINUAL_DB_PATH) -> list[dict[str, Any]]:
    initialize(path)
    query = "SELECT * FROM reports WHERE deleted_at IS NULL"
    params: list[str] = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY received_at DESC"
    with _connection(path) as conn:
        return [_row_to_report(row) for row in conn.execute(query, params)]


def review_report(report_id: str, status: str, labels: dict[str, int], note: str,
                  path: Path = config.CONTINUAL_DB_PATH) -> None:
    if status not in {"validado", "rechazado"}:
        raise ValueError("El estado de revisión no es válido.")
    unknown = set(labels) - set(config.LABELS)
    if unknown:
        raise ValueError("La revisión contiene etiquetas desconocidas.")
    normalized = {label: int(bool(labels.get(label, 0))) for label in config.LABELS}
    now = _now()
    initialize(path)
    with _connection(path) as conn:
        updated = conn.execute(
            """UPDATE reports SET status = ?, labels_json = ?, reviewer_note = ?, reviewed_at = ?
               WHERE id = ? AND deleted_at IS NULL""",
            (status, json.dumps(normalized), note.strip(), now, report_id),
        )
        if updated.rowcount != 1:
            raise ValueError("No se encontró el aporte para revisar.")
        conn.execute("""INSERT INTO review_events (report_id, action, labels_json, note, created_at)
                        VALUES (?, ?, ?, ?, ?)""",
                     (report_id, status, json.dumps(normalized), note.strip(), now))


def mark_duplicate(report_id: str, original_id: str, note: str = "",
                   path: Path = config.CONTINUAL_DB_PATH) -> None:
    if report_id == original_id:
        raise ValueError("Un aporte no puede ser duplicado de sí mismo.")
    initialize(path)
    now = _now()
    with _connection(path) as conn:
        original = conn.execute("SELECT 1 FROM reports WHERE id = ? AND deleted_at IS NULL", (original_id,)).fetchone()
        if original is None:
            raise ValueError("No se encontró el aporte original.")
        conn.execute("UPDATE reports SET duplicate_of = ? WHERE id = ?", (original_id, report_id))
        conn.execute("INSERT INTO review_events (report_id, action, note, created_at) VALUES (?, 'duplicado', ?, ?)",
                     (report_id, note.strip(), now))


def delete_report(report_id: str, deletion_code: str, path: Path = config.CONTINUAL_DB_PATH) -> bool:
    """Elimina el contenido y el hash. Se conserva una auditoría sin texto."""
    initialize(path)
    with _connection(path) as conn:
        token = conn.execute("SELECT token_hash FROM deletion_tokens WHERE report_id = ?", (report_id,)).fetchone()
        if token is None or not secrets.compare_digest(token["token_hash"], _hash(deletion_code)):
            return False
        now = _now()
        conn.execute("""UPDATE reports SET content = NULL, content_hash = NULL, status = 'eliminado',
                        labels_json = NULL, deleted_at = ? WHERE id = ?""", (now, report_id))
        conn.execute("DELETE FROM deletion_tokens WHERE report_id = ?", (report_id,))
        conn.execute("INSERT INTO review_events (report_id, action, created_at) VALUES (?, 'eliminado', ?)",
                     (report_id, now))
    return True


def review_events(report_id: str, path: Path = config.CONTINUAL_DB_PATH) -> list[dict[str, Any]]:
    initialize(path)
    with _connection(path) as conn:
        return [dict(row) for row in conn.execute(
            "SELECT action, labels_json, note, created_at FROM review_events WHERE report_id = ? ORDER BY id", (report_id,)
        )]
