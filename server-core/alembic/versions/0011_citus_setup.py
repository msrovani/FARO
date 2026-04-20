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
    # Try to install Citus extension - skip if not available
    try:
        op.execute(
            sa.text(
                """
                CREATE EXTENSION IF NOT EXISTS citus;
                """
            )
        )
        citus_available = True
    except Exception:
        # Citus not available (likely not installed or Docker not running)
        citus_available = False
        print("WARNING: Citus extension not available - skipping horizontal scaling")

    if citus_available:
        # Distribute tables by agency_id for multi-tenant sharding
        tables_to_distribute = [
            'vehicleobservation',
            'convoy_events',
            'impossible_travel_events',
            'route_anomaly_events',
            'sensitive_asset_recurrence_events',
            'roaming_events',
            'suspicion_scores',
            'watchlist_hits'
        ]

        for table in tables_to_distribute:
            op.execute(
                sa.text(
                    f"""
                    SELECT create_distributed_table('{table}', 'agency_id', if_not_exists => TRUE);
                    """
                )
            )

        # Reference tables (not distributed, replicated to all nodes)
        reference_tables = ['agency', 'user']

        for table in reference_tables:
            op.execute(
                sa.text(
                    f"""
                    SELECT create_reference_table('{table}', if_not_exists => TRUE);
                    """
                )
            )


def downgrade() -> None:
    # Try to undistribute tables - skip if Citus not available
    try:
        # Undistribute tables
        tables_to_undistribute = [
            'vehicleobservation',
            'convoy_events',
            'impossible_travel_events',
            'route_anomaly_events',
            'sensitive_asset_recurrence_events',
            'roaming_events',
            'suspicion_scores',
            'watchlist_hits'
        ]

        for table in tables_to_undistribute:
            op.execute(
                sa.text(
                    f"""
                    SELECT undistribute_table('{table}', if_exists => TRUE);
                    """
                )
            )

        # Remove reference tables
        reference_tables = ['agency', 'user']

        for table in reference_tables:
            op.execute(
                sa.text(
                    f"""
                    SELECT undistribute_table('{table}', if_exists => TRUE);
                    """
                )
            )

        # Drop Citus extension
        op.execute(
            sa.text(
                """
                DROP EXTENSION IF EXISTS citus;
                """
            )
        )
    except Exception:
        # Citus not available - nothing to rollback
        print("WARNING: Citus extension not available - nothing to rollback")
