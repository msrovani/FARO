"""Add connectivity_type column to vehicleobservation table

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0015_add_connectivity_type'
down_revision = '0014_add_sync_error'
branch_labels = None
depends_on = None


def upgrade():
    # Add connectivity_type column to vehicleobservation table (skipped - already exists from migration 0001)
    # op.add_column('vehicleobservation', sa.Column('connectivity_type', sa.String(20), nullable=True))
    pass


def downgrade():
    # No column was added in upgrade (already exists from migration 0001)
    pass
