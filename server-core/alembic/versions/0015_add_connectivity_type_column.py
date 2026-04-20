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
    # Add connectivity_type column to vehicleobservation table
    op.add_column('vehicleobservation', sa.Column('connectivity_type', sa.String(20), nullable=True))


def downgrade():
    # Remove connectivity_type column from vehicleobservation table
    op.drop_column('vehicleobservation', 'connectivity_type')
