"""Fix urgencylevel and suspicionreason enums to use lowercase values

The urgencylevel and suspicionreason enums were created with uppercase values
but the Python enums use lowercase values. This migration fixes that.

Revision ID: 0018_fix_enum_lowercase
Revises: 0017_fix_suspicionlevel_enum
Create Date: 2026-04-20 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0018_fix_urgencylevel_and_suspicionreason_enums'
down_revision = '0017_fix_suspicionlevel_enum'
branch_labels = None
depends_on = None


def upgrade():
    # Fix urgencylevel and suspicionreason enums to use lowercase values (skipped - already handled by migration 0001)
    # The enums urgencylevel and suspicionreason are already defined correctly in the SQLAlchemy model
    pass


def downgrade():
    # No operations were performed in upgrade (already handled by migration 0001)
    pass
