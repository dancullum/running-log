"""Add last_sync_at to strava_tokens

Revision ID: 001
Revises:
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add last_sync_at column to strava_tokens table
    with op.batch_alter_table('strava_tokens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_sync_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('strava_tokens', schema=None) as batch_op:
        batch_op.drop_column('last_sync_at')
