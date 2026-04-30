#!/usr/bin/env python3
"""
Create temporary admin user for F.A.R.O. system
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import get_db
from app.db.base import User, UserRole, Agency
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    """Create a temporary admin user"""
    async for db in get_db():
        # Check if user already exists
        existing_user = await db.execute(
            select(User).where(User.email == "temp_admin@faro.pol")
        )
        if existing_user.scalar_one_or_none():
            print("User temp_admin@faro.pol already exists")
            return
        
        # Get or create default agency
        agency = await db.execute(
            select(Agency).where(Agency.code == "FARO-DEFAULT")
        )
        agency = agency.scalar_one_or_none()
        
        if not agency:
            # Create default agency
            agency = Agency(
                id="11111111-1111-1111-1111-111111111111",
                name="Agencia Padrao FARO",
                code="FARO-DEFAULT",
                is_active=True,
                type="LOCAL"
            )
            db.add(agency)
            await db.commit()
            await db.refresh(agency)
        
        # Create admin user
        admin_user = User(
            email="temp_admin@faro.pol",
            hashed_password=get_password_hash("admin123"),
            full_name="Temp Admin",
            badge_number="TEMP001",
            role=UserRole.ADMIN,
            agency_id=agency.id,
            is_active=True,
            is_verified=True,
            is_on_duty=True
        )
        
        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)
        
        print(f"Created admin user:")
        print(f"  Email: temp_admin@faro.pol")
        print(f"  Password: admin123")
        print(f"  Role: {admin_user.role}")
        print(f"  Agency: {agency.name}")

if __name__ == "__main__":
    asyncio.run(create_admin())
