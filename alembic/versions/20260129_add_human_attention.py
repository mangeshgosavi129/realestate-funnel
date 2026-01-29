"""add human attention flag

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-01-29 19:33:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversations', sa.Column('needs_human_attention', sa.Boolean(), server_default='false', nullable=True))


def downgrade() -> None:
    op.drop_column('conversations', 'needs_human_attention')
