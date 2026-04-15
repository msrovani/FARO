"""
State registry adapter boundary.

This module is intentionally separated so the real state-level integration
can be implemented without touching operational service flow.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


async def query_state_vehicle_registry(*, plate_number: str) -> dict[str, Any]:
    """
    Development fallback while state registry integration is not available.
    """
    return {
        "provider": "state_vehicle_registry_adapter",
        "plate_number": plate_number,
        "connected": False,
        "status": "no_connection",
        "message": "sem conexao com base estadual",
        "queried_at": datetime.utcnow().isoformat(),
    }
