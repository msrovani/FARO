"""Script para definir senha de usuário"""
import asyncio
from app.db.session import get_db
from sqlalchemy import text
from app.core.security import get_password_hash


async def set_password():
    """Atualiza o usuário existente para role INTELLIGENCE"""
    email = "admin@faro.test"
    new_password = "password123"
    new_role = "INTELLIGENCE"
    
    async for db in get_db():
        try:
            # Listar todos os usuários
            result = await db.execute(text("SELECT id, email, role FROM \"user\" LIMIT 10"))
            users = result.fetchall()
            print("Usuários no banco:")
            for u in users:
                print(f"  ID: {u[0]}, Email: {u[1]}, Role: {u[2]}")
            
            # Verificar se usuário existe
            result = await db.execute(
                text("SELECT id, email, role FROM \"user\" WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"\n❌ Usuário {email} não encontrado")
                return
            
            user_id = user[0]
            print(f"\n✓ Usuário encontrado: {user[1]} (ID: {user_id})")
            
            # Atualizar role para INTELLIGENCE
            password_hash = get_password_hash(new_password)
            await db.execute(
                text("UPDATE \"user\" SET hashed_password = :hash, role = :role WHERE id = :id"),
                {"hash": password_hash, "role": new_role, "id": user_id}
            )
            await db.commit()
            
            print(f"✅ Usuário atualizado para role INTELLIGENCE: {email}")
            print(f"   Senha: {new_password}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            await db.rollback()
        
        break


if __name__ == "__main__":
    asyncio.run(set_password())
