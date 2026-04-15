"""Agency schemas for BI Institutional Dashboard."""
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AgencyBase(BaseModel):
    name: str
    code: str
    type: str  # "local", "regional", "central"


class AgencyCreate(AgencyBase):
    parent_agency_id: UUID | None = None


class AgencyUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    parent_agency_id: UUID | None = None
    is_active: bool | None = None


class AgencyResponse(AgencyBase):
    id: UUID
    parent_agency_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgencyListResponse(BaseModel):
    agencies: list[AgencyResponse]
    total: int
