"""
F.A.R.O. API Dependencies - Shared dependencies for endpoints
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

__all__ = ["get_db"]
