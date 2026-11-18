"""Comentarios moderados y reacciones únicas."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision='20261118_05'
down_revision='20261118_04'
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('community_comments',sa.Column('id',UUID(),primary_key=True,server_default=sa.text('gen_random_uuid()')),sa.Column('post_id',UUID(),sa.ForeignKey('community_posts.id'),nullable=False),sa.Column('owner_id',UUID(),sa.ForeignKey('users.id'),nullable=False),sa.Column('content',sa.Text(),nullable=False),sa.Column('status',sa.String(20),server_default='pendiente',nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False))
    op.create_table('community_reactions',sa.Column('post_id',UUID(),sa.ForeignKey('community_posts.id'),primary_key=True),sa.Column('owner_id',UUID(),sa.ForeignKey('users.id'),primary_key=True))
def downgrade():
    op.drop_table('community_reactions');op.drop_table('community_comments')
