"""Fix suspicionlevel enum type to use correct SuspicionLevel values

The suspicionlevel enum was incorrectly created with SuspicionReason values
instead of SuspicionLevel values. This migration fixes that.

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-20 00:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0017_fix_suspicionlevel_enum'
down_revision = '0016_fix_sync_status_enum'
branch_labels = None
depends_on = None


def upgrade():
    # First, convert both columns to VARCHAR to drop dependency on the enum type
    # suspicionreport.level
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN level DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN level TYPE VARCHAR(20) 
        USING level::text
    """)
    
    # intelligencereview.reclassified_level
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_level DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_level TYPE VARCHAR(20) 
        USING reclassified_level::text
    """)
    
    # Now drop the wrong enum type
    op.execute("DROP TYPE IF EXISTS suspicionlevel")
    
    # Create the correct enum type with SuspicionLevel values
    op.execute("CREATE TYPE suspicionlevel AS ENUM ('low', 'medium', 'high')")
    
    # Convert existing values in suspicionreport - map old SuspicionReason values to SuspicionLevel
    # Default to 'medium' for any unknown values
    op.execute("""
        UPDATE suspicionreport 
        SET level = CASE 
            WHEN level = 'stolen_vehicle' THEN 'high'
            WHEN level = 'suspicious_behavior' THEN 'medium'
            WHEN level = 'wanted_plate' THEN 'high'
            WHEN level = 'unusual_hours' THEN 'medium'
            WHEN level = 'known_associate' THEN 'medium'
            WHEN level = 'drug_trafficking' THEN 'high'
            WHEN level = 'weapons' THEN 'high'
            WHEN level = 'gang_activity' THEN 'high'
            WHEN level = 'other' THEN 'low'
            ELSE 'medium'
        END
    """)
    
    # Convert existing values in intelligencereview
    op.execute("""
        UPDATE intelligencereview 
        SET reclassified_level = CASE 
            WHEN reclassified_level = 'stolen_vehicle' THEN 'high'
            WHEN reclassified_level = 'suspicious_behavior' THEN 'medium'
            WHEN reclassified_level = 'wanted_plate' THEN 'high'
            WHEN reclassified_level = 'unusual_hours' THEN 'medium'
            WHEN reclassified_level = 'known_associate' THEN 'medium'
            WHEN reclassified_level = 'drug_trafficking' THEN 'high'
            WHEN reclassified_level = 'weapons' THEN 'high'
            WHEN reclassified_level = 'gang_activity' THEN 'high'
            WHEN reclassified_level = 'other' THEN 'low'
            ELSE 'medium'
        END
        WHERE reclassified_level IS NOT NULL
    """)
    
    # Alter columns back to enum with correct type
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN level TYPE suspicionlevel 
        USING level::text::suspicionlevel
    """)
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN level SET DEFAULT 'medium'::suspicionlevel")
    
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_level TYPE suspicionlevel 
        USING reclassified_level::text::suspicionlevel
    """)


def downgrade():
    # Revert the changes
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_level DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_level TYPE VARCHAR(20) 
        USING reclassified_level::text
    """)
    
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN level DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN level TYPE VARCHAR(20) 
        USING level::text
    """)
    
    # Drop the correct enum type
    op.execute("DROP TYPE IF EXISTS suspicionlevel")
    
    # Recreate the wrong enum type (for downgrade)
    op.execute("CREATE TYPE suspicionlevel AS ENUM ('stolen_vehicle', 'suspicious_behavior', 'wanted_plate', 'unusual_hours', 'known_associate', 'drug_trafficking', 'weapons', 'gang_activity', 'other')")
    
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN level TYPE suspicionlevel 
        USING level::text::suspicionlevel
    """)
    
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN level SET DEFAULT 'suspicious_behavior'::suspicionlevel")
