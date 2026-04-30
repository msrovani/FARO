"""
Simple in-memory rate limiting middleware for development and baseline abuse protection.

For production clusters, this should be replaced by a shared store limiter (Redis/Nginx/Traefik).
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class Bucket:
    timestamps: Deque[float]


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        requests: int,
        window_seconds: int,
        exempt_paths: set[str] | None = None,
    ):
        super().__init__(app)
        self.requests = max(1, requests)
        self.window_seconds = max(1, window_seconds)
        self.exempt_paths = exempt_paths or set()
        self._buckets: dict[str, Bucket] = {}
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if self._is_exempt(path):
            return await call_next(request)

        key = self._build_key(request)
        now = time.time()

        async with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = Bucket(timestamps=deque())
                self._buckets[key] = bucket

            cutoff = now - self.window_seconds
            while bucket.timestamps and bucket.timestamps[0] < cutoff:
                bucket.timestamps.popleft()

            if len(bucket.timestamps) >= self.requests:
                retry_after = int(
                    max(1, self.window_seconds - (now - bucket.timestamps[0]))
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Muitas Requisições",
                        "message": "Limite de requisicoes excedido. Tente novamente em instantes.",
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.timestamps.append(now)

            # Avoid unbounded growth: remove stale buckets.
            if len(self._buckets) > 10_000:
                keys_to_remove = [
                    bucket_key
                    for bucket_key, bucket_value in self._buckets.items()
                    if not bucket_value.timestamps
                    or bucket_value.timestamps[-1] < cutoff
                ]
                for bucket_key in keys_to_remove:
                    self._buckets.pop(bucket_key, None)

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        if path in self.exempt_paths:
            return True
        return (
            path.startswith("/docs")
            or path.startswith("/redoc")
            or path.startswith("/openapi.json")
        )

    @staticmethod
    def _build_key(request: Request) -> str:
        auth = request.headers.get("authorization")
        if auth:
            token = auth[-24:]
            return f"token:{token}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"
