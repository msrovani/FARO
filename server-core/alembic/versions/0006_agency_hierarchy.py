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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Verificar se o enum agencytype já existe
    existing_types = inspector.get_enums()
    existing_type_names = [e['name'] for e in existing_types]
    
    if 'agencytype' not in existing_type_names:
        # Create agencytype enum
        agencytype_enum = postgresql.ENUM(
            "local",
            "regional",
            "central",
            name="agencytype",
            create_type=True,
        )
        agencytype_enum.create(op.get_bind())

    # Verificar colunas da tabela agency
    agency_columns = [col['name'] for col in inspector.get_columns('agency')]
    
    # Add type column to agency se não existir
    if 'type' not in agency_columns:
        op.add_column(
            "agency",
            sa.Column(
                "type",
                postgresql.ENUM(name="agencytype", create_constraint=True),
                nullable=True,  # Temporariamente nullable para evitar erro
            ),
        )
        op.execute("UPDATE agency SET type = 'local' WHERE type IS NULL")
        op.alter_column("agency", "type", nullable=False)

    # Add parent_agency_id column to agency se não existir
    if 'parent_agency_id' not in agency_columns:
        op.add_column(
            "agency",
            sa.Column(
                "parent_agency_id",
                postgresql.UUID(as_uuid=True),
                nullable=True,
            ),
        )

    # Create index on parent_agency_id se não existir
    agency_indexes = [idx['name'] for idx in inspector.get_indexes('agency')]
    if 'ix_agency_parent_agency_id' not in agency_indexes:
        op.create_index(
            "ix_agency_parent_agency_id",
            "agency",
            ["parent_agency_id"],
            unique=False,
        )

    # Create foreign key constraint se não existir
    # Verificar se o constraint já existe
    existing_constraints = [c['name'] for c in inspector.get_foreign_keys('agency')]
    if 'fk_agency_parent_agency' not in existing_constraints:
        op.create_foreign_key(
            "fk_agency_parent_agency",
            "agency",
            "agency",
            ["parent_agency_id"],
            ["id"],
        )

    # Set default values for existing agencies
    # Não necessário pois migration 0001 já cria com valor default


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
