"""
Multi-tenant foundation for FARO: agency table and agency scoping columns.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_multi_tenant_agency_scope"
down_revision = "0002_operational_indexes"
branch_labels = None
depends_on = None


BOOTSTRAP_AGENCY_ID = "11111111-1111-1111-1111-111111111111"


def upgrade() -> None:
    # Criar tabela agency manualmente com schema correto (sem type e parent_agency_id)
    # Essas colunas serão adicionadas nas migrations 0006 e posteriores
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if "agency" not in inspector.get_table_names():
        op.create_table(
            "agency",
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_agency_code", "agency", ["code"], unique=True)
        op.create_index("ix_agency_name", "agency", ["name"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO agency (id, name, code, is_active)
            VALUES (:id, 'Agencia Padrao FARO', 'FARO-DEFAULT', true)
            ON CONFLICT (code) DO NOTHING
            """
        ).bindparams(id=BOOTSTRAP_AGENCY_ID)
    )

    # users
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    user_columns = [col['name'] for col in inspector.get_columns('user')]
    
    if 'agency_id' not in user_columns:
        op.add_column("user", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(sa.text("UPDATE \"user\" SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("user", "agency_id", nullable=False)
        op.create_index("ix_user_agency_id", "user", ["agency_id"], unique=False)
        op.create_foreign_key("fk_user_agency_id", "user", "agency", ["agency_id"], ["id"])

    # units
    unit_columns = [col['name'] for col in inspector.get_columns('unit')]
    if 'agency_id' not in unit_columns:
        op.add_column("unit", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(sa.text("UPDATE unit SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("unit", "agency_id", nullable=False)
        op.create_index("ix_unit_agency_id", "unit", ["agency_id"], unique=False)
        op.create_foreign_key("fk_unit_agency_id", "unit", "agency", ["agency_id"], ["id"])
        op.create_unique_constraint("uq_unit_agency_code", "unit", ["agency_id", "code"])
        op.execute("ALTER TABLE unit DROP CONSTRAINT IF EXISTS unit_code_key")

    # device
    device_columns = [col['name'] for col in inspector.get_columns('device')]
    if 'agency_id' not in device_columns:
        op.add_column("device", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE device d
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE d.user_id = u.id AND d.agency_id IS NULL
                """
            )
        )
        op.execute(sa.text("UPDATE device SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("device", "agency_id", nullable=False)
        op.create_index("ix_device_agency_id", "device", ["agency_id"], unique=False)
        op.create_foreign_key("fk_device_agency_id", "device", "agency", ["agency_id"], ["id"])
        op.execute("ALTER TABLE device DROP CONSTRAINT IF EXISTS device_device_id_key")
        op.create_unique_constraint("uq_device_user_device_id", "device", ["user_id", "device_id"])

    # vehicle observation
    vehicleobservation_columns = [col['name'] for col in inspector.get_columns('vehicleobservation')]
    if 'agency_id' not in vehicleobservation_columns:
        op.add_column("vehicleobservation", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE vehicleobservation vo
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE vo.agent_id = u.id AND vo.agency_id IS NULL
                """
            )
        )
        op.execute(
            sa.text("UPDATE vehicleobservation SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID)
        )
        op.alter_column("vehicleobservation", "agency_id", nullable=False)
        op.create_index("ix_vehicleobservation_agency_id", "vehicleobservation", ["agency_id"], unique=False)
        op.create_index(
            "ix_observation_agency_plate_time",
            "vehicleobservation",
            ["agency_id", "plate_number", "observed_at_local"],
            unique=False,
        )
        op.create_foreign_key("fk_vehicleobservation_agency_id", "vehicleobservation", "agency", ["agency_id"], ["id"])

    # route patterns
    routepattern_columns = [col['name'] for col in inspector.get_columns('routepattern')]
    if 'agency_id' not in routepattern_columns:
        op.add_column("routepattern", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(sa.text("UPDATE routepattern SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("routepattern", "agency_id", nullable=False)
        op.create_index("ix_routepattern_agency_id", "routepattern", ["agency_id"], unique=False)
        op.drop_index("ix_route_pattern_plate", table_name="routepattern")
        op.create_index("ix_route_pattern_plate", "routepattern", ["agency_id", "plate_number"], unique=False)
        op.create_foreign_key("fk_routepattern_agency_id", "routepattern", "agency", ["agency_id"], ["id"])

    # watchlist
    watchlistentry_columns = [col['name'] for col in inspector.get_columns('watchlistentry')]
    if 'agency_id' not in watchlistentry_columns:
        op.add_column("watchlistentry", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE watchlistentry we
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE we.created_by = u.id AND we.agency_id IS NULL
                """
            )
        )
        op.execute(sa.text("UPDATE watchlistentry SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("watchlistentry", "agency_id", nullable=False)
        op.create_index("ix_watchlistentry_agency_id", "watchlistentry", ["agency_id"], unique=False)
        op.drop_index("ix_watchlist_status_priority", table_name="watchlistentry")
        op.drop_index("ix_watchlist_plate_status", table_name="watchlistentry")
        op.create_index(
            "ix_watchlist_status_priority",
            "watchlistentry",
            ["agency_id", "status", "priority"],
            unique=False,
        )
        op.create_index(
            "ix_watchlist_plate_status",
            "watchlistentry",
            ["agency_id", "plate_number", "status"],
            unique=False,
        )
        op.create_foreign_key("fk_watchlistentry_agency_id", "watchlistentry", "agency", ["agency_id"], ["id"])

    # route regions
    routeregionofinterest_columns = [col['name'] for col in inspector.get_columns('routeregionofinterest')]
    if 'agency_id' not in routeregionofinterest_columns:
        op.add_column("routeregionofinterest", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text("UPDATE routeregionofinterest SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID)
        )
        op.alter_column("routeregionofinterest", "agency_id", nullable=False)
        op.create_index("ix_routeregionofinterest_agency_id", "routeregionofinterest", ["agency_id"], unique=False)
        op.create_foreign_key(
            "fk_routeregionofinterest_agency_id",
            "routeregionofinterest",
            "agency",
            ["agency_id"],
            ["id"],
        )

    # sensitive zones
    sensitiveassetzone_columns = [col['name'] for col in inspector.get_columns('sensitiveassetzone')]
    if 'agency_id' not in sensitiveassetzone_columns:
        op.add_column("sensitiveassetzone", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text("UPDATE sensitiveassetzone SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID)
        )
        op.alter_column("sensitiveassetzone", "agency_id", nullable=False)
        op.create_index("ix_sensitiveassetzone_agency_id", "sensitiveassetzone", ["agency_id"], unique=False)
        op.create_foreign_key("fk_sensitiveassetzone_agency_id", "sensitiveassetzone", "agency", ["agency_id"], ["id"])

    # intelligence case
    intelligencecase_columns = [col['name'] for col in inspector.get_columns('intelligencecase')]
    if 'agency_id' not in intelligencecase_columns:
        op.add_column("intelligencecase", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE intelligencecase ic
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE ic.created_by = u.id AND ic.agency_id IS NULL
                """
            )
        )
        op.execute(sa.text("UPDATE intelligencecase SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID))
        op.alter_column("intelligencecase", "agency_id", nullable=False)
        op.create_index("ix_intelligencecase_agency_id", "intelligencecase", ["agency_id"], unique=False)
        op.create_foreign_key("fk_intelligencecase_agency_id", "intelligencecase", "agency", ["agency_id"], ["id"])

    # feedback template
    analystfeedbacktemplate_columns = [col['name'] for col in inspector.get_columns('analystfeedbacktemplate')]
    if 'agency_id' not in analystfeedbacktemplate_columns:
        op.add_column("analystfeedbacktemplate", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE analystfeedbacktemplate aft
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE aft.created_by = u.id AND aft.agency_id IS NULL
                """
            )
        )
        op.execute(
            sa.text("UPDATE analystfeedbacktemplate SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID)
        )
        op.alter_column("analystfeedbacktemplate", "agency_id", nullable=False)
        op.create_index("ix_analystfeedbacktemplate_agency_id", "analystfeedbacktemplate", ["agency_id"], unique=False)
        op.create_foreign_key(
            "fk_analystfeedbacktemplate_agency_id",
            "analystfeedbacktemplate",
            "agency",
            ["agency_id"],
            ["id"],
        )

    # feedback event
    analystfeedbackevent_columns = [col['name'] for col in inspector.get_columns('analystfeedbackevent')]
    if 'agency_id' not in analystfeedbackevent_columns:
        op.add_column("analystfeedbackevent", sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.execute(
            sa.text(
                """
                UPDATE analystfeedbackevent afe
                SET agency_id = u.agency_id
                FROM "user" u
                WHERE afe.analyst_id = u.id AND afe.agency_id IS NULL
                """
            )
        )
        op.execute(
            sa.text("UPDATE analystfeedbackevent SET agency_id = :id WHERE agency_id IS NULL").bindparams(id=BOOTSTRAP_AGENCY_ID)
        )
        op.alter_column("analystfeedbackevent", "agency_id", nullable=False)
        op.create_index("ix_analystfeedbackevent_agency_id", "analystfeedbackevent", ["agency_id"], unique=False)
        op.create_foreign_key("fk_analystfeedbackevent_agency_id", "analystfeedbackevent", "agency", ["agency_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_analystfeedbackevent_agency_id", "analystfeedbackevent", type_="foreignkey")
    op.drop_index("ix_analystfeedbackevent_agency_id", table_name="analystfeedbackevent")
    op.drop_column("analystfeedbackevent", "agency_id")

    op.drop_constraint("fk_analystfeedbacktemplate_agency_id", "analystfeedbacktemplate", type_="foreignkey")
    op.drop_index("ix_analystfeedbacktemplate_agency_id", table_name="analystfeedbacktemplate")
    op.drop_column("analystfeedbacktemplate", "agency_id")

    op.drop_constraint("fk_intelligencecase_agency_id", "intelligencecase", type_="foreignkey")
    op.drop_index("ix_intelligencecase_agency_id", table_name="intelligencecase")
    op.drop_column("intelligencecase", "agency_id")

    op.drop_constraint("fk_sensitiveassetzone_agency_id", "sensitiveassetzone", type_="foreignkey")
    op.drop_index("ix_sensitiveassetzone_agency_id", table_name="sensitiveassetzone")
    op.drop_column("sensitiveassetzone", "agency_id")

    op.drop_constraint("fk_routeregionofinterest_agency_id", "routeregionofinterest", type_="foreignkey")
    op.drop_index("ix_routeregionofinterest_agency_id", table_name="routeregionofinterest")
    op.drop_column("routeregionofinterest", "agency_id")

    op.drop_constraint("fk_watchlistentry_agency_id", "watchlistentry", type_="foreignkey")
    op.drop_index("ix_watchlist_status_priority", table_name="watchlistentry")
    op.drop_index("ix_watchlist_plate_status", table_name="watchlistentry")
    op.create_index("ix_watchlist_plate_status", "watchlistentry", ["plate_number", "status"], unique=False)
    op.create_index("ix_watchlist_status_priority", "watchlistentry", ["status", "priority"], unique=False)
    op.drop_index("ix_watchlistentry_agency_id", table_name="watchlistentry")
    op.drop_column("watchlistentry", "agency_id")

    op.drop_constraint("fk_vehicleobservation_agency_id", "vehicleobservation", type_="foreignkey")
    op.drop_index("ix_observation_agency_plate_time", table_name="vehicleobservation")
    op.drop_index("ix_vehicleobservation_agency_id", table_name="vehicleobservation")
    op.drop_column("vehicleobservation", "agency_id")

    op.drop_constraint("fk_routepattern_agency_id", "routepattern", type_="foreignkey")
    op.drop_index("ix_route_pattern_plate", table_name="routepattern")
    op.create_index("ix_route_pattern_plate", "routepattern", ["plate_number"], unique=False)
    op.drop_index("ix_routepattern_agency_id", table_name="routepattern")
    op.drop_column("routepattern", "agency_id")

    op.drop_constraint("fk_device_agency_id", "device", type_="foreignkey")
    op.drop_constraint("uq_device_user_device_id", "device", type_="unique")
    op.execute("ALTER TABLE device ADD CONSTRAINT device_device_id_key UNIQUE (device_id)")
    op.drop_index("ix_device_agency_id", table_name="device")
    op.drop_column("device", "agency_id")

    op.execute("ALTER TABLE unit ADD CONSTRAINT unit_code_key UNIQUE (code)")
    op.drop_constraint("uq_unit_agency_code", "unit", type_="unique")
    op.drop_constraint("fk_unit_agency_id", "unit", type_="foreignkey")
    op.drop_index("ix_unit_agency_id", table_name="unit")
    op.drop_column("unit", "agency_id")

    op.drop_constraint("fk_user_agency_id", "user", type_="foreignkey")
    op.drop_index("ix_user_agency_id", table_name="user")
    op.drop_column("user", "agency_id")

    op.drop_index("ix_agency_name", table_name="agency")
    op.drop_index("ix_agency_code", table_name="agency")
    op.drop_table("agency")
