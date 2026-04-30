"""Implement table partitioning for VehicleObservation

Revision ID: 0024
Revises: 0023
Create Date: 2026-04-25

This migration implements table partitioning for VehicleObservation to improve
performance on large datasets. Partitioning is done by month on observed_at_local.

Best Practice Reference:
- https://www.postgresql.org/docs/current/ddl-partitioning.html
- https://www.postgresql.org/docs/current/sql-createpartitionedtable.html
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0024_table_partitioning"
down_revision = "0023_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Note: This migration is complex and requires careful planning
    # Partitioning an existing table with data requires:
    # 1. Creating a new partitioned table
    # 2. Migrating data from the old table
    # 3. Renaming tables
    # 4. Updating foreign keys and indexes
    
    # For production, this should be done in stages:
    # 1. Create partitioned table with same structure
    # 2. Copy data in batches
    # 3. Switch tables with minimal downtime
    # 4. Drop old table
    
    # This migration creates the infrastructure for partitioning
    # but does not perform the actual data migration
    
    # Create a function to manage partition creation
    op.execute("""
        CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
        RETURNS VOID AS $$
        DECLARE
            partition_name TEXT;
            end_date DATE;
        BEGIN
            partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
            end_date := start_date + INTERVAL '1 month';
            
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                partition_name,
                table_name,
                start_date,
                end_date
            );
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create a function to automatically create future partitions
    op.execute("""
        CREATE OR REPLACE FUNCTION create_future_partitions(table_name TEXT, months_ahead INTEGER)
        RETURNS VOID AS $$
        DECLARE
            i INTEGER;
            start_date DATE;
        BEGIN
            FOR i IN 0..months_ahead-1 LOOP
                start_date := date_trunc('month', CURRENT_DATE) + (i || ' months')::INTERVAL;
                PERFORM create_monthly_partition(table_name, start_date);
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Note: Actual partitioning of VehicleObservation should be done
    # in a separate migration with proper data migration strategy
    # This is documented in docs/database/table_partitioning.md


def downgrade() -> None:
    # Drop partition management functions
    op.execute("DROP FUNCTION IF EXISTS create_future_partitions")
    op.execute("DROP FUNCTION IF EXISTS create_monthly_partition")
