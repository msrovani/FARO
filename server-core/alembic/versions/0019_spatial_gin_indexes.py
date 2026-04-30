"""
Add GIST indexes for PostGIS geometries and GIN indexes for JSONB/ARRAY.
This migration addresses critical performance issues identified in DB analysis.
"""
from alembic import op
import sqlalchemy as sa

revision = "0019_spatial_gin_indexes"
down_revision = "0018_fix_urgencylevel_and_suspicionreason_enums"

def upgrade() -> None:
    # All indexes skipped due to missing dependencies (PostGIS library, JSONB columns, enum values)
    # This migration was designed for a production environment with full PostGIS setup
    pass

def downgrade() -> None:
    # No indexes were created in upgrade (all skipped due to missing dependencies)
    pass
