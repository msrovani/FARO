"""Add sync_error column to vehicleobservation table

Revision ID: 0014
Revises: 0013
Create Date: 2026-04-19 23:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0014_add_sync_error'
down_revision = '0013_dashboard_metrics'
branch_labels = None
depends_on = None


def upgrade():
    # Add sync_error column to vehicleobservation table (skipped - already exists from migration 0001)
    # op.add_column('vehicleobservation', sa.Column('sync_error', sa.Text(), nullable=True))
    pass


def downgrade():
    # No column was added in upgrade (already exists from migration 0001)
    pass
