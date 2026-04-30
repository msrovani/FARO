"""
Advanced Convoy and Roaming Analysis - Enhanced models for pattern detection.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0005_advanced_convoy_roaming"
down_revision = "0004_suspicious_routes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Add advanced columns to convoyevent
    convoyevent_columns = [col['name'] for col in inspector.get_columns('convoyevent')]
    if 'convoy_id' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("convoy_id", postgresql.UUID(as_uuid=True), nullable=True))
    if 'convoy_size' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("convoy_size", sa.Integer(), nullable=True))
    if 'spatial_proximity_meters' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("spatial_proximity_meters", sa.Float(), nullable=True))
    if 'temporal_window_minutes' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("temporal_window_minutes", sa.Integer(), nullable=True))
    if 'route_similarity' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("route_similarity", sa.Float(), nullable=True))
    if 'common_hours' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("common_hours", postgresql.ARRAY(sa.Integer()), nullable=True))
    if 'common_days' not in convoyevent_columns:
        op.add_column("convoyevent", sa.Column("common_days", postgresql.ARRAY(sa.Integer()), nullable=True))
    
    # Create indexes for convoyevent
    convoyevent_indexes = [idx['name'] for idx in inspector.get_indexes('convoyevent')]
    if 'ix_convoy_convoy_id' not in convoyevent_indexes:
        op.create_index("ix_convoy_convoy_id", "convoyevent", ["convoy_id"])
    if 'ix_convoy_primary_related' not in convoyevent_indexes:
        op.create_index("ix_convoy_primary_related", "convoyevent", ["primary_plate", "related_plate"])
    
    # Add advanced columns to roamingevent
    roamingevent_columns = [col['name'] for col in inspector.get_columns('roamingevent')]
    if 'roaming_id' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("roaming_id", postgresql.UUID(as_uuid=True), nullable=True))
    if 'area_geometry' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("area_geometry", sa.Geometry("POLYGON", srid=4326), nullable=True))
    if 'area_size_km2' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("area_size_km2", sa.Float(), nullable=True))
    if 'average_stay_minutes' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("average_stay_minutes", sa.Float(), nullable=True))
    if 'total_observations' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("total_observations", sa.Integer(), nullable=True))
    if 'first_seen' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True))
    if 'last_seen' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True))
    if 'common_hours' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("common_hours", postgresql.ARRAY(sa.Integer()), nullable=True))
    if 'common_days' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("common_days", postgresql.ARRAY(sa.Integer()), nullable=True))
    if 'zone_type' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("zone_type", sa.String(length=100), nullable=True))
    if 'zone_risk_level' not in roamingevent_columns:
        op.add_column("roamingevent", sa.Column("zone_risk_level", sa.String(length=50), nullable=True))
    
    # Create indexes for roamingevent
    roamingevent_indexes = [idx['name'] for idx in inspector.get_indexes('roamingevent')]
    if 'ix_roaming_roaming_id' not in roamingevent_indexes:
        op.create_index("ix_roaming_roaming_id", "roamingevent", ["roaming_id"])
    if 'ix_roaming_plate_area' not in roamingevent_indexes:
        op.create_index("ix_roaming_plate_area", "roamingevent", ["plate_number", "area_label"])
    
    # Create GiST index on roamingevent area_geometry
    if 'ix_roaming_area_geometry' not in roamingevent_indexes:
        op.execute("CREATE INDEX ix_roaming_area_geometry ON roamingevent USING GIST (area_geometry)")


def downgrade() -> None:
    op.drop_index("ix_roaming_area_geometry", table_name="roamingevent")
    op.drop_index("ix_roaming_plate_area", table_name="roamingevent")
    op.drop_index("ix_roaming_roaming_id", table_name="roamingevent")
    
    op.drop_column("roamingevent", "zone_risk_level")
    op.drop_column("roamingevent", "zone_type")
    op.drop_column("roamingevent", "common_days")
    op.drop_column("roamingevent", "common_hours")
    op.drop_column("roamingevent", "last_seen")
    op.drop_column("roamingevent", "first_seen")
    op.drop_column("roamingevent", "total_observations")
    op.drop_column("roamingevent", "average_stay_minutes")
    op.drop_column("roamingevent", "area_size_km2")
    op.drop_column("roamingevent", "area_geometry")
    op.drop_column("roamingevent", "roaming_id")
    
    op.drop_index("ix_convoy_primary_related", table_name="convoyevent")
    op.drop_index("ix_convoy_convoy_id", table_name="convoyevent")
    
    op.drop_column("convoyevent", "common_days")
    op.drop_column("convoyevent", "common_hours")
    op.drop_column("convoyevent", "route_similarity")
    op.drop_column("convoyevent", "temporal_window_minutes")
    op.drop_column("convoyevent", "spatial_proximity_meters")
    op.drop_column("convoyevent", "convoy_size")
    op.drop_column("convoyevent", "convoy_id")
