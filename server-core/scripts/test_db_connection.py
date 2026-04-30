import asyncio
import logging
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    try:
        async with engine.connect() as conn:
            logger.info("Database connected successfully")
            return True
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
