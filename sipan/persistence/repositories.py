"""Repositorios ORM pequeños y tipados para los servicios."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from sipan.persistence.models import Analysis, Prediction, Report


class ReportRepository:
    def __init__(self, session: Session): self.session = session
    def save(self, report: Report) -> Report:
        self.session.add(report); self.session.flush(); return report
    def find_by_id(self, report_id: UUID) -> Report | None:
        return self.session.get(Report, report_id)
    def find_all(self, status: str | None = None, offset: int = 0, limit: int = 50) -> list[Report]:
        stmt = select(Report).where(Report.deleted_at.is_(None)).order_by(Report.created_at.desc()).offset(offset).limit(limit)
        if status: stmt = stmt.where(Report.status == status)
        return list(self.session.scalars(stmt.options(selectinload(Report.analyses).selectinload(Analysis.predictions))).all())
    def count(self, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Report).where(Report.deleted_at.is_(None))
        if status: stmt = stmt.where(Report.status == status)
        return int(self.session.scalar(stmt) or 0)
