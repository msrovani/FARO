"""
F.A.R.O. Integrations — Conector BM / Boletim de Atendimento

Boundary adapter para comunicação com o sistema estadual da Brigada Militar.

STATUS ATUAL: DEV-MODE (sem conexão com sistema externo).
    - Todas as chamadas retornam `connected=False` e `status="not_sent"`.
    - Quando a integração real for implementada, apenas este módulo
      precisará ser alterado. O restante do fluxo (service, endpoints)
      permanece intacto.

Requisitos futuros:
    - Autenticação via certificado digital ou token OAuth2 da BM.
    - Formato de payload conforme pacote de dados da BM.
    - Envio síncrono ou assíncrono (batch) via REST/SOAP.
    - Tratamento de rejeição com código de erro da BM.
    - Retry com backoff exponencial e dead-letter queue.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.boletim_atendimento import BAPayload, BATransmissionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuração do conector (a ser externalizada via env/config)
# ---------------------------------------------------------------------------
BM_SYSTEM_ENDPOINT: Optional[str] = None  # Ex.: "https://bm.rs.gov.br/api/ba"
BM_SYSTEM_CONNECTED: bool = False  # Flag de dev-mode


# ---------------------------------------------------------------------------
# Envio unitário
# ---------------------------------------------------------------------------
async def transmit_ba_to_state_system(
    *,
    payload: BAPayload,
) -> Dict[str, Any]:
    """
    Envia um único Boletim de Atendimento ao sistema estadual.

    Em dev-mode, retorna NOT_SENT sem efetuar chamada externa.
    Quando a integração estiver ativa, este método realizará a
    chamada HTTP/SOAP ao endpoint da BM e retornará o resultado.

    Returns:
        dict com chaves:
            - provider: identificador do conector
            - connected: se houve conexão real
            - status: resultado do envio
            - external_protocol: protocolo externo (quando disponível)
            - message: mensagem legível
            - transmitted_at: timestamp do envio
    """
    if not BM_SYSTEM_CONNECTED or BM_SYSTEM_ENDPOINT is None:
        logger.info(
            "BA connector [dev-mode]: BA para observação %s NÃO enviado (sem conexão)",
            payload.observation_id,
        )
        return {
            "provider": "bm_ba_connector",
            "connected": False,
            "status": BATransmissionStatus.NOT_SENT.value,
            "external_protocol": None,
            "message": "Sem conexão com sistema estadual (dev-mode). "
                       "BA registrado localmente para envio futuro.",
            "transmitted_at": datetime.utcnow().isoformat(),
        }

    # ----- IMPLEMENTAÇÃO FUTURA -----
    # Aqui entraria a chamada real:
    #
    # async with httpx.AsyncClient(
    #     base_url=BM_SYSTEM_ENDPOINT,
    #     cert=("/path/to/cert.pem", "/path/to/key.pem"),
    #     timeout=30.0,
    # ) as client:
    #     response = await client.post(
    #         "/ba/registrar",
    #         json=payload.model_dump(mode="json"),
    #     )
    #     if response.status_code == 200:
    #         data = response.json()
    #         return {
    #             "provider": "bm_ba_connector",
    #             "connected": True,
    #             "status": BATransmissionStatus.TRANSMITTED.value,
    #             "external_protocol": data.get("protocolo"),
    #             "message": "BA transmitido com sucesso ao sistema estadual.",
    #             "transmitted_at": datetime.utcnow().isoformat(),
    #         }
    #     else:
    #         return {
    #             "provider": "bm_ba_connector",
    #             "connected": True,
    #             "status": BATransmissionStatus.REJECTED.value,
    #             "external_protocol": None,
    #             "message": f"Rejeitado pelo sistema estadual: {response.text}",
    #             "transmitted_at": datetime.utcnow().isoformat(),
    #         }
    # -----------------------------------

    # Fallback de segurança (não deveria ser alcançado)
    return {
        "provider": "bm_ba_connector",
        "connected": False,
        "status": BATransmissionStatus.ERROR.value,
        "external_protocol": None,
        "message": "Conector configurado mas sem implementação de envio.",
        "transmitted_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Envio em lote (batch)
# ---------------------------------------------------------------------------
async def transmit_ba_batch(
    *,
    payloads: List[BAPayload],
) -> Dict[str, Any]:
    """
    Envia um lote de BAs ao sistema estadual.

    Em dev-mode, marca todos como NOT_SENT.
    Quando implementado, agrupa os payloads e envia em uma única
    chamada ou em chunks conforme limite do endpoint da BM.

    Returns:
        dict com chaves:
            - batch_id: identificador do lote
            - total: quantidade de BAs no lote
            - transmitted: quantidade enviada com sucesso
            - errors: quantidade com falha
            - results: lista de resultados individuais
    """
    batch_id = f"BA-BATCH-{uuid4().hex[:12].upper()}"

    results = []
    for payload in payloads:
        result = await transmit_ba_to_state_system(payload=payload)
        results.append({
            "observation_id": str(payload.observation_id),
            "plate_number": payload.plate_number,
            **result,
        })

    transmitted = sum(
        1 for r in results
        if r["status"] == BATransmissionStatus.TRANSMITTED.value
    )
    errors = sum(
        1 for r in results
        if r["status"] in (
            BATransmissionStatus.ERROR.value,
            BATransmissionStatus.REJECTED.value,
        )
    )

    logger.info(
        "BA batch %s: %d total, %d transmitted, %d errors, %d not_sent",
        batch_id,
        len(payloads),
        transmitted,
        errors,
        len(payloads) - transmitted - errors,
    )

    return {
        "batch_id": batch_id,
        "total": len(payloads),
        "transmitted": transmitted,
        "errors": errors,
        "results": results,
    }
