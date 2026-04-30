"""Verifica contagens das tabelas no banco de dados"""
import asyncio
from sqlalchemy import text
from app.db.session import get_db


async def check_counts():
    """Verifica contagens das tabelas principais"""
    print("📊 Verificando contagens das tabelas no banco de dados...\n")
    
    async for db in get_db():
        tables = [
            ("vehicleobservation", "Vehicle Observations"),
            ("plateread", "Plate Reads"),
            ("suspicionreport", "Suspicion Reports"),
            ("intelligencereview", "Intelligence Reviews"),
            ("watchlistentry", "Watchlist Entries"),
            ("alert", "Alerts"),
            ("device", "Devices"),
            ("user", "Users"),
        ]
        
        for table_name, display_name in tables:
            try:
                result = await db.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = result.scalar()
                print(f"  • {display_name}: {count}")
            except Exception as e:
                print(f"  • {display_name}: Erro - {e}")
        
        break


if __name__ == "__main__":
    asyncio.run(check_counts())
