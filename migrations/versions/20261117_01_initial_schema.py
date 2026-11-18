"""Esquema inicial de persistencia SipánAlert.

Revisar esta migración antes de aplicarla con Alembic.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261117_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("reports", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("content", sa.Text()), sa.Column("content_hash", sa.String(64)), sa.Column("source", sa.String(64), nullable=False), sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("model_version", sa.String(80)), sa.Column("deletion_token_hash", sa.String(64)), sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id")), sa.Column("deleted_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_reports_content_hash", "reports", ["content_hash"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_table("analyses", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False), sa.Column("analyzer_version", sa.String(80)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("predictions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analyses.id"), nullable=False), sa.Column("label", sa.String(64), nullable=False), sa.Column("probability", sa.Float(), nullable=False), sa.UniqueConstraint("analysis_id", "label", name="uq_prediction_analysis_label"))
    op.create_table("human_reviews", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.id"), nullable=False), sa.Column("decision", sa.String(20), nullable=False), sa.Column("labels", postgresql.JSONB(), nullable=False), sa.Column("note", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("emerging_patterns", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("similarity", sa.Float(), nullable=False), sa.Column("common_terms", postgresql.JSONB(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("dataset_versions", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(120), nullable=False, unique=True), sa.Column("manifest", postgresql.JSONB(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade():
    op.drop_table("dataset_versions"); op.drop_table("emerging_patterns"); op.drop_table("human_reviews"); op.drop_table("predictions"); op.drop_table("analyses"); op.drop_index("ix_reports_status", table_name="reports"); op.drop_index("ix_reports_content_hash", table_name="reports"); op.drop_table("reports")
