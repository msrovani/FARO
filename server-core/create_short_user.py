"""Create test user with very short password"""
import asyncio
import uuid
import bcrypt
from sqlalchemy import text
from app.db.session import get_db


async def create_short_user():
    """Create test user with very short password"""
    print("Creating test user with short password...")
    
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
        
        # Create test user with bcrypt directly
        user_id = str(uuid.uuid4())
        password = b"abc"  # Very short password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password, salt).decode('utf-8')
        
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
        
        print(f"✓ Created test user:")
        print(f"  Email: admin@faro.test")
        print(f"  Password: abc")
        print(f"  Role: admin")
        print(f"  User ID: {user_id}")
        
        break
    
    print("\nYou can now login with:")
    print("  Email: admin@faro.test")
    print("  Password: abc")


if __name__ == "__main__":
    asyncio.run(create_short_user())
