"""
Initial FARO schema with geospatial and analytical tables.
"""
from __future__ import annotations

from alembic import op

from app.db.base import Base

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)
    
    # Alterar coluna type da tabela agency para permitir NULL temporariamente
    # O enum agencytype só será criado na migration 0006
    op.execute("ALTER TABLE agency ALTER COLUMN type DROP NOT NULL")


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
