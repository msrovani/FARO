#!/usr/bin/env python3
"""
Test authentication and API endpoints
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import get_db
from app.api.v1.endpoints.auth import authenticate_user, create_access_token
from app.db.base import User
from sqlalchemy import select

async def test_auth():
    """Test authentication and get token"""
    async for db in get_db():
        # Find user
        result = await db.execute(
            select(User).where(User.email == "temp_admin@faro.pol")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("User not found")
            return
        
        print(f"Found user: {user.email}")
        print(f"Role: {user.role}")
        
        # Create token
        token = create_access_token(data={"sub": user.email})
        print(f"Token: {token}")
        
        return token

if __name__ == "__main__":
    asyncio.run(test_auth())
