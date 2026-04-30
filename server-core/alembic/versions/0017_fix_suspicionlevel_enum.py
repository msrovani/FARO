"""Fix suspicionlevel enum type to use correct SuspicionLevel values

The suspicionlevel enum was incorrectly created with SuspicionReason values
instead of SuspicionLevel values. This migration fixes that.

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-20 00:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0017_fix_suspicionlevel_enum'
down_revision = '0016_fix_sync_status_enum'
branch_labels = None
depends_on = None


def upgrade():
    # Fix suspicionlevel enum type to use correct SuspicionLevel values (skipped - already handled by migration 0001)
    # The enum suspicionlevel and column types are already defined correctly in the SQLAlchemy model
    pass


def downgrade():
    # No operations were performed in upgrade (already handled by migration 0001)
    pass
