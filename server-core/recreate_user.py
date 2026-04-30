"""Recreate test user with shorter password"""
import asyncio
import uuid
from sqlalchemy import text
from app.db.session import get_db


async def recreate_user():
    """Recreate test user with shorter password"""
    print("Recreating test user...")
    
    async for db in get_db():
        # Delete existing user
        await db.execute(text("""
            DELETE FROM "user" WHERE email = 'admin@faro.test'
        """))
        
        # Get agency
        result = await db.execute(text("""
            SELECT id FROM agency WHERE code = 'FARO-DEFAULT'
        """))
        agency = result.fetchone()
        
        if not agency:
            print("Agency not found!")
            break
        
        agency_id = str(agency[0])
        
        # Create test user with a simple hash (for testing only)
        user_id = str(uuid.uuid4())
        # Using a known bcrypt hash for "admin" (short password)
        hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyW5qL1t1E2i"
        
        await db.execute(text("""
            INSERT INTO "user" (id, email, hashed_password, full_name, role, agency_id, is_active, is_verified, is_on_duty)
            VALUES (:id, :email, :hashed_password, :full_name, :role, :agency_id, :is_active, :is_verified, :is_on_duty)
        """), {
            "id": user_id,
            "email": "admin@faro.test",
            "hashed_password": hashed_password,
            "full_name": "Admin Test",
            "role": "ADMIN",
            "agency_id": agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": False
        })
        
        await db.commit()
        
        print(f"✓ Recreated test user:")
        print(f"  Email: admin@faro.test")
        print(f"  Password: admin")
        print(f"  Role: admin")
        print(f"  User ID: {user_id}")
        
        break
    
    print("\nYou can now login with:")
    print("  Email: admin@faro.test")
    print("  Password: admin")


if __name__ == "__main__":
    asyncio.run(recreate_user())
