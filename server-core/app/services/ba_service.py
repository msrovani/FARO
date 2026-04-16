"""
F.A.R.O. Services — Boletim de Atendimento (BA)

Orquestra a geração, persistência e transmissão de BAs.
Cada abordagem concluída gera 1 BA. A transmissão pode ser:
    - unitária (imediata após a abordagem), ou
    - em lote (batch) via endpoint administrativo.

NOTA: Em dev-mode, o conector não envia ao sistema estadual.
      O BA é persistido com status NOT_SENT/PENDING.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from geoalchemy2.shape import to_shape
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    BoletimAtendimento,
    SuspicionReport,
    User,
    Unit,
    Agency,
    VehicleObservation,
)
from app.integrations.bm_ba_connector import transmit_ba_to_state_system, transmit_ba_batch
from app.schemas.boletim_atendimento import (
    BABatchResult,
    BAListResponse,
    BAPayload,
    BARecord,
    BATransmissionStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Geração de BA a partir de uma abordagem concluída
# ---------------------------------------------------------------------------
async def generate_ba_from_approach(
    db: AsyncSession,
    *,
    observation_id: UUID,
    approach_data: Dict[str, Any],
    current_user: User,
) -> BoletimAtendimento:
    """
    Gera um Boletim de Atendimento vinculado a uma observação/abordagem.

    Args:
        db: Sessão do banco.
        observation_id: ID da VehicleObservation.
        approach_data: Dados da abordagem (vindos do ApproachConfirmationRequest).
        current_user: Usuário autenticado (agente de campo).

    Returns:
        BoletimAtendimento persistido.
    """
    # Buscar observação + contexto
    obs_result = await db.execute(
        select(VehicleObservation).where(VehicleObservation.id == observation_id)
    )
    observation = obs_result.scalar_one_or_none()
    if observation is None:
        raise ValueError(f"Observação {observation_id} não encontrada.")

    # Extrair localização
    point = to_shape(observation.location)

    # Buscar dados da unidade/agência
    unit_code = None
    agency_code = None
    if current_user.unit_id:
        unit_result = await db.execute(
            select(Unit).where(Unit.id == current_user.unit_id)
        )
        unit = unit_result.scalar_one_or_none()
        if unit:
            unit_code = unit.code
    agency_result = await db.execute(
        select(Agency).where(Agency.id == current_user.agency_id)
    )
    agency = agency_result.scalar_one_or_none()
    if agency:
        agency_code = agency.code

    # Montar payload
    payload = BAPayload(
        observation_id=observation.id,
        approach_timestamp=approach_data.get(
            "approached_at_local", datetime.utcnow()
        ),
        agent_badge_number=current_user.badge_number,
        agent_full_name=current_user.full_name,
        unit_code=unit_code,
        agency_code=agency_code,
        plate_number=observation.plate_number,
        plate_state=observation.plate_state,
        vehicle_color=observation.vehicle_color,
        vehicle_type=observation.vehicle_type,
        vehicle_model=observation.vehicle_model,
        vehicle_year=observation.vehicle_year,
        latitude=point.y,
        longitude=point.x,
        street_direction=approach_data.get("street_direction"),
        approach_outcome=approach_data.get("approach_outcome", "approached"),
        confirmed_suspicion=approach_data.get("confirmed_suspicion", False),
        suspicion_level=approach_data.get("suspicion_level_slider"),
        has_incident=approach_data.get("has_incident", False),
        incident_notes=approach_data.get("notes"),
    )

    # Tentar enviar ao sistema estadual (dev-mode retorna NOT_SENT)
    transmission_result = await transmit_ba_to_state_system(payload=payload)

    # Persistir BA
    ba = BoletimAtendimento(
        observation_id=observation.id,
        agent_id=current_user.id,
        agency_id=current_user.agency_id,
        plate_number=observation.plate_number,
        agent_name=current_user.full_name,
        approach_timestamp=payload.approach_timestamp,
        payload_json=payload.model_dump(mode="json"),
        transmission_status=transmission_result["status"],
        transmission_error=None if transmission_result["status"] != "error"
            else transmission_result.get("message"),
        transmitted_at=datetime.utcnow() if transmission_result["connected"] else None,
        external_protocol=transmission_result.get("external_protocol"),
    )
    db.add(ba)
    await db.flush()

    logger.info(
        "BA %s gerado para obs %s | placa %s | status=%s",
        ba.id,
        observation_id,
        observation.plate_number,
        ba.transmission_status,
    )

    return ba


# ---------------------------------------------------------------------------
# Processamento batch de BAs pendentes
# ---------------------------------------------------------------------------
async def process_ba_batch(
    db: AsyncSession,
    *,
    max_items: int = 50,
    force_retry_errors: bool = False,
) -> BABatchResult:
    """
    Busca BAs pendentes (PENDING, NOT_SENT, opcionalmente ERROR) e tenta
    transmiti-los em lote ao sistema estadual.

    Returns:
        BABatchResult com o resumo do lote.
    """
    statuses = [
        BATransmissionStatus.PENDING.value,
        BATransmissionStatus.NOT_SENT.value,
    ]
    if force_retry_errors:
        statuses.append(BATransmissionStatus.ERROR.value)

    result = await db.execute(
        select(BoletimAtendimento)
        .where(BoletimAtendimento.transmission_status.in_(statuses))
        .order_by(BoletimAtendimento.created_at)
        .limit(max_items)
    )
    pending_bas = result.scalars().all()

    if not pending_bas:
        return BABatchResult(
            batch_id=f"BA-BATCH-{uuid4().hex[:12].upper()}",
            total_processed=0,
            transmitted=0,
            errors=0,
            status="empty",
            details=[],
        )

    # Montar payloads a partir do JSON persistido
    payloads = []
    ba_map = {}  # observation_id -> BoletimAtendimento
    for ba in pending_bas:
        try:
            payload = BAPayload(**ba.payload_json)
            payloads.append(payload)
            ba_map[str(ba.observation_id)] = ba
        except Exception as e:
            logger.error("Erro ao montar payload do BA %s: %s", ba.id, e)
            ba.transmission_status = BATransmissionStatus.ERROR.value
            ba.transmission_error = f"Payload inválido: {e}"

    # Enviar batch
    batch_result = await transmit_ba_batch(payloads=payloads)

    # Atualizar status de cada BA
    details = []
    for item_result in batch_result.get("results", []):
        obs_id = item_result.get("observation_id")
        ba = ba_map.get(obs_id)
        if ba is None:
            continue
        ba.transmission_status = item_result["status"]
        ba.batch_id = batch_result["batch_id"]
        if item_result["status"] == BATransmissionStatus.TRANSMITTED.value:
            ba.transmitted_at = datetime.utcnow()
            ba.external_protocol = item_result.get("external_protocol")
        elif item_result["status"] in (
            BATransmissionStatus.ERROR.value,
            BATransmissionStatus.REJECTED.value,
        ):
            ba.transmission_error = item_result.get("message")
        details.append({
            "ba_id": str(ba.id),
            "observation_id": obs_id,
            "status": item_result["status"],
        })

    await db.flush()

    return BABatchResult(
        batch_id=batch_result["batch_id"],
        total_processed=len(payloads),
        transmitted=batch_result["transmitted"],
        errors=batch_result["errors"],
        status="completed",
        details=details,
    )


# ---------------------------------------------------------------------------
# Consultas
# ---------------------------------------------------------------------------
async def list_bas(
    db: AsyncSession,
    *,
    agent_id: Optional[UUID] = None,
    status: Optional[BATransmissionStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> BAListResponse:
    """Lista BAs com filtros opcionais."""
    query = select(BoletimAtendimento).order_by(
        desc(BoletimAtendimento.created_at)
    )

    if agent_id:
        query = query.where(BoletimAtendimento.agent_id == agent_id)
    if status:
        query = query.where(
            BoletimAtendimento.transmission_status == status.value
        )

    count_query = select(func.count(BoletimAtendimento.id))
    if agent_id:
        count_query = count_query.where(BoletimAtendimento.agent_id == agent_id)

    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(BoletimAtendimento.id)).where(
            BoletimAtendimento.transmission_status.in_([
                BATransmissionStatus.PENDING.value,
                BATransmissionStatus.NOT_SENT.value,
            ])
        )
    )
    pending_count = pending_result.scalar() or 0

    transmitted_result = await db.execute(
        select(func.count(BoletimAtendimento.id)).where(
            BoletimAtendimento.transmission_status
            == BATransmissionStatus.TRANSMITTED.value
        )
    )
    transmitted_count = transmitted_result.scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    items = [
        BARecord(
            id=ba.id,
            observation_id=ba.observation_id,
            plate_number=ba.plate_number,
            agent_name=ba.agent_name,
            approach_timestamp=ba.approach_timestamp,
            transmission_status=ba.transmission_status,
            transmitted_at=ba.transmitted_at,
            transmission_error=ba.transmission_error,
            batch_id=ba.batch_id,
            created_at=ba.created_at,
            updated_at=ba.updated_at,
        )
        for ba in result.scalars().all()
    ]

    return BAListResponse(
        items=items,
        total_count=total_count,
        pending_count=pending_count,
        transmitted_count=transmitted_count,
    )


async def get_ba_by_observation(
    db: AsyncSession,
    observation_id: UUID,
) -> Optional[BoletimAtendimento]:
    """Busca BA pela observação vinculada."""
    result = await db.execute(
        select(BoletimAtendimento).where(
            BoletimAtendimento.observation_id == observation_id
        )
    )
    return result.scalar_one_or_none()
