"""
F.A.R.O. API — Boletim de Atendimento (BA)

Endpoints para consulta, reenvio e processamento batch de Boletins
de Atendimento vinculados a abordagens de campo.

NOTE: A geração do BA é acionada automaticamente pelo endpoint de
      approach confirmation em mobile.py. Os endpoints aqui servem
      para gestão e auditoria pela Intelligence Console.
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.db.base import User, UserRole
from app.db.session import get_db
from app.schemas.boletim_atendimento import (
    BABatchRequest,
    BABatchResult,
    BAListResponse,
    BARecord,
    BATransmissionStatus,
)
from app.services import ba_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Role guards
# ---------------------------------------------------------------------------
def require_supervisor_or_intelligence(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requer papel de supervisor, inteligência ou admin."""
    allowed = {UserRole.SUPERVISOR, UserRole.INTELLIGENCE, UserRole.ADMIN}
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a supervisores, analistas ou administradores.",
        )
    return current_user


# ---------------------------------------------------------------------------
# Listagem de BAs
# ---------------------------------------------------------------------------
@router.get(
    "/ba",
    response_model=BAListResponse,
    summary="Listar Boletins de Atendimento",
    description=(
        "Retorna lista paginada de BAs com contadores de status. "
        "Filtrável por agente e status de transmissão."
    ),
)
async def list_boletins(
    agent_id: Optional[UUID] = Query(None, description="Filtrar por agente"),
    status: Optional[BATransmissionStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_intelligence),
):
    return await ba_service.list_bas(
        db,
        agent_id=agent_id,
        status=status,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Detail por observação
# ---------------------------------------------------------------------------
@router.get(
    "/ba/observation/{observation_id}",
    response_model=BARecord,
    summary="Consultar BA por observação",
    description="Retorna o BA vinculado a uma observação/abordagem específica.",
)
async def get_ba_by_observation(
    observation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_intelligence),
):
    ba = await ba_service.get_ba_by_observation(db, observation_id)
    if ba is None:
        raise HTTPException(
            status_code=404,
            detail=f"BA não encontrado para observação {observation_id}.",
        )
    return BARecord(
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


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------
@router.post(
    "/ba/batch",
    response_model=BABatchResult,
    summary="Processar lote de BAs pendentes",
    description=(
        "Busca BAs com status PENDING/NOT_SENT e tenta transmitir em lote "
        "ao sistema estadual. Em dev-mode, todos retornam NOT_SENT. "
        "Use force_retry_errors=true para incluir BAs com falha anterior."
    ),
)
async def process_batch(
    request: BABatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_intelligence),
):
    result = await ba_service.process_ba_batch(
        db,
        max_items=request.max_items,
        force_retry_errors=request.force_retry_errors,
    )
    await db.commit()
    return result


# ---------------------------------------------------------------------------
# Status summary
# ---------------------------------------------------------------------------
@router.get(
    "/ba/status",
    summary="Resumo de status dos BAs",
    description="Retorna contadores agregados por status de transmissão.",
)
async def ba_status_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_intelligence),
):
    from sqlalchemy import func, select
    from app.db.base import BoletimAtendimento

    result = await db.execute(
        select(
            BoletimAtendimento.transmission_status,
            func.count(BoletimAtendimento.id),
        ).group_by(BoletimAtendimento.transmission_status)
    )

    status_counts = {status: count for status, count in result.all()}

    return {
        "total": sum(status_counts.values()),
        "by_status": status_counts,
        "connector_active": False,  # dev-mode
        "message": "Conector BM em modo desenvolvimento. BAs pendentes serão "
                   "transmitidos quando a integração for ativada.",
    }
