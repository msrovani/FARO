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
    # Try to install TimescaleDB extension - skip if not available
    try:
        op.execute(
            sa.text(
                """
                CREATE EXTENSION IF NOT EXISTS timescaledb;
                """
            )
        )
        timescale_available = True
    except Exception:
        # TimescaleDB not available (likely not installed or Docker not running)
        timescale_available = False
        print("WARNING: TimescaleDB extension not available - skipping time-series optimization")

    if timescale_available:
        # Convert vehicle_observations to hypertable
        op.execute(
            sa.text(
                """
                SELECT create_hypertable('vehicleobservation', 'observed_at_local', if_not_exists => TRUE);
                """
            )
        )

        # Create continuous aggregate for daily observation counts
        op.execute(
            sa.text(
                """
                CREATE MATERIALIZED VIEW mv_daily_observation_counts
                WITH (timescaledb.continuous) AS
                SELECT
                    DATE_TRUNC('day', observed_at_local) as day,
                    agency_id,
                    COUNT(*) as observation_count
                FROM vehicleobservation
                GROUP BY DATE_TRUNC('day', observed_at_local), agency_id
                WITH NO DATA;
                """
            )
        )

        # Set refresh policy for continuous aggregate
        op.execute(
            sa.text(
                """
                SELECT add_continuous_aggregate_policy('mv_daily_observation_counts',
                    start_offset => INTERVAL '30 days',
                    end_offset => INTERVAL '1 hour',
                    schedule_interval => INTERVAL '1 hour');
                """
            )
        )


def downgrade() -> None:
    # Try to rollback TimescaleDB - skip if not available
    try:
        # Remove continuous aggregate policy
        op.execute(
            sa.text(
                """
                SELECT remove_continuous_aggregate_policy('mv_daily_observation_counts', if_exists => TRUE);
                """
            )
        )

        # Drop continuous aggregate
        op.execute(
            sa.text(
                """
                DROP MATERIALIZED VIEW IF EXISTS mv_daily_observation_counts;
                """
            )
        )

        # Convert hypertable back to regular table
        op.execute(
            sa.text(
                """
                SELECT remove_hypertable('vehicleobservation', if_exists => TRUE);
                """
            )
        )

        # Drop TimescaleDB extension
        op.execute(
            sa.text(
                """
                DROP EXTENSION IF EXISTS timescaledb;
                """
            )
        )
    except Exception:
        # TimescaleDB not available - nothing to rollback
        print("WARNING: TimescaleDB extension not available - nothing to rollback")
