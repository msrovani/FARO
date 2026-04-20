"""
Materialized Views for Hotspots Analysis.
Optimization Fase 2.4: Materialized views for pre-computed hotspot data.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0009_materialized_views_hotspots"
down_revision = "0008_parallel_query_tuning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create materialized views for hotspot analysis
    op.execute(
        sa.text(
            """
            CREATE MATERIALIZED VIEW mv_daily_hotspots AS
            SELECT
                DATE_TRUNC('day', observed_at_local) as day,
                ST_ClusterWithin(
                    ST_Collect(location),
                    500
                ) as hotspot_clusters
            FROM vehicleobservation
            WHERE observed_at_local >= NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('day', observed_at_local)
            WITH DATA;
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE MATERIALIZED VIEW mv_agency_hotspots AS
            SELECT
                agency_id,
                DATE_TRUNC('day', observed_at_local) as day,
                ST_ClusterWithin(
                    ST_Collect(location),
                    500
                ) as hotspot_clusters
            FROM vehicleobservation
            WHERE observed_at_local >= NOW() - INTERVAL '30 days'
            GROUP BY agency_id, DATE_TRUNC('day', observed_at_local)
            WITH DATA;
            """
        )
    )

    # Create unique indexes for CONCURRENTLY refresh
    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX mv_daily_hotspots_day_idx ON mv_daily_hotspots (day);
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE UNIQUE INDEX mv_agency_hotspots_agency_day_idx ON mv_agency_hotspots (agency_id, day);
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DROP MATERIALIZED VIEW IF EXISTS mv_agency_hotspots;
            """
        )
    )

    op.execute(
        sa.text(
            """
            DROP MATERIALIZED VIEW IF EXISTS mv_daily_hotspots;
            """
        )
    )
