import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://faro:senha@localhost:5432/faro_db"

async def check_users():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Verificar colunas da tabela user
        result = await session.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print(f"Colunas da tabela user: {len(columns)}")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # Verificar usuários
        result = await session.execute(text("SELECT email, role, is_active FROM user"))
        users = result.fetchall()
        print(f"\nUsuários encontrados: {len(users)}")
        if users:
            for user in users:
                print(f"User: email={user[0]}, role={user[1]}, is_active={user[2]}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_users())
