"""List users in database"""
import asyncio
from sqlalchemy import text
from app.db.session import get_db


async def list_users():
    """List all users in database"""
    print("Listing users in database...")
    
    async for db in get_db():
        result = await db.execute(text("""
            SELECT id, email, full_name, role, is_active, agency_id 
            FROM "user" 
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        users = result.fetchall()
        
        if not users:
            print("No users found in database.")
            print("\nYou need to create a user first.")
            print("Use the auth endpoint to register a user:")
            print("POST /api/v1/auth/register")
        else:
            print(f"Found {len(users)} users:")
            print("-" * 80)
            for user in users:
                print(f"ID: {user[0]}")
                print(f"Email: {user[1]}")
                print(f"Name: {user[2]}")
                print(f"Role: {user[3]}")
                print(f"Active: {user[4]}")
                print(f"Agency ID: {user[5]}")
                print("-" * 80)
        
        break


if __name__ == "__main__":
    asyncio.run(list_users())
