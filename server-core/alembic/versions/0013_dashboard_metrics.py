"""
Dashboard Metrics Table for Historical Analysis.
Stores aggregated metrics for trend analysis and dashboard history.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0013_dashboard_metrics"
down_revision = "0012_alert_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dashboard_metrics table
    op.create_table(
        "dashboard_metrics",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_group", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("value_type", sa.String(20), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl_days", sa.Integer(), nullable=False, default=90),
    )
    
    # Create indexes (skipped - already created by migration 0001)
    # op.create_index("ix_dash_metric_group_time", "dashboard_metrics", ["metric_group", "recorded_at"])
    # op.create_index("ix_dash_metric_name_time", "dashboard_metrics", ["metric_name", "recorded_at"])
    # op.create_index("ix_dash_metric_recorded", "dashboard_metrics", ["recorded_at"])


def downgrade() -> None:
    # No indexes were created in upgrade (all skipped)
    op.drop_table("dashboard_metrics")