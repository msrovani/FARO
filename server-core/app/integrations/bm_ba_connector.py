"""
F.A.R.O. Integrations — Conector BM / Boletim de Atendimento

Boundary adapter para comunicação com o sistema estadual da Brigada Militar.

STATUS ATUAL: DEV-MODE (sem conexão com sistema externo).
    - Em modo DEV: salva BA localmente com TTL de 7 dias.
    - Quando a integração real for implementada, apenas este módulo
      precisará ser alterado. O restante do fluxo (service, endpoints)
      permanece intacto.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.boletim_atendimento import BAPayload, BATransmissionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuração do conector (a ser externalizada via env/config)
# ---------------------------------------------------------------------------
BM_SYSTEM_ENDPOINT: Optional[str] = None  # Ex.: "https://bm.rs.gov.br/api/ba"
BM_SYSTEM_CONNECTED: bool = False  # Flag de dev-mode
DEV_MODE: bool = True  # Quando True, salva localmente com TTL
BA_LOCAL_TTL_DAYS: int = 7  # Tempo de vida do BA local


# ---------------------------------------------------------------------------
# Armazenamento local em memória (DEV-MODE)
# ---------------------------------------------------------------------------
class BALocalStorage:
    """In-memory storage for BAs with TTL."""

    def __init__(self, ttl_days: int = 7):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._ttl_days = ttl_days
        self._cleanup_task: Optional[asyncio.Task] = None

    def _get_key(self, observation_id: str) -> str:
        return f"ba:{observation_id}"

    def _is_expired(self, created_at: datetime) -> bool:
        expiry = created_at + timedelta(days=self._ttl_days)
        return datetime.utcnow() > expiry

    async def save(
        self, payload: BAPayload, transmission_result: Dict[str, Any]
    ) -> str:
        """Save BA locally with TTL."""
        key = self._get_key(str(payload.observation_id))
        self._store[key] = {
            "observation_id": str(payload.observation_id),
            "plate_number": payload.plate_number,
            "payload": payload.model_dump(mode="json"),
            "transmission_result": transmission_result,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=self._ttl_days),
        }

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        logger.info(
            "BA local storage: saved BA for observation %s (TTL: %d dias)",
            payload.observation_id,
            self._ttl_days,
        )
        return key

    async def get(self, observation_id: str) -> Optional[Dict[str, Any]]:
        """Get BA by observation ID."""
        key = self._get_key(observation_id)
        entry = self._store.get(key)

        if entry is None:
            return None

        if self._is_expired(entry["created_at"]):
            del self._store[key]
            logger.info(
                "BA local storage: expired BA for observation %s", observation_id
            )
            return None

        return entry

    async def list_pending(self) -> List[Dict[str, Any]]:
        """List all BAs that haven't been transmitted."""
        pending = []
        expired_keys = []

        for key, entry in self._store.items():
            if self._is_expired(entry["created_at"]):
                expired_keys.append(key)
                continue

            if (
                entry["transmission_result"].get("status")
                != BATransmissionStatus.TRANSMITTED.value
            ):
                pending.append(entry)

        for key in expired_keys:
            del self._store[key]

        return pending

    async def list_all(self) -> List[Dict[str, Any]]:
        """List all stored BAs."""
        await self._periodic_cleanup()
        return list(self._store.values())

    async def delete(self, observation_id: str) -> bool:
        """Delete a specific BA."""
        key = self._get_key(observation_id)
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def _periodic_cleanup(self) -> None:
        """Periodically clean expired entries."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                expired_keys = [
                    key
                    for key, entry in self._store.items()
                    if self._is_expired(entry["created_at"])
                ]
                for key in expired_keys:
                    del self._store[key]

                if expired_keys:
                    logger.info(
                        "BA local storage: cleaned %d expired entries",
                        len(expired_keys),
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("BA local storage cleanup error: %s", e)


ba_local_storage = BALocalStorage(ttl_days=BA_LOCAL_TTL_DAYS)


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
        # Salva localmente em modo DEV
        transmission_result = {
            "provider": "bm_ba_connector",
            "connected": False,
            "status": BATransmissionStatus.NOT_SENT.value,
            "external_protocol": None,
            "message": "Sem conexão com sistema estadual (dev-mode). "
            "BA registrado localmente para envio futuro.",
            "transmitted_at": datetime.utcnow().isoformat(),
        }

        if DEV_MODE:
            try:
                await ba_local_storage.save(payload, transmission_result)
                logger.info(
                    "BA connector [dev-mode]: BA para observação %s salvo localmente (TTL: %d dias)",
                    payload.observation_id,
                    BA_LOCAL_TTL_DAYS,
                )
            except Exception as e:
                logger.error(
                    "BA connector [dev-mode]: erro ao salvar localmente: %s", e
                )

        logger.info(
            "BA connector [dev-mode]: BA para observação %s NÃO enviado (sem conexão)",
            payload.observation_id,
        )
        return transmission_result

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
        results.append(
            {
                "observation_id": str(payload.observation_id),
                "plate_number": payload.plate_number,
                **result,
            }
        )

    transmitted = sum(
        1 for r in results if r["status"] == BATransmissionStatus.TRANSMITTED.value
    )
    errors = sum(
        1
        for r in results
        if r["status"]
        in (
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
