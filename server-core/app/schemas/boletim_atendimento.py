"""
F.A.R.O. Schemas — Boletim de Atendimento (BA)

Define os DTOs para geração, consulta e envio de Boletins de Atendimento
ao sistema estadual da Brigada Militar.

Cada abordagem concluída pelo agente de campo gera exatamente 1 BA.
O pacote de dados será definido em conjunto com a especificação da BM,
mas os campos estruturais já estão mapeados aqui para permitir
desenvolvimento iterativo.

Workflow:
    abordagem concluída → BA gerado (status PENDING) → batch enviado ao
    sistema estadual → confirmação ou reenvio.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enum de status do envio
# ---------------------------------------------------------------------------
class BATransmissionStatus(str, PyEnum):
    """Ciclo de vida do envio de um BA ao sistema estadual."""
    PENDING = "pending"              # Gerado, aguardando envio
    QUEUED = "queued"                # Na fila do batch
    TRANSMITTED = "transmitted"      # Enviado com sucesso
    REJECTED = "rejected"            # Rejeitado pelo sistema estadual
    ERROR = "error"                  # Falha de comunicacao
    NOT_SENT = "not_sent"            # Dev-mode: sem conexao com o destino


# ---------------------------------------------------------------------------
# Payload do BA (pacote de dados a ser definido com a BM)
# ---------------------------------------------------------------------------
class BAPayload(BaseModel):
    """
    Pacote de dados que compõe o BA enviado ao sistema estadual.

    IMPORTANT: Os campos abaixo são um esqueleto inicial.
    O formato final será alinhado com a especificação do sistema da
    Brigada Militar. Campos marcados como Optional podem se tornar
    obrigatórios conforme a definição do pacote.
    """
    model_config = ConfigDict(from_attributes=True)

    # --- Identificação da abordagem ---
    observation_id: UUID
    approach_timestamp: datetime
    agent_badge_number: Optional[str] = None
    agent_full_name: str
    unit_code: Optional[str] = None
    agency_code: Optional[str] = None

    # --- Dados do veículo ---
    plate_number: str
    plate_state: Optional[str] = None
    vehicle_color: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None

    # --- Localização ---
    latitude: float
    longitude: float
    street_direction: Optional[str] = None

    # --- Resultado operacional ---
    approach_outcome: str = Field(
        default="approached",
        description="Resultado da abordagem: approached, no_approach, incident, etc.",
    )
    confirmed_suspicion: bool = False
    suspicion_level: Optional[int] = Field(
        None, ge=0, le=100,
        description="Nível de suspeição informado pelo agente (0-100)",
    )
    has_incident: bool = False
    incident_notes: Optional[str] = None

    # --- Envelope para dados adicionais da BM (a definir) ---
    extended_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Campos adicionais conforme pacote BM — a ser definido.",
    )


# ---------------------------------------------------------------------------
# Schemas de resposta / listagem
# ---------------------------------------------------------------------------
class BARecord(BaseModel):
    """Representação de um BA persistido no sistema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: UUID
    plate_number: str
    agent_name: str
    approach_timestamp: datetime
    transmission_status: BATransmissionStatus
    transmitted_at: Optional[datetime] = None
    transmission_error: Optional[str] = None
    batch_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BAListResponse(BaseModel):
    """Resposta paginada de BAs."""
    items: List[BARecord]
    total_count: int
    pending_count: int
    transmitted_count: int


class BABatchRequest(BaseModel):
    """Solicitação para processar lote de BAs pendentes."""
    max_items: int = Field(default=50, ge=1, le=500)
    force_retry_errors: bool = Field(
        default=False,
        description="Se True, inclui BAs com status ERROR para reenvio.",
    )


class BABatchResult(BaseModel):
    """Resultado de um processamento batch de BAs."""
    batch_id: str
    total_processed: int
    transmitted: int
    errors: int
    status: str
    details: List[Dict[str, Any]] = []
