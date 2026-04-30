"""Enable pg_stat_statements for query performance monitoring

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-22

This migration enables the pg_stat_statements extension to track
query performance statistics, which is essential for:
- Identifying slow queries
- Monitoring database performance
- Optimizing SQL queries
- Understanding query patterns

Best Practice Reference:
- https://www.crunchydata.com/blog/postgis-performance-postgres-tuning
- https://www.postgresql.org/docs/current/pgstatstatements.html
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0020_pg_stat_statements'
down_revision = '0019_spatial_gin_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable pg_stat_statements extension for query performance monitoring."""
    # Enable pg_stat_statements extension
    # Note: This requires superuser privileges
    # The extension should be loaded via shared_preload_libraries in postgresql.conf
    # If this fails, ensure postgresql.conf contains: shared_preload_libraries = 'pg_stat_statements'
    # Then restart PostgreSQL and run this migration again
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
    except Exception as e:
        # Log the error but don't fail the migration
        # The extension can be enabled manually by the DBA
        print(f"Warning: Could not enable pg_stat_statements: {e}")
        print("To enable manually: 1) Add 'shared_preload_libraries = pg_stat_statements' to postgresql.conf")
        print("2) Restart PostgreSQL")
        print("3) Run: CREATE EXTENSION pg_stat_statements;")


def downgrade() -> None:
    """Disable pg_stat_statements extension."""
    try:
        op.execute('DROP EXTENSION IF EXISTS pg_stat_statements')
    except Exception as e:
        print(f"Warning: Could not drop pg_stat_statements: {e}")
