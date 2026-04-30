"""
Alert History Table for Prometheus Alert Storage.
Stores all triggered alerts from monitoring with TTL support.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0012_alert_history"
down_revision = "0011_citus_setup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create alert_history table
    op.create_table(
        "alert_history",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("alert_name", sa.String(100), nullable=False),
        sa.Column("alert_group", sa.String(100), nullable=False),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("urgency", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("insight", sa.Text(), nullable=True),
        sa.Column("possible_causes", sa.Text(), nullable=True),
        sa.Column("solutions", sa.Text(), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("annotations", sa.JSON(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, default=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(255), nullable=True),
        sa.Column("ttl_days", sa.Integer(), nullable=False, default=90),
    )
    
    # Create indexes (skipped - already created by migration 0001)
    # op.create_index("ix_alert_fired_severity", "alert_history", ["fired_at", "severity"])
    # op.create_index("ix_alert_group_fired", "alert_history", ["alert_group", "fired_at"])
    # op.create_index("ix_alert_unresolved", "alert_history", ["resolved_at", "acknowledged"])
    # op.create_index("ix_alert_name", "alert_history", ["alert_name"])


def downgrade() -> None:
    # No indexes were created in upgrade (all skipped)
    op.drop_table("alert_history")