"""Publicaciones de comunidad con moderación independiente."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision='20261118_04'
down_revision='20261118_03'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('community_posts',sa.Column('id',UUID(as_uuid=True),primary_key=True,server_default=sa.text('gen_random_uuid()')),sa.Column('owner_id',UUID(as_uuid=True),sa.ForeignKey('users.id'),nullable=False),sa.Column('alias',sa.String(40),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('status',sa.String(20),nullable=False,server_default='pendiente'),sa.Column('reviewer_id',UUID(as_uuid=True),sa.ForeignKey('users.id')),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
def downgrade():op.drop_table('community_posts')
