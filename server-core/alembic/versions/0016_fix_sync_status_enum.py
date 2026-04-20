"""Fix sync_status column type to use proper enum

Revision ID: 0016
Revises: 0015
Create Date: 2026-04-20 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016_fix_sync_status_enum'
down_revision = '0015_add_connectivity_type'
branch_labels = None
depends_on = None


def upgrade():
    # First, create the enum type if it doesn't exist using DO block
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE syncstatus AS ENUM ('PENDING', 'COMPLETED', 'FAILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Convert existing VARCHAR values to the enum type
    # First, update any NULL values to 'PENDING'
    op.execute("UPDATE vehicleobservation SET sync_status = 'PENDING' WHERE sync_status IS NULL")
    
    # Drop default value constraint
    op.execute("ALTER TABLE vehicleobservation ALTER COLUMN sync_status DROP DEFAULT")
    
    # Then alter the column type
    op.execute("""
        ALTER TABLE vehicleobservation 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING sync_status::text::syncstatus
    """)
    
    # Set default back to enum type
    op.execute("ALTER TABLE vehicleobservation ALTER COLUMN sync_status SET DEFAULT 'PENDING'::syncstatus")


def downgrade():
    # Revert back to VARCHAR
    op.execute("""
        ALTER TABLE vehicleobservation 
        ALTER COLUMN sync_status TYPE VARCHAR(20) 
        USING sync_status::text
    """)
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS syncstatus")
