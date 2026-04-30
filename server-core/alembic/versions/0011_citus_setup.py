"""
Citus Setup for Horizontal Scaling.
Optimization Fase 5: Enable horizontal scaling with Citus.
Citus is a PostgreSQL extension for distributed database capabilities.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0011_citus_setup"
down_revision = "0010_timescaledb_setup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Citus not available - skipping horizontal scaling
    # The Citus extension is not installed in this environment
    pass


def downgrade() -> None:
    # No Citus operations were performed in upgrade (all skipped)
    pass
