"""
Redis Streams worker for asynchronous FARO analytical processing.
"""
from __future__ import annotations

import asyncio
import json
import logging
import socket
from dataclasses import dataclass
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError, ResponseError

from app.core.config import settings
from app.workers.analytics_worker import reprocess_observation


logger = logging.getLogger(__name__)


@dataclass
class StreamMessage:
    stream: str
    message_id: str
    fields: dict[str, str]


class AnalyticsStreamWorker:
    def __init__(self) -> None:
        self._client: Redis | None = None
        self._running = False
        self._consumer_name = (
            settings.redis_stream_consumer_name
            or f"{socket.gethostname()}-{id(self)}"
        )

    async def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                settings.redis_streams_url,
                decode_responses=True,
                socket_timeout=settings.redis_socket_timeout,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
            )
        return self._client

    async def _ensure_group(self) -> None:
        client = await self._get_client()
        try:
            await client.xgroup_create(
                name=settings.redis_stream_key,
                groupname=settings.redis_stream_group,
                id="$",
                mkstream=True,
            )
            logger.info(
                "Grupo Redis criado",
                extra={
                    "stream": settings.redis_stream_key,
                    "group": settings.redis_stream_group,
                },
            )
        except ResponseError as exc:
            if "BUSYGROUP" in str(exc):
                return
            raise

    async def _read_batch(self) -> list[StreamMessage]:
        client = await self._get_client()
        raw_messages = await client.xreadgroup(
            groupname=settings.redis_stream_group,
            consumername=self._consumer_name,
            streams={settings.redis_stream_key: ">"},
            count=settings.redis_stream_batch_size,
            block=settings.redis_stream_block_ms,
        )
        items: list[StreamMessage] = []
        for stream_name, entries in raw_messages:
            for message_id, fields in entries:
                items.append(
                    StreamMessage(
                        stream=stream_name,
                        message_id=message_id,
                        fields=fields,
                    )
                )
        return items

    async def _ack(self, message: StreamMessage) -> None:
        client = await self._get_client()
        await client.xack(
            message.stream,
            settings.redis_stream_group,
            message.message_id,
        )

    @staticmethod
    def _parse_payload(raw_payload: str | None) -> dict:
        if not raw_payload:
            return {}
        try:
            parsed = json.loads(raw_payload)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _to_uuid(value: str | None) -> UUID | None:
        if not value:
            return None
        try:
            return UUID(value)
        except (TypeError, ValueError):
            return None

    async def _handle_message(self, message: StreamMessage) -> None:
        event_name = message.fields.get("event_name", "")
        payload = self._parse_payload(message.fields.get("payload"))
        observation_id: UUID | None = None

        if event_name == "observation_created":
            observation_id = self._to_uuid(payload.get("observation_id"))
        elif event_name == "sync_completed":
            is_observation = payload.get("entity_type") == "observation"
            is_completed = payload.get("status") == "completed"
            if is_observation and is_completed:
                observation_id = self._to_uuid(payload.get("entity_server_id"))

        if observation_id is None:
            return

        reprocessed_id = await reprocess_observation(observation_id)
        if reprocessed_id is not None:
            logger.info(
                "Reprocessamento analitico executado",
                extra={
                    "event_name": event_name,
                    "observation_id": str(reprocessed_id),
                    "message_id": message.message_id,
                },
            )

    async def run(self) -> None:
        if not settings.redis_streams_enabled:
            logger.warning("Worker de streams desabilitado por configuracao")
            return

        self._running = True
        await self._ensure_group()
        logger.info(
            "Worker de streams iniciado",
            extra={
                "stream": settings.redis_stream_key,
                "group": settings.redis_stream_group,
                "consumer": self._consumer_name,
            },
        )

        while self._running:
            try:
                batch = await self._read_batch()
                for message in batch:
                    try:
                        await self._handle_message(message)
                    finally:
                        # Evita mensagem presa no pending list por erro de parser/evento.
                        await self._ack(message)
            except RedisError as exc:
                logger.warning("Erro de Redis no worker de streams: %s", exc)
                await asyncio.sleep(settings.redis_stream_error_backoff_seconds)
            except asyncio.CancelledError:
                self._running = False
                raise
            except Exception as exc:
                logger.exception("Falha inesperada no worker de streams: %s", exc)
                await asyncio.sleep(settings.redis_stream_error_backoff_seconds)

        await self.shutdown()

    async def shutdown(self) -> None:
        self._running = False
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None


async def main() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    worker = AnalyticsStreamWorker()
    try:
        await worker.run()
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
