"""Add performance indexes for common query patterns

Revision ID: 0023
Revises: 0022
Create Date: 2026-04-25

This migration adds:
- Partial indexes for common filters
- Composite indexes for time-based queries
- Missing indexes on critical columns

Best Practice Reference:
- https://www.postgresql.org/docs/current/indexes-partial.html
- https://www.postgresql.org/docs/current/indexes-multicolumn.html
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0023_performance_indexes"
down_revision = "0022_missing_fk_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # P1-6: Index on created_at for insertion order queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vehicleobservation_created_at
        ON vehicleobservation (created_at)
    """)
    
    # Composite index on AlertHistory for time-based queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alerthistory_fired_severity
        ON alerthistory (fired_at, severity)
    """)
    
    # Composite index on DashboardMetric for time-based queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_dashboardmetric_name_time
        ON dashboardmetric (metric_name, recorded_at)
    """)


def downgrade() -> None:
    op.drop_index("ix_dashboardmetric_name_time", table_name="dashboardmetric")
    op.drop_index("ix_alerthistory_fired_severity", table_name="alerthistory")
    op.drop_index("ix_vehicleobservation_created_at", table_name="vehicleobservation")
