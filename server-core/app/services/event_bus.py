"""
Minimal Redis Streams publisher for internal FARO events.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings


logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._client: Redis | None = None

    async def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                settings.redis_streams_url,
                decode_responses=True,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
            )
        return self._client

    async def publish(self, event_name: str, payload: dict[str, Any]) -> bool:
        if not settings.redis_streams_enabled:
            return False
        try:
            client = await self._get_client()
            envelope = {
                "event_name": event_name,
                "payload_version": payload.get("payload_version", "v1"),
                "published_at": datetime.utcnow().isoformat(),
                "payload": json.dumps(payload, default=str),
            }
            await client.xadd(
                settings.redis_stream_key,
                envelope,
                maxlen=10000,
                approximate=True,
            )
            return True
        except RedisError as exc:
            logger.warning(
                "Redis Streams indisponivel para evento %s: %s",
                event_name,
                exc,
            )
            await self._reset_client()
            return False
        except Exception as exc:
            logger.exception(
                "Falha nao esperada ao publicar evento %s: %s", event_name, exc
            )
            await self._reset_client()
            return False

    async def _reset_client(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception as exc:
                logger.warning("Erro ao fechar Redis client no reset: %s", exc)
        self._client = None


event_bus = EventBus()
