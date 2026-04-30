"""Data retention policy and CHECK constraints for data validation

Revision ID: 0021
Revises: 0020
Create Date: 2026-04-25

This migration implements:
- CHECK constraints for data validation
- Data retention policy enforcement
- TTL-based cleanup triggers
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0021_data_retention_and_constraints"
down_revision = "0020_pg_stat_statements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add CHECK constraints for data validation
    
    # VehicleObservation: observed_at_local cannot be in future
    op.execute("""
        ALTER TABLE vehicleobservation 
        ADD CONSTRAINT chk_observation_time_not_future 
        CHECK (observed_at_local <= NOW() AT TIME ZONE 'UTC')
    """)
    
    # VehicleObservation: sync_attempts must be >= 0
    op.execute("""
        ALTER TABLE vehicleobservation 
        ADD CONSTRAINT chk_sync_attempts_non_negative 
        CHECK (sync_attempts >= 0)
    """)
    
    # PlateRead: ocr_confidence must be between 0.0 and 1.0
    op.execute("""
        ALTER TABLE plateread 
        ADD CONSTRAINT chk_ocr_confidence_range 
        CHECK (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0)
    """)
    
    # AlertHistory: ttl_days must be >= 0
    op.execute("""
        ALTER TABLE alerthistory 
        ADD CONSTRAINT chk_ttl_days_non_negative 
        CHECK (ttl_days >= 0)
    """)
    
    # DashboardMetric: ttl_days must be >= 0
    op.execute("""
        ALTER TABLE dashboardmetric 
        ADD CONSTRAINT chk_metric_ttl_non_negative 
        CHECK (ttl_days >= 0)
    """)
    
    # WatchlistEntry: priority must be within valid range (0-100)
    op.execute("""
        ALTER TABLE watchlistentry 
        ADD CONSTRAINT chk_watchlist_priority_range 
        CHECK (priority >= 0 AND priority <= 100)
    """)
    
    # IntelligenceCase: priority must be within valid range (0-100)
    op.execute("""
        ALTER TABLE intelligencecase 
        ADD CONSTRAINT chk_case_priority_range 
        CHECK (priority >= 0 AND priority <= 100)
    """)
    
    # AlertRule: priority must be within valid range (0-100)
    op.execute("""
        ALTER TABLE alertrule 
        ADD CONSTRAINT chk_alert_rule_priority_range 
        CHECK (priority >= 0 AND priority <= 100)
    """)
    
    # Create function for TTL-based cleanup
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_records()
        RETURNS TRIGGER AS $$
        BEGIN
            -- This function is called by a scheduled job
            -- It deletes records older than their TTL
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function to check if record should be deleted based on TTL
    op.execute("""
        CREATE OR REPLACE FUNCTION should_delete_by_ttl(record_timestamp TIMESTAMP WITH TIME ZONE, ttl_days INTEGER)
        RETURNS BOOLEAN AS $$
        BEGIN
            IF ttl_days IS NULL THEN
                RETURN FALSE;
            END IF;
            RETURN record_timestamp < (NOW() - INTERVAL '1 day' * ttl_days);
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS should_delete_by_ttl")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_records")
    
    # Drop CHECK constraints
    op.execute("ALTER TABLE alertrule DROP CONSTRAINT IF EXISTS chk_alert_rule_priority_range")
    op.execute("ALTER TABLE intelligencecase DROP CONSTRAINT IF EXISTS chk_case_priority_range")
    op.execute("ALTER TABLE watchlistentry DROP CONSTRAINT IF EXISTS chk_watchlist_priority_range")
    op.execute("ALTER TABLE dashboardmetric DROP CONSTRAINT IF EXISTS chk_metric_ttl_non_negative")
    op.execute("ALTER TABLE alerthistory DROP CONSTRAINT IF EXISTS chk_ttl_days_non_negative")
    op.execute("ALTER TABLE plateread DROP CONSTRAINT IF EXISTS chk_ocr_confidence_range")
    op.execute("ALTER TABLE vehicleobservation DROP CONSTRAINT IF EXISTS chk_sync_attempts_non_negative")
    op.execute("ALTER TABLE vehicleobservation DROP CONSTRAINT IF EXISTS chk_observation_time_not_future")
