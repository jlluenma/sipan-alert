"""Fotos de publicaciones de la comunidad."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '20261118_06'
down_revision = '20261118_05'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'community_post_photos',
        sa.Column('post_id', UUID(), sa.ForeignKey('community_posts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('position', sa.SmallInteger(), primary_key=True),
        sa.Column('image', sa.LargeBinary(), nullable=False),
        sa.CheckConstraint('position BETWEEN 1 AND 2'),
    )


def downgrade():
    op.drop_table('community_post_photos')
