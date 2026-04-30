from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import InMemoryRateLimitMiddleware


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        InMemoryRateLimitMiddleware,
        requests=2,
        window_seconds=60,
        exempt_paths=set(),
    )

    @app.get("/limited")
    async def limited() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_rate_limit_blocks_after_threshold() -> None:
    app = _build_test_app()

    with TestClient(app) as client:
        first = client.get("/limited")
        second = client.get("/limited")
        third = client.get("/limited")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert "Retry-After" in third.headers
