import asyncio
from app.db.session import engine

async def test_connection():
    try:
        async with engine.connect() as conn:
            print("Database connected successfully")
            return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
