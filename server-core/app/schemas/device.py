from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    device_id: str
    user_id: UUID
    agency_id: Optional[UUID] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    is_active: bool
    last_seen: datetime
    last_justification: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class DeviceSuspendRequest(BaseModel):
    justification: str
