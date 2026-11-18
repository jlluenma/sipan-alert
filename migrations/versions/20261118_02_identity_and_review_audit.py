"""Usuarios, roles y trazabilidad de revisiones."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261118_02"
down_revision = "20261117_01"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(254), nullable=False, unique=True), sa.Column("password_hash", sa.String(256), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(32), nullable=False, unique=True))
    op.create_table("user_roles", sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True))
    op.bulk_insert(sa.table("roles", sa.column("id", sa.Integer), sa.column("name", sa.String)), [{"id": 1, "name": "usuario"}, {"id": 2, "name": "revisor"}, {"id": 3, "name": "administrador"}])
    op.add_column("reports", sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.add_column("human_reviews", sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")))

def downgrade():
    op.drop_column("human_reviews", "reviewer_id")
    op.drop_column("reports", "owner_id")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
