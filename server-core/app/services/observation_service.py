"""
Serviços de observação e feedback operacional.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    AnalystFeedbackEvent,
    Device,
    FeedbackEvent,
    IntelligenceReview,
    PlateRead,
    SuspicionReport,
    SyncStatus,
    UrgencyLevel,
    User,
    VehicleObservation,
)
from app.schemas.common import GeolocationPoint
from app.schemas.observation import InstantFeedback, PlateReadResponse, VehicleObservationResponse


async def get_or_register_device(
    db: AsyncSession,
    *,
    device_identifier: str,
    current_user: User,
    app_version: str,
) -> Device:
    result = await db.execute(
        select(Device).where(
            and_(
                Device.device_id == device_identifier,
                Device.user_id == current_user.id,
            )
        )
    )
    device = result.scalar_one_or_none()

    if device is None:
        device = Device(
            user_id=current_user.id,
            agency_id=current_user.agency_id,
            device_id=device_identifier,
            device_model="unknown",
            os_version="unknown",
            app_version=app_version,
            last_seen=datetime.utcnow(),
        )
        db.add(device)
        await db.flush()
    else:
        device.last_seen = datetime.utcnow()
        device.app_version = app_version

    return device


def location_geometry(location: GeolocationPoint):
    return ST_SetSRID(ST_MakePoint(location.longitude, location.latitude), 4326)


async def fetch_plate_reads_map(
    db: AsyncSession,
    observation_ids: list[UUID],
) -> dict[UUID, list[PlateReadResponse]]:
    if not observation_ids:
        return {}

    result = await db.execute(
        select(PlateRead)
        .where(PlateRead.observation_id.in_(observation_ids))
        .order_by(PlateRead.observation_id, desc(PlateRead.processed_at))
    )

    plate_reads_by_observation: dict[UUID, list[PlateReadResponse]] = {}
    for plate_read in result.scalars().all():
        plate_reads_by_observation.setdefault(plate_read.observation_id, []).append(
            PlateReadResponse.model_validate(plate_read)
        )

    return plate_reads_by_observation


async def fetch_plate_activity_map(
    db: AsyncSession,
    plate_numbers: list[str],
    agency_id: UUID | None = None,
) -> dict[str, dict[str, int | bool]]:
    if not plate_numbers:
        return {}

    completed_counts_result = await db.execute(
        select(
            VehicleObservation.plate_number,
            func.count(VehicleObservation.id),
        )
        .where(
            and_(
                VehicleObservation.plate_number.in_(plate_numbers),
                VehicleObservation.sync_status == SyncStatus.COMPLETED,
            )
        )
        .group_by(VehicleObservation.plate_number)
    )
    monitored_result = await db.execute(
        select(VehicleObservation.plate_number)
        .join(SuspicionReport, SuspicionReport.observation_id == VehicleObservation.id)
        .where(
            and_(
                VehicleObservation.plate_number.in_(plate_numbers),
                SuspicionReport.urgency == UrgencyLevel.MONITOR,
            )
        )
        .group_by(VehicleObservation.plate_number)
    )
    if agency_id is not None:
        completed_counts_result = await db.execute(
            select(
                VehicleObservation.plate_number,
                func.count(VehicleObservation.id),
            )
            .where(
                and_(
                    VehicleObservation.plate_number.in_(plate_numbers),
                    VehicleObservation.sync_status == SyncStatus.COMPLETED,
                    VehicleObservation.agency_id == agency_id,
                )
            )
            .group_by(VehicleObservation.plate_number)
        )
        monitored_result = await db.execute(
            select(VehicleObservation.plate_number)
            .join(SuspicionReport, SuspicionReport.observation_id == VehicleObservation.id)
            .where(
                and_(
                    VehicleObservation.plate_number.in_(plate_numbers),
                    SuspicionReport.urgency == UrgencyLevel.MONITOR,
                    VehicleObservation.agency_id == agency_id,
                )
            )
            .group_by(VehicleObservation.plate_number)
        )

    counts = {plate: count for plate, count in completed_counts_result.all()}
    monitored = {plate for plate, in monitored_result.all()}

    return {
        plate: {
            "completed_count": counts.get(plate, 0),
            "is_monitored": plate in monitored,
        }
        for plate in set(plate_numbers)
    }


async def build_instant_feedback(
    db: AsyncSession,
    *,
    plate_number: str,
    current_observation_id: UUID,
    agency_id: UUID | None = None,
    state_registry_status: dict[str, Any] | None = None,
    prior_suspicion_context: dict[str, Any] | None = None,
) -> InstantFeedback:
    activity_map = await fetch_plate_activity_map(db, [plate_number], agency_id=agency_id)
    plate_activity = activity_map.get(
        plate_number,
        {"completed_count": 0, "is_monitored": False},
    )

    previous_count = max(int(plate_activity["completed_count"]) - 1, 0)
    is_monitored = bool(plate_activity["is_monitored"])

    severity = None
    title = None
    message = None
    guidance = None

    if state_registry_status and state_registry_status.get("status") in {"wanted", "judicial_block"}:
        severity = "critical"
        title = "Restricao no cadastro estadual"
        restriction = state_registry_status.get("restriction") or "restricao_ativa"
        message = f"Consulta estadual retornou condicao {state_registry_status.get('status')} ({restriction})."
        guidance = "Realize abordagem com protocolo de seguranca e confirme o desfecho no sistema."
    elif previous_count >= 8:
        severity = "high"
        title = "Recorrencia elevada"
        message = f"Placa ja observada {previous_count} vezes anteriormente."
        guidance = "Priorize confirmacao contextual e informe estruturado."
    elif is_monitored:
        severity = "moderate"
        title = "Monitoramento previo"
        message = "Ha informes anteriores com indicacao de monitoramento."
        guidance = "Registrar contexto e manter observacao qualificada."
    elif prior_suspicion_context and prior_suspicion_context.get("has_prior_suspicion"):
        severity = "moderate"
        title = "Suspeicao previa registrada"
        reason = prior_suspicion_context.get("first_suspicion_reason") or "other"
        level = prior_suspicion_context.get("first_suspicion_level") or "medium"
        message = f"Existe suspeicao anterior para a placa (motivo: {reason}, grau: {level})."
        guidance = "Se houver abordagem, confirme ou descarte a suspeicao no retorno operacional."

    return InstantFeedback(
        has_alert=severity is not None,
        alert_level=severity,
        alert_title=title,
        alert_message=message,
        previous_observations_count=previous_count,
        is_monitored=is_monitored,
        intelligence_interest=is_monitored or previous_count >= 8,
        guidance=guidance,
        state_registry_status=state_registry_status,
        prior_suspicion_context=prior_suspicion_context,
        requires_suspicion_confirmation=bool(
            prior_suspicion_context and prior_suspicion_context.get("has_prior_suspicion")
        ),
    )


async def serialize_observation(
    db: AsyncSession,
    observation: VehicleObservation,
    agent: User,
    *,
    plate_reads_map: dict[UUID, list[PlateReadResponse]] | None = None,
    operational_context: dict[str, Any] | None = None,
) -> VehicleObservationResponse:
    plate_reads_lookup = plate_reads_map or await fetch_plate_reads_map(db, [observation.id])
    plate_reads = plate_reads_lookup.get(observation.id, [])
    point = to_shape(observation.location)
    instant_feedback = await build_instant_feedback(
        db,
        plate_number=observation.plate_number,
        current_observation_id=observation.id,
        agency_id=observation.agency_id,
        state_registry_status=(operational_context or {}).get("state_registry"),
        prior_suspicion_context=(operational_context or {}).get("prior_suspicion"),
    )

    return VehicleObservationResponse(
        id=observation.id,
        client_id=observation.client_id,
        plate_number=observation.plate_number,
        plate_state=observation.plate_state,
        plate_country=observation.plate_country,
        observed_at_local=observation.observed_at_local,
        observed_at_server=observation.observed_at_server,
        location=GeolocationPoint(
            latitude=point.y,
            longitude=point.x,
            accuracy=observation.location_accuracy,
        ),
        location_accuracy=observation.location_accuracy,
        heading=observation.heading,
        speed=observation.speed,
        vehicle_color=observation.vehicle_color,
        vehicle_type=observation.vehicle_type,
        vehicle_model=observation.vehicle_model,
        vehicle_year=observation.vehicle_year,
        sync_status=observation.sync_status,
        sync_attempts=observation.sync_attempts,
        synced_at=observation.synced_at,
        metadata_snapshot=observation.metadata_snapshot,
        agent_id=agent.id,
        agent_name=agent.full_name,
        device_id=observation.device_id,
        created_at=observation.created_at,
        updated_at=observation.updated_at,
        plate_reads=plate_reads,
        instant_feedback=instant_feedback,
    )


async def fetch_history_flags(
    db: AsyncSession,
    observation_ids: list[UUID],
) -> tuple[dict[UUID, bool], dict[UUID, bool]]:
    if not observation_ids:
        return {}, {}

    feedback_result = await db.execute(
        select(IntelligenceReview.observation_id, func.count(FeedbackEvent.id))
        .join(FeedbackEvent, FeedbackEvent.review_id == IntelligenceReview.id)
        .where(IntelligenceReview.observation_id.in_(observation_ids))
        .group_by(IntelligenceReview.observation_id)
    )
    structured_feedback_result = await db.execute(
        select(AnalystFeedbackEvent.observation_id, func.count(AnalystFeedbackEvent.id))
        .where(
            and_(
                AnalystFeedbackEvent.observation_id.is_not(None),
                AnalystFeedbackEvent.observation_id.in_(observation_ids),
            )
        )
        .group_by(AnalystFeedbackEvent.observation_id)
    )
    suspicion_result = await db.execute(
        select(SuspicionReport.observation_id, func.count(SuspicionReport.id))
        .where(SuspicionReport.observation_id.in_(observation_ids))
        .group_by(SuspicionReport.observation_id)
    )

    feedback_map = {observation_id: count > 0 for observation_id, count in feedback_result.all()}
    for observation_id, count in structured_feedback_result.all():
        feedback_map[observation_id] = feedback_map.get(observation_id, False) or count > 0
    suspicion_map = {observation_id: count > 0 for observation_id, count in suspicion_result.all()}
    return feedback_map, suspicion_map
