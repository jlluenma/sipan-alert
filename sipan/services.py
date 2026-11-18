"""Servicios de aplicación que aíslan Streamlit de SQLAlchemy."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from sipan import config
from sipan.persistence.database import session_scope
from sipan.persistence.models import Analysis, DatasetVersion, HumanReview, Prediction, Report
from sipan.persistence.repositories import ReportRepository


def _hash(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()


class ReportService:
    def submit(self, content: str, predictions: dict[str, float], model_version: str | None) -> tuple[str, str, str | None]:
        token = secrets.token_urlsafe(18)
        now = datetime.now(timezone.utc)
        with session_scope() as session:
            repo = ReportRepository(session)
            duplicate = session.scalar(select(Report).where(Report.content_hash == _hash(content), Report.deleted_at.is_(None)))
            report = repo.save(Report(content=content, content_hash=_hash(content), source=config.VOLUNTARY_SOURCE,
                consented_at=now, model_version=model_version, deletion_token_hash=_hash(token), duplicate_of_id=duplicate.id if duplicate else None))
            analysis = Analysis(report=report, analyzer_version=model_version)
            analysis.predictions = [Prediction(label=label, probability=value) for label, value in predictions.items()]
            session.add(analysis)
            return str(report.id), token, str(duplicate.id) if duplicate else None
    def list(self, status: str | None = None) -> list[Report]:
        with session_scope() as session: return ReportRepository(session).find_all(status)
    def review(self, report_id: str, decision: str, labels: dict[str, int], note: str) -> None:
        if decision not in {"validado", "rechazado"}:
            raise ValueError("La decisión de revisión no es válida.")
        with session_scope() as session:
            report = ReportRepository(session).find_by_id(UUID(report_id))
            if not report: raise ValueError("No se encontró el aporte.")
            report.status = decision
            session.add(HumanReview(report=report, decision=decision, labels=labels, note=note))
    def mark_duplicate(self, report_id: str, original_id: str) -> None:
        if report_id == original_id:
            raise ValueError("Un aporte no puede ser duplicado de sí mismo.")
        with session_scope() as session:
            repo = ReportRepository(session)
            report, original = repo.find_by_id(UUID(report_id)), repo.find_by_id(UUID(original_id))
            if not report or not original or original.deleted_at:
                raise ValueError("No se encontró el aporte original.")
            report.duplicate_of_id = original.id
    def delete(self, report_id: str, token: str) -> bool:
        with session_scope() as session:
            report = ReportRepository(session).find_by_id(UUID(report_id))
            if not report or not report.deletion_token_hash or not secrets.compare_digest(report.deletion_token_hash, _hash(token)): return False
            report.content = report.content_hash = report.deletion_token_hash = None
            report.status, report.deleted_at = "eliminado", datetime.now(timezone.utc)
            return True


class LearningService:
    def __init__(self): self.reports = ReportService()
    @staticmethod
    def _as_dict(report: Report) -> dict:
        latest = report.analyses[-1] if report.analyses else None
        return {"id": str(report.id), "content": report.content, "status": report.status,
                "received_at": report.created_at.isoformat(), "source": report.source,
                "duplicate_of": str(report.duplicate_of_id) if report.duplicate_of_id else None,
                "prediction": {item.label: item.probability for item in latest.predictions} if latest else {}}
    def list_reports(self, status: str | None = None) -> list[dict]:
        return [self._as_dict(report) for report in self.reports.list(status)]
    def create_dataset_version(self) -> dict:
        from sipan.dataset_versions import create_version

        manifest = create_version(self.list_reports())
        with session_scope() as session:
            session.add(DatasetVersion(name=manifest["version"], manifest=manifest))
        return manifest
