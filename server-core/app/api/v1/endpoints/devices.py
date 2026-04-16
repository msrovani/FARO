from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import Device, User, UserRole
from app.schemas.device import DeviceResponse, DeviceSuspendRequest

router = APIRouter()

def require_supervisor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.SUPERVISOR, UserRole.ADMIN, UserRole.INTELLIGENCE}:
        raise HTTPException(status_code=403, detail="Acesso administrativo requerido")
    return current_user

@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_admin),
):
    query = select(Device).order_by(Device.last_seen.desc())
    if current_user.role != UserRole.ADMIN:
        if current_user.agency_id:
            query = query.where(Device.agency_id == current_user.agency_id)
        else:
            return []
            
    result = await db.execute(query)
    devices = result.scalars().all()
    return devices

@router.patch("/{device_id}/suspend", response_model=DeviceResponse)
async def suspend_device(
    device_id: UUID,
    request: DeviceSuspendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_admin),
):
    device = (await db.execute(select(Device).where(Device.id == device_id))).scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
        
    if current_user.role != UserRole.ADMIN and device.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Sem acesso a este dispositivo")
        
    device.is_active = not device.is_active
    device.last_justification = request.justification
    db.add(device)
    await db.flush()
    return device
