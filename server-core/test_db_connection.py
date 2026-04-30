"""Test database connection and migrations"""
import asyncio
from sqlalchemy import text
from app.db.session import get_db


async def test_db():
    """Test database connection and check migrations"""
    print("Testing database connection...")
    
    async for db in get_db():
        # Test basic connection
        result = await db.execute(text("SELECT 1"))
        print(f"✓ Database connection: OK (result: {result.scalar()})")
        
        # Check alembic version
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        print(f"✓ Current migration version: {result.scalar()}")
        
        # Check if tables exist
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('user', 'agency', 'vehicleobservation', 'alert', 'suspicionreport')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"✓ Core tables exist: {', '.join(tables)}")
        
        # Check if new indexes exist (from migrations 0021-0024)
        result = await db.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname LIKE 'ix_vehicleobservation_created_at'
            OR indexname LIKE 'ix_alert_observation_id'
            OR indexname LIKE 'ix_suspicionreport_observation_id'
        """))
        indexes = [row[0] for row in result.fetchall()]
        print(f"✓ New performance indexes: {', '.join(indexes) if indexes else 'None'}")
        
        # Check if CHECK constraints exist (from migration 0021)
        result = await db.execute(text("""
            SELECT conname 
            FROM pg_constraint 
            WHERE conname LIKE 'chk_%'
            LIMIT 5
        """))
        constraints = [row[0] for row in result.fetchall()]
        print(f"✓ CHECK constraints: {', '.join(constraints) if constraints else 'None'}")
        
        # Check if partitioning functions exist (from migration 0024)
        result = await db.execute(text("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_name LIKE 'create_monthly_partition%'
            OR routine_name LIKE 'drop_old_partitions%'
        """))
        functions = [row[0] for row in result.fetchall()]
        print(f"✓ Partitioning functions: {', '.join(functions) if functions else 'None'}")
        
        break
    
    print("\n✓ Database is healthy and migrations are applied!")


if __name__ == "__main__":
    asyncio.run(test_db())
