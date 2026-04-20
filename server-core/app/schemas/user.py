"""
F.A.R.O. User Schemas - Authentication and user management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from app.db.base import UserRole
from app.schemas.common import GeolocationPoint


class UserBase(BaseModel):
    """Base user schema."""

    model_config = ConfigDict(from_attributes=True)

    cpf: Optional[str] = Field(
        None, min_length=11, max_length=11, description="Brazilian CPF (only digits)"
    )
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    badge_number: Optional[str] = Field(None, max_length=50)
    role: UserRole = UserRole.FIELD_AGENT


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100)
    agency_id: UUID
    unit_id: Optional[UUID] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    model_config = ConfigDict(from_attributes=True)

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    badge_number: Optional[str] = Field(None, max_length=50)
    role: Optional[UserRole] = None
    agency_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agency_id: UUID
    agency_name: Optional[str] = None
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """Schema for user login - supports both email and CPF authentication."""

    # Can be either email OR CPF (11 digits)
    identifier: str = Field(..., description="Email or CPF (11 digits)")
    password: str
    device_id: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    shift_duration_hours: Optional[int] = Field(None, description="Shift duration in hours (+1, +6, +12, +24)")

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        # Remove any formatting from CPF
        cpf_digits = v.replace(".", "").replace("-", "")
        # If it's 11 digits, treat as CPF, otherwise as email
        if len(cpf_digits) == 11 and cpf_digits.isdigit():
            return cpf_digits
        # Otherwise must be valid email
        if "@" not in v:
            raise ValueError("Identifier must be a valid email or CPF (11 digits)")
        return v


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: Optional[str] = None  # user id
    exp: Optional[datetime] = None
    type: Optional[str] = None  # "access" or "refresh"
    role: Optional[UserRole] = None
    agency_id: Optional[str] = None


class TokenRefresh(BaseModel):
    """Schema for token refresh."""

    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class AgentLocationUpdate(BaseModel):
    """Schema for a single location update."""
    location: GeolocationPoint
    recorded_at: datetime
    connectivity_status: Optional[str] = None
    battery_level: Optional[float] = None


class AgentLocationBatchSync(BaseModel):
    """Schema for batch syncing historical/offline locations."""
    items: List[AgentLocationUpdate]
    device_id: str


class ShiftRenewalRequest(BaseModel):
    shift_duration_hours: int
