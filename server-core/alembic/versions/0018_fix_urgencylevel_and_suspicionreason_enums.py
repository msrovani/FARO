"""Fix urgencylevel and suspicionreason enums to use lowercase values

The urgencylevel and suspicionreason enums were created with uppercase values
but the Python enums use lowercase values. This migration fixes that.

Revision ID: 0018_fix_enum_lowercase
Revises: 0017_fix_suspicionlevel_enum
Create Date: 2026-04-20 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0018_fix_enum_lowercase'
down_revision = '0017_fix_suspicionlevel_enum'
branch_labels = None
depends_on = None


def upgrade():
    # Fix urgencylevel enum
    # Convert suspicionreport.urgency to VARCHAR
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN urgency DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN urgency TYPE VARCHAR(20) 
        USING urgency::text
    """)
    
    # Convert intelligencereview.reclassified_urgency to VARCHAR
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_urgency DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_urgency TYPE VARCHAR(20) 
        USING reclassified_urgency::text
    """)
    
    # Drop the old enum type
    op.execute("DROP TYPE IF EXISTS urgencylevel")
    
    # Create the new enum type with lowercase values
    op.execute("CREATE TYPE urgencylevel AS ENUM ('monitor', 'intelligence', 'approach')")
    
    # Convert existing values from uppercase to lowercase in suspicionreport
    op.execute("""
        UPDATE suspicionreport 
        SET urgency = CASE 
            WHEN urgency = 'MONITOR' THEN 'monitor'
            WHEN urgency = 'INTELLIGENCE' THEN 'intelligence'
            WHEN urgency = 'APPROACH' THEN 'approach'
            ELSE 'intelligence'
        END
    """)
    
    # Convert existing values from uppercase to lowercase in intelligencereview
    op.execute("""
        UPDATE intelligencereview 
        SET reclassified_urgency = CASE 
            WHEN reclassified_urgency = 'MONITOR' THEN 'monitor'
            WHEN reclassified_urgency = 'INTELLIGENCE' THEN 'intelligence'
            WHEN reclassified_urgency = 'APPROACH' THEN 'approach'
            ELSE 'intelligence'
        END
        WHERE reclassified_urgency IS NOT NULL
    """)
    
    # Alter suspicionreport.urgency back to enum with correct type
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN urgency TYPE urgencylevel 
        USING urgency::text::urgencylevel
    """)
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN urgency SET DEFAULT 'intelligence'::urgencylevel")
    
    # Alter intelligencereview.reclassified_urgency back to enum with correct type
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_urgency TYPE urgencylevel 
        USING CASE WHEN reclassified_urgency IS NOT NULL THEN reclassified_urgency::text::urgencylevel ELSE NULL END
    """)
    
    # Fix suspicionreason enum
    # Convert suspicionreport.reason to VARCHAR
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN reason DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN reason TYPE VARCHAR(50) 
        USING reason::text
    """)
    
    # Convert intelligencereview.reclassified_reason to VARCHAR
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_reason DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_reason TYPE VARCHAR(50) 
        USING reclassified_reason::text
    """)
    
    # Drop the old enum type
    op.execute("DROP TYPE IF EXISTS suspicionreason")
    
    # Create the new enum type with lowercase values
    op.execute("CREATE TYPE suspicionreason AS ENUM ('stolen_vehicle', 'suspicious_behavior', 'wanted_plate', 'unusual_hours', 'known_associate', 'drug_trafficking', 'weapons', 'gang_activity', 'other')")
    
    # Convert existing values from uppercase to lowercase in suspicionreport
    op.execute("""
        UPDATE suspicionreport 
        SET reason = CASE 
            WHEN reason = 'STOLEN_VEHICLE' THEN 'stolen_vehicle'
            WHEN reason = 'SUSPICIOUS_BEHAVIOR' THEN 'suspicious_behavior'
            WHEN reason = 'WANTED_PLATE' THEN 'wanted_plate'
            WHEN reason = 'UNUSUAL_HOURS' THEN 'unusual_hours'
            WHEN reason = 'KNOWN_ASSOCIATE' THEN 'known_associate'
            WHEN reason = 'DRUG_TRAFFICKING' THEN 'drug_trafficking'
            WHEN reason = 'WEAPONS' THEN 'weapons'
            WHEN reason = 'GANG_ACTIVITY' THEN 'gang_activity'
            WHEN reason = 'OTHER' THEN 'other'
            ELSE 'suspicious_behavior'
        END
    """)
    
    # Convert existing values from uppercase to lowercase in intelligencereview
    op.execute("""
        UPDATE intelligencereview 
        SET reclassified_reason = CASE 
            WHEN reclassified_reason = 'STOLEN_VEHICLE' THEN 'stolen_vehicle'
            WHEN reclassified_reason = 'SUSPICIOUS_BEHAVIOR' THEN 'suspicious_behavior'
            WHEN reclassified_reason = 'WANTED_PLATE' THEN 'wanted_plate'
            WHEN reclassified_reason = 'UNUSUAL_HOURS' THEN 'unusual_hours'
            WHEN reclassified_reason = 'KNOWN_ASSOCIATE' THEN 'known_associate'
            WHEN reclassified_reason = 'DRUG_TRAFFICKING' THEN 'drug_trafficking'
            WHEN reclassified_reason = 'WEAPONS' THEN 'weapons'
            WHEN reclassified_reason = 'GANG_ACTIVITY' THEN 'gang_activity'
            WHEN reclassified_reason = 'OTHER' THEN 'other'
            ELSE 'suspicious_behavior'
        END
        WHERE reclassified_reason IS NOT NULL
    """)
    
    # Alter suspicionreport.reason back to enum with correct type
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN reason TYPE suspicionreason 
        USING reason::text::suspicionreason
    """)
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN reason SET DEFAULT 'suspicious_behavior'::suspicionreason")
    
    # Alter intelligencereview.reclassified_reason back to enum with correct type
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_reason TYPE suspicionreason 
        USING CASE WHEN reclassified_reason IS NOT NULL THEN reclassified_reason::text::suspicionreason ELSE NULL END
    """)


def downgrade():
    # Revert the changes for suspicionreason
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN reason DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN reason TYPE VARCHAR(50) 
        USING reason::text
    """)
    
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_reason DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_reason TYPE VARCHAR(50) 
        USING reclassified_reason::text
    """)
    
    op.execute("DROP TYPE IF EXISTS suspicionreason")
    
    op.execute("CREATE TYPE suspicionreason AS ENUM ('STOLEN_VEHICLE', 'SUSPICIOUS_BEHAVIOR', 'WANTED_PLATE', 'UNUSUAL_HOURS', 'KNOWN_ASSOCIATE', 'DRUG_TRAFFICKING', 'WEAPONS', 'GANG_ACTIVITY', 'OTHER')")
    
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN reason TYPE suspicionreason 
        USING reason::text::suspicionreason
    """)
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN reason SET DEFAULT 'SUSPICIOUS_BEHAVIOR'::suspicionreason")
    
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_reason TYPE suspicionreason 
        USING CASE WHEN reclassified_reason IS NOT NULL THEN reclassified_reason::text::suspicionreason ELSE NULL END
    """)
    
    # Revert the changes for urgencylevel
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN urgency DROP DEFAULT")
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN urgency TYPE VARCHAR(20) 
        USING urgency::text
    """)
    
    op.execute("ALTER TABLE intelligencereview ALTER COLUMN reclassified_urgency DROP DEFAULT")
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_urgency TYPE VARCHAR(20) 
        USING reclassified_urgency::text
    """)
    
    op.execute("DROP TYPE IF EXISTS urgencylevel")
    
    op.execute("CREATE TYPE urgencylevel AS ENUM ('MONITOR', 'INTELLIGENCE', 'APPROACH')")
    
    op.execute("""
        ALTER TABLE suspicionreport 
        ALTER COLUMN urgency TYPE urgencylevel 
        USING urgency::text::urgencylevel
    """)
    op.execute("ALTER TABLE suspicionreport ALTER COLUMN urgency SET DEFAULT 'INTELLIGENCE'::urgencylevel")
    
    op.execute("""
        ALTER TABLE intelligencereview 
        ALTER COLUMN reclassified_urgency TYPE urgencylevel 
        USING CASE WHEN reclassified_urgency IS NOT NULL THEN reclassified_urgency::text::urgencylevel ELSE NULL END
    """)
