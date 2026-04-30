"""Check enum values in database"""
import asyncio
from sqlalchemy import text
from app.db.session import get_db


async def check_enum():
    """Check userrole enum values"""
    print("Checking userrole enum values...")
    
    async for db in get_db():
        result = await db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = 'userrole'::regtype
            ORDER BY enumsortorder
        """))
        
        values = [row[0] for row in result.fetchall()]
        print(f"UserRole enum values: {values}")
        
        break


if __name__ == "__main__":
    asyncio.run(check_enum())
