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
    def submit(self, content: str, predictions: dict[str, float], model_version: str | None,
               owner_id: str | None = None) -> tuple[str, str, str | None]:
        token = secrets.token_urlsafe(18)
        now = datetime.now(timezone.utc)
        with session_scope() as session:
            repo = ReportRepository(session)
            duplicate = session.scalar(select(Report).where(Report.content_hash == _hash(content), Report.deleted_at.is_(None)))
            report = repo.save(Report(content=content, content_hash=_hash(content), source=config.VOLUNTARY_SOURCE,
                consented_at=now, model_version=model_version, deletion_token_hash=_hash(token), duplicate_of_id=duplicate.id if duplicate else None,
                owner_id=UUID(owner_id) if owner_id else None))
            analysis = Analysis(report=report, analyzer_version=model_version)
            analysis.predictions = [Prediction(label=label, probability=value) for label, value in predictions.items()]
            session.add(analysis)
            return str(report.id), token, str(duplicate.id) if duplicate else None
    def list(self, status: str | None = None) -> list[Report]:
        with session_scope() as session: return ReportRepository(session).find_all(status)
    def list_owned(self, owner_id: str) -> list[Report]:
        with session_scope() as session: return ReportRepository(session).find_by_owner(UUID(owner_id))
    def review(self, report_id: str, decision: str, labels: dict[str, int], note: str,
               reviewer_id: str | None = None) -> None:
        if decision not in {"validado", "rechazado"}:
            raise ValueError("La decisión de revisión no es válida.")
        if set(labels) != set(config.LABELS) or any(type(value) is not int or value not in (0, 1) for value in labels.values()):
            raise ValueError("Revisa las cuatro categorías antes de guardar.")
        with session_scope() as session:
            report = ReportRepository(session).find_by_id(UUID(report_id))
            if not report: raise ValueError("No se encontró el aporte.")
            report.status = decision
            session.add(HumanReview(report=report, decision=decision, labels=labels, note=note,
                                    reviewer_id=UUID(reviewer_id) if reviewer_id else None))
    def mark_duplicate(self, report_id: str, original_id: str) -> None:
        if report_id == original_id:
            raise ValueError("Un aporte no puede ser duplicado de sí mismo.")
        with session_scope() as session:
            repo = ReportRepository(session)
            report, original = repo.find_by_id(UUID(report_id)), repo.find_by_id(UUID(original_id))
            if not report or not original or original.deleted_at:
                raise ValueError("No se encontró el aporte original.")
            report.duplicate_of_id = original.id
    def delete(self, report_id: str, token: str, owner_id: str | None = None) -> bool:
        with session_scope() as session:
            report = ReportRepository(session).find_by_id(UUID(report_id))
            if not report or not report.deletion_token_hash or not secrets.compare_digest(report.deletion_token_hash, _hash(token)): return False
            if owner_id and report.owner_id != UUID(owner_id): return False
            report.content = report.content_hash = report.deletion_token_hash = None
            report.status, report.deleted_at = "eliminado", datetime.now(timezone.utc)
            return True


class LearningService:
    def __init__(self): self.reports = ReportService()
    @staticmethod
    def _as_dict(report: Report) -> dict:
        latest = report.analyses[-1] if report.analyses else None
        review = max(report.reviews, key=lambda item: item.created_at) if report.reviews else None
        return {"id": str(report.id), "content": report.content, "status": report.status,
                "received_at": report.created_at.isoformat(), "source": report.source,
                "duplicate_of": str(report.duplicate_of_id) if report.duplicate_of_id else None,
                "labels": review.labels if review else {},
                "prediction": {item.label: item.probability for item in latest.predictions} if latest else {}}
    def list_reports(self, status: str | None = None) -> list[dict]:
        return [self._as_dict(report) for report in self.reports.list(status)]
    def create_dataset_version(self) -> dict:
        from sipan.dataset_versions import create_version

        manifest = create_version(self.list_reports())
        with session_scope() as session:
            session.add(DatasetVersion(name=manifest["version"], manifest=manifest))
        return manifest


class AccountService:
    def report_history(self, user_id: str) -> list[dict]:
        reports = ReportService().list_owned(user_id)
        return [{"id": str(report.id), "estado": report.status, "fecha": report.created_at,
                 "version_modelo": report.model_version or "sin modelo"} for report in reports]
    def delete_own_report(self, user_id: str, report_id: str, token: str) -> bool:
        return ReportService().delete(report_id, token, owner_id=user_id)
