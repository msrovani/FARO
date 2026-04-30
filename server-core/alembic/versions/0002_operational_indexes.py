"""
Operational and geospatial indexes for FARO analytical workloads.

This migration is intentionally additive and idempotent (IF NOT EXISTS)
to support existing environments initialized from 0001.
"""
from __future__ import annotations

from alembic import op


revision = "0002_operational_indexes"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Geospatial indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vehicleobservation_location_gist
        ON vehicleobservation
        USING GIST (location)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_routepattern_centroid_location_gist
        ON routepattern
        USING GIST (centroid_location)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_routepattern_bounding_box_gist
        ON routepattern
        USING GIST (bounding_box)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_routepattern_corridor_gist
        ON routepattern
        USING GIST (corridor)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_routeregionofinterest_geometry_gist
        ON routeregionofinterest
        USING GIST (geometry)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sensitiveassetzone_geometry_gist
        ON sensitiveassetzone
        USING GIST (geometry)
        """
    )

    # Analytical access patterns
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_routeanomalyevent_plate_created_at
        ON routeanomalyevent (plate_number, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_convoyevent_primary_related_created_at
        ON convoyevent (primary_plate, related_plate, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_roamingevent_plate_created_at
        ON roamingevent (plate_number, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sensitiveassetrecurrenceevent_plate_zone_created_at
        ON sensitiveassetrecurrenceevent (plate_number, zone_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_algorithmrun_type_scope_status_created_at
        ON algorithmrun (algorithm_type, run_scope, status, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_algorithmexplanation_run_type
        ON algorithmexplanation (algorithm_run_id, algorithm_type)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_analystfeedbackevent_target_read_created_at
        ON analystfeedbackevent (target_user_id, read_at, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_auditlog_user_action_created_at
        ON auditlog (user_id, action, created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_auditlog_user_action_created_at")
    op.execute("DROP INDEX IF EXISTS ix_analystfeedbackevent_target_read_created_at")
    op.execute("DROP INDEX IF EXISTS ix_algorithmexplanation_run_type")
    op.execute("DROP INDEX IF EXISTS ix_algorithmrun_type_scope_status_created_at")
    op.execute("DROP INDEX IF EXISTS ix_sensitiveassetrecurrenceevent_plate_zone_created_at")
    op.execute("DROP INDEX IF EXISTS ix_roamingevent_plate_created_at")
    op.execute("DROP INDEX IF EXISTS ix_convoyevent_primary_related_created_at")
    op.execute("DROP INDEX IF EXISTS ix_routeanomalyevent_plate_created_at")
    op.execute("DROP INDEX IF EXISTS ix_sensitiveassetzone_geometry_gist")
    op.execute("DROP INDEX IF EXISTS ix_routeregionofinterest_geometry_gist")
    op.execute("DROP INDEX IF EXISTS ix_routepattern_corridor_gist")
    op.execute("DROP INDEX IF EXISTS ix_routepattern_bounding_box_gist")
    op.execute("DROP INDEX IF EXISTS ix_routepattern_centroid_location_gist")
    op.execute("DROP INDEX IF EXISTS ix_vehicleobservation_location_gist")
