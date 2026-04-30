#!/usr/bin/env python3
"""
Simple test to check if endpoint exists and authentication works
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import get_db
from app.db.base import User
from sqlalchemy import select
from app.core.security import create_access_token

async def test_simple():
    """Simple test - get user and create token"""
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
        print(f"Agency: {user.agency_id}")
        
        # Create token
        token = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            agency_id=str(user.agency_id)
        )
        print(f"Token: {token}")
        
        # Test endpoint URL
        print("Testing endpoint: http://localhost:8000/intelligence/analytics/overview")
        print("Use this token in Authorization header: Bearer", token)

if __name__ == "__main__":
    asyncio.run(test_simple())
