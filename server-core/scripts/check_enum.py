import asyncio
from app.db.session import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'urgencylevel'"))
        print('urgencylevel values:', [row[0] for row in result])
        
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'suspicionlevel'"))
        print('suspicionlevel values:', [row[0] for row in result])
        
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'suspicionreason'"))
        print('suspicionreason values:', [row[0] for row in result])

asyncio.run(check())
