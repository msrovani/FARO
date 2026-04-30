"""Add missing foreign key indexes for frequently joined columns

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-25

This migration adds indexes on foreign key columns that are frequently
used in JOIN operations but lack explicit indexes.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0022_missing_fk_indexes"
down_revision = "0021_data_retention_and_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes on frequently joined FK columns
    # Use IF NOT EXISTS to avoid errors if indexes already exist
    
    # SuspicionReport FKs
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_suspicionreport_observation_id
        ON suspicionreport (observation_id)
    """)
    
    # Alert FKs
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alert_observation_id
        ON alert (observation_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alert_suspicion_report_id
        ON alert (suspicion_report_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alert_triggered_by_rule_id
        ON alert (triggered_by_rule_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alert_triggered_manually_by
        ON alert (triggered_manually_by)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_alert_acknowledged_by
        ON alert (acknowledged_by)
    """)
    
    # WatchlistHit FKs
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_watchlisthit_observation_id
        ON watchlisthit (observation_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_watchlisthit_watchlist_entry_id
        ON watchlisthit (watchlist_entry_id)
    """)


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("ix_watchlisthit_watchlist_entry_id", table_name="watchlisthit")
    op.drop_index("ix_watchlisthit_observation_id", table_name="watchlisthit")
    
    op.drop_index("ix_alert_acknowledged_by", table_name="alert")
    op.drop_index("ix_alert_triggered_manually_by", table_name="alert")
    op.drop_index("ix_alert_triggered_by_rule_id", table_name="alert")
    op.drop_index("ix_alert_suspicion_report_id", table_name="alert")
    op.drop_index("ix_alert_observation_id", table_name="alert")
    
    op.drop_index("ix_suspicionreport_observation_id", table_name="suspicionreport")
