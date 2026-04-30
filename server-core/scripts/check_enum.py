import asyncio
import logging
from app.db.session import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'urgencylevel'"))
        logger.info('urgencylevel values: %s', [row[0] for row in result])
        
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'suspicionlevel'"))
        logger.info('suspicionlevel values: %s', [row[0] for row in result])
        
        result = await conn.execute(text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'suspicionreason'"))
        logger.info('suspicionreason values: %s', [row[0] for row in result])

asyncio.run(check())
