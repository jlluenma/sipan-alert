"""Entidades ORM para reportes, revisión y evolución del dataset."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipan.persistence.database import Base


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Report(Timestamped, Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pendiente", nullable=False, index=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(80))
    deletion_token_hash: Mapped[Optional[str]] = mapped_column(String(64))
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("reports.id"))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="report", cascade="all, delete-orphan")
    reviews: Mapped[list["HumanReview"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class Analysis(Timestamped, Base):
    __tablename__ = "analyses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    analyzer_version: Mapped[Optional[str]] = mapped_column(String(80))
    report: Mapped[Report] = relationship(back_populates="analyses")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("analysis_id", "label", name="uq_prediction_analysis_label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    probability: Mapped[float] = mapped_column(nullable=False)
    analysis: Mapped[Analysis] = relationship(back_populates="predictions")


class HumanReview(Timestamped, Base):
    __tablename__ = "human_reviews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reports.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    labels: Mapped[dict] = mapped_column(JSONB, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    report: Mapped[Report] = relationship(back_populates="reviews")


class EmergingPattern(Timestamped, Base):
    __tablename__ = "emerging_patterns"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), default="candidato", nullable=False)
    similarity: Mapped[float] = mapped_column(nullable=False)
    common_terms: Mapped[list] = mapped_column(JSONB, nullable=False)


class DatasetVersion(Timestamped, Base):
    __tablename__ = "dataset_versions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    manifest: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="generado", nullable=False)
