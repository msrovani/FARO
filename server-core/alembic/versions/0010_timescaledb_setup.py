"""
TimescaleDB Setup for Time-Series Optimization.
Optimization Fase 4: Convert vehicle_observations to hypertable for time-series performance.
TimescaleDB is a PostgreSQL extension for time-series data.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0010_timescaledb_setup"
down_revision = "0009_materialized_views_hotspots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TimescaleDB not available - skipping time-series optimization
    # The TimescaleDB extension is not installed in this environment
    pass


def downgrade() -> None:
    # No TimescaleDB operations were performed in upgrade (all skipped)
    pass
