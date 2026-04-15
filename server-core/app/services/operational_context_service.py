"""
Operational context enrichment for field observations.

This service provides:
- state-level vehicle registry lookup via adapter
- prior suspicion lookup by plate
- audit-friendly records in ExternalQuery
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import ExternalQuery, SuspicionReport, User, VehicleObservation
from app.integrations.state_registry_adapter import query_state_vehicle_registry


async def _record_external_query(
    db: AsyncSession,
    *,
    observation_id: UUID | None,
    query_type: str,
    queried_value: str,
    system_name: str,
    request_payload: dict[str, Any],
    response_status: str,
    response_data: dict[str, Any],
) -> None:
    response_raw = json.dumps(response_data, sort_keys=True, ensure_ascii=True).encode("utf-8")
    response_hash = hashlib.sha256(response_raw).hexdigest()
    db.add(
        ExternalQuery(
            observation_id=observation_id,
            query_type=query_type,
            queried_value=queried_value,
            system_name=system_name,
            request_payload=request_payload,
            response_status=response_status,
            response_data=response_data,
            response_hash=response_hash,
            queried_at=datetime.utcnow(),
            cache_hit=False,
        )
    )
    await db.flush()


async def query_state_registry_for_plate(
    db: AsyncSession,
    *,
    observation_id: UUID | None,
    plate_number: str,
) -> dict[str, Any]:
    response_data = await query_state_vehicle_registry(plate_number=plate_number)
    response_status = "success" if response_data.get("connected") else "unavailable"
    await _record_external_query(
        db,
        observation_id=observation_id,
        query_type="state_registry_lookup",
        queried_value=plate_number,
        system_name="state_vehicle_registry",
        request_payload={"plate_number": plate_number, "adapter_mode": "separate_adapter"},
        response_status=response_status,
        response_data=response_data,
    )
    return response_data


async def get_first_prior_suspicion_for_plate(
    db: AsyncSession,
    *,
    plate_number: str,
    agency_id: UUID | None = None,
    exclude_observation_id: UUID | None = None,
    record_external: bool = False,
    observation_id: UUID | None = None,
) -> dict[str, Any] | None:
    query = (
        select(SuspicionReport, VehicleObservation, User)
        .join(VehicleObservation, VehicleObservation.id == SuspicionReport.observation_id)
        .join(User, User.id == VehicleObservation.agent_id)
        .where(VehicleObservation.plate_number == plate_number)
        .order_by(SuspicionReport.created_at.asc())
    )
    if agency_id is not None:
        query = query.where(VehicleObservation.agency_id == agency_id)
    if exclude_observation_id is not None:
        query = query.where(VehicleObservation.id != exclude_observation_id)

    first_row = (await db.execute(query.limit(1))).first()
    total_count_query = (
        select(func.count(SuspicionReport.id))
        .join(VehicleObservation, VehicleObservation.id == SuspicionReport.observation_id)
        .where(VehicleObservation.plate_number == plate_number)
    )
    if agency_id is not None:
        total_count_query = total_count_query.where(VehicleObservation.agency_id == agency_id)
    if exclude_observation_id is not None:
        total_count_query = total_count_query.where(VehicleObservation.id != exclude_observation_id)
    total_count = (await db.execute(total_count_query)).scalar() or 0

    if first_row is None:
        response_data = {
            "has_prior_suspicion": False,
            "prior_suspicion_count": 0,
        }
        if record_external:
            await _record_external_query(
                db,
                observation_id=observation_id,
                query_type="prior_suspicion_lookup",
                queried_value=plate_number,
                system_name="internal_suspicion_index",
                request_payload={"plate_number": plate_number},
                response_status="success",
                response_data=response_data,
            )
        return None

    suspicion, source_observation, source_agent = first_row
    context = {
        "has_prior_suspicion": True,
        "prior_suspicion_count": int(total_count),
        "first_suspicion_observation_id": str(source_observation.id),
        "first_suspicion_agent_id": str(source_agent.id),
        "first_suspicion_agent_name": source_agent.full_name,
        "first_suspicion_agency_id": str(source_observation.agency_id),  # Agencia de origem
        "first_suspicion_reason": suspicion.reason.value,
        "first_suspicion_level": suspicion.level.value,
        "first_suspicion_urgency": suspicion.urgency.value,
        "first_suspicion_notes": suspicion.notes,
        "first_suspicion_created_at": suspicion.created_at.isoformat(),
    }
    if record_external:
        await _record_external_query(
            db,
            observation_id=observation_id,
            query_type="prior_suspicion_lookup",
            queried_value=plate_number,
            system_name="internal_suspicion_index",
            request_payload={"plate_number": plate_number},
            response_status="success",
            response_data=context,
        )
    return context


async def count_recent_observations(
    db: AsyncSession,
    *,
    plate_number: str,
    agency_id: UUID | None = None,
    days: int = 30,
) -> int:
    """Count recent observations for a plate within the last N days."""
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(func.count(VehicleObservation.id)).where(
        and_(
            VehicleObservation.plate_number == plate_number,
            VehicleObservation.observed_at_server >= cutoff_date,
        )
    )
    
    if agency_id is not None:
        query = query.where(VehicleObservation.agency_id == agency_id)
    
    result = await db.execute(query)
    return result.scalar() or 0


async def build_operational_context_for_observation(
    db: AsyncSession,
    *,
    observation: VehicleObservation,
) -> dict[str, Any]:
    state_registry = await query_state_registry_for_plate(
        db,
        observation_id=observation.id,
        plate_number=observation.plate_number,
    )
    prior_suspicion = await get_first_prior_suspicion_for_plate(
        db,
        plate_number=observation.plate_number,
        agency_id=observation.agency_id,
        exclude_observation_id=observation.id,
        record_external=True,
        observation_id=observation.id,
    )
    return {
        "state_registry": state_registry,
        "prior_suspicion": prior_suspicion,
    }
