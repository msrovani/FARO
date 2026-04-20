"""
BRIN Index for vehicle_observations table.
Optimization Fase 2.2: BRIN index for time-ordered data.
BRIN (Block Range INdex) is much smaller than GiST for time-ordered data.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0007_brin_index_observations"
down_revision = "0006_agency_hierarchy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create BRIN index on observed_at_local for time-ordered queries
    # pages_per_range = 128 means each index entry covers 128 pages
    # This is optimal for time-series data that grows sequentially
    op.execute(
        sa.text(
            """
            CREATE INDEX ix_vehicleobservation_observed_at_local_brin
            ON vehicleobservation USING BRIN (observed_at_local)
            WITH (pages_per_range = 128);
            """
        )
    )

    # Create BRIN index on created_at for insertion order
    op.execute(
        sa.text(
            """
            CREATE INDEX ix_vehicleobservation_created_at_brin
            ON vehicleobservation USING BRIN (created_at)
            WITH (pages_per_range = 128);
            """
        )
    )


def downgrade() -> None:
    # Drop BRIN indexes
    op.drop_index(
        "ix_vehicleobservation_observed_at_local_brin",
        table_name="vehicleobservation",
    )
    op.drop_index(
        "ix_vehicleobservation_created_at_brin",
        table_name="vehicleobservation",
    )
