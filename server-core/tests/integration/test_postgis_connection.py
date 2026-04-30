import os

import asyncpg
import pytest


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_postgis_available_and_schema_migrated() -> None:
    if os.getenv("RUN_DB_TESTS", "false").lower() != "true":
        pytest.skip("RUN_DB_TESTS nao habilitado para este ambiente.")

    database_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://faro:faro_secret@localhost:5432/faro_db",
    )
    conn = await asyncpg.connect(database_url)
    try:
        postgis_version = await conn.fetchval("SELECT PostGIS_Version();")
        assert postgis_version is not None

        alembic_exists = await conn.fetchval(
            """
            SELECT EXISTS (
              SELECT 1
              FROM information_schema.tables
              WHERE table_schema = 'public' AND table_name = 'alembic_version'
            );
            """
        )
        assert alembic_exists is True
    finally:
        await conn.close()
