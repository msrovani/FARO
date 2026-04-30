"""Fix sync_status column type to use proper enum

Revision ID: 0016
Revises: 0015
Create Date: 2026-04-20 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016_fix_sync_status_enum'
down_revision = '0015_add_connectivity_type'
branch_labels = None
depends_on = None


def upgrade():
    # Fix sync_status column type to use proper enum (skipped - already handled by migration 0001)
    # The enum syncstatus and column type are already defined in the SQLAlchemy model
    pass


def downgrade():
    # No operations were performed in upgrade (already handled by migration 0001)
    pass
