"""Nombre visible de las cuentas."""
from alembic import op
import sqlalchemy as sa
revision='20261118_03'
down_revision='20261118_02'
branch_labels=None
depends_on=None
def upgrade():
    op.add_column('users',sa.Column('display_name',sa.String(80),nullable=True))
def downgrade():
    op.drop_column('users','display_name')
