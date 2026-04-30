"""
F.A.R.O. API Dependencies - Shared dependencies for endpoints
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.endpoints.auth import get_current_user, require_role
from app.db.base import UserRole

__all__ = ["get_db", "require_field_agent", "require_intelligence_analyst", "get_current_user"]

# Role-based dependencies
require_field_agent = require_role(UserRole.FIELD_AGENT)
require_intelligence_analyst = require_role(UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN)
