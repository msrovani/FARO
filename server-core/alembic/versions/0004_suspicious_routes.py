"""
Suspicious Routes - Manual route registration for intelligence analysis.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0004_suspicious_routes"
down_revision = "0003_multi_tenant_agency_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verificar se os enums já existem antes de criá-los
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_types = inspector.get_enums()
    existing_type_names = [e['name'] for e in existing_types]
    
    if 'crimetype' not in existing_type_names:
        op.execute("CREATE TYPE crimetype AS ENUM ('drug_trafficking', 'contraband', 'escape', 'weapons_trafficking', 'kidnapping', 'car_theft', 'stolen_vehicle', 'gang_activity', 'human_trafficking', 'money_laundering', 'other')")
    if 'routedirection' not in existing_type_names:
        op.execute("CREATE TYPE routedirection AS ENUM ('inbound', 'outbound', 'bidirectional')")
    if 'risklevel' not in existing_type_names:
        op.execute("CREATE TYPE risklevel AS ENUM ('low', 'medium', 'high', 'critical')")
    
    # Verificar se a tabela suspiciousroute já existe
    if "suspiciousroute" not in inspector.get_table_names():
        # Create suspicious routes table
        op.create_table(
            "suspiciousroute",
            sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("crime_type", sa.Enum(name="crimetype", create_constraint=True), nullable=False),
            sa.Column("direction", sa.Enum(name="routedirection", create_constraint=True), nullable=False),
            sa.Column("risk_level", sa.Enum(name="risklevel", create_constraint=True), nullable=False),
            sa.Column("route_geometry", sa.Geometry("LINESTRING", srid=4326), nullable=False),
            sa.Column("buffer_distance_meters", sa.Float(), nullable=True),
            sa.Column("active_from_hour", sa.Integer(), nullable=True),
            sa.Column("active_to_hour", sa.Integer(), nullable=True),
            sa.Column("active_days", postgresql.ARRAY(sa.Integer()), nullable=True),
            sa.Column("justification", sa.Text(), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="pending"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["agency_id"], "agency", ["id"]),
            sa.ForeignKeyConstraint(["created_by"], "user", ["id"]),
            sa.ForeignKeyConstraint(["approved_by"], "user", ["id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    
    # Create indexes se não existirem
    if "suspiciousroute" in inspector.get_table_names():
        suspiciousroute_indexes = [idx['name'] for idx in inspector.get_indexes('suspiciousroute')]
        if 'ix_suspiciousroute_agency_id' not in suspiciousroute_indexes:
            op.create_index("ix_suspiciousroute_agency_id", "suspiciousroute", ["agency_id"])
        if 'ix_suspiciousroute_name' not in suspiciousroute_indexes:
            op.create_index("ix_suspiciousroute_name", "suspiciousroute", ["name"])
        if 'ix_suspiciousroute_agency_active' not in suspiciousroute_indexes:
            op.create_index("ix_suspiciousroute_agency_active", "suspiciousroute", ["agency_id", "is_active"])
        if 'ix_suspiciousroute_crime_type' not in suspiciousroute_indexes:
            op.create_index("ix_suspiciousroute_crime_type", "suspiciousroute", ["crime_type"])
        
        # Create GiST index on route_geometry for spatial queries
        if 'ix_suspiciousroute_route_geometry' not in suspiciousroute_indexes:
            op.execute("CREATE INDEX ix_suspiciousroute_route_geometry ON suspiciousroute USING GIST (route_geometry)")


def downgrade() -> None:
    op.drop_index("ix_suspiciousroute_route_geometry", table_name="suspiciousroute")
    op.drop_index("ix_suspiciousroute_crime_type", table_name="suspiciousroute")
    op.drop_index("ix_suspiciousroute_agency_active", table_name="suspiciousroute")
    op.drop_index("ix_suspiciousroute_name", table_name="suspiciousroute")
    op.drop_index("ix_suspiciousroute_agency_id", table_name="suspiciousroute")
    op.drop_table("suspiciousroute")
    op.execute("DROP TYPE risklevel")
    op.execute("DROP TYPE routedirection")
    op.execute("DROP TYPE crimetype")
