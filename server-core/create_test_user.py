"""Create test user in database"""
import asyncio
import uuid
import bcrypt
from sqlalchemy import text
from app.db.session import get_db


async def create_test_user():
    """Create a test admin user"""
    print("Creating test user...")
    
    async for db in get_db():
        # Check if user already exists
        result = await db.execute(text("""
            SELECT id FROM "user" WHERE email = 'admin@faro.test'
        """))
        
        if result.fetchone():
            print("User admin@faro.test already exists.")
            break
        
        # Create a default agency first if it doesn't exist
        result = await db.execute(text("""
            SELECT id FROM agency WHERE code = 'FARO-DEFAULT'
        """))
        agency = result.fetchone()
        
        if not agency:
            print("Creating default agency...")
            agency_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO agency (id, name, code, is_active, type)
                VALUES (:id, :name, :code, :is_active, :type)
            """), {
                "id": agency_id,
                "name": "FARO Default Agency",
                "code": "FARO-DEFAULT",
                "is_active": True,
                "type": "central"
            })
            print(f"Created agency: {agency_id}")
        else:
            agency_id = str(agency[0])
            print(f"Using existing agency: {agency_id}")
        
        # Create test user with bcrypt directly
        user_id = str(uuid.uuid4())
        password = b"admin123"
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
            "role": "ADMIN",  # Enum value must be uppercase
            "agency_id": agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": False
        })
        
        await db.commit()
        
        print(f"✓ Created test user:")
        print(f"  Email: admin@faro.test")
        print(f"  Password: admin123")
        print(f"  Role: admin")
        print(f"  User ID: {user_id}")
        print(f"  Agency ID: {agency_id}")
        
        break
    
    print("\nYou can now login with:")
    print("  Email: admin@faro.test")
    print("  Password: admin123")


if __name__ == "__main__":
    asyncio.run(create_test_user())
