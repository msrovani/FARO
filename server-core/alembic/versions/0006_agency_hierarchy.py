"""
Agency hierarchy for BI Institutional Dashboard.
Adds type (local/regional/central) and parent_agency fields to support multi-level intelligence organization.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0006_agency_hierarchy"
down_revision = "0005_advanced_convoy_roaming"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agencytype enum
    agencytype_enum = postgresql.ENUM(
        "local",
        "regional",
        "central",
        name="agencytype",
        create_type=True,
    )
    agencytype_enum.create(op.get_bind())

    # Add type column to agency
    op.add_column(
        "agency",
        sa.Column(
            "type",
            agencytype_enum,
            nullable=False,
            server_default="local",
        ),
    )

    # Add parent_agency_id column to agency
    op.add_column(
        "agency",
        sa.Column(
            "parent_agency_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Create index on parent_agency_id
    op.create_index(
        "ix_agency_parent_agency_id",
        "agency",
        ["parent_agency_id"],
        unique=False,
    )

    # Create foreign key constraint
    op.create_foreign_key(
        "fk_agency_parent_agency_id",
        "agency",
        "agency",
        ["parent_agency_id"],
        ["id"],
    )

    # Set default values for existing agencies
    op.execute(
        sa.text(
            """
            UPDATE agency
            SET type = 'local'
            WHERE type IS NULL
            """
        )
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_agency_parent_agency_id",
        "agency",
        type_="foreignkey",
    )

    # Drop index
    op.drop_index(
        "ix_agency_parent_agency_id",
        table_name="agency",
    )

    # Drop columns
    op.drop_column("agency", "parent_agency_id")
    op.drop_column("agency", "type")

    # Drop enum
    agencytype_enum = postgresql.ENUM(
        "local",
        "regional",
        "central",
        name="agencytype",
    )
    agencytype_enum.drop(op.get_bind())
