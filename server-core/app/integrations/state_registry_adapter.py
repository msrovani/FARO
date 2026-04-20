"""
State registry adapter boundary - DETRAN/RENAVAM.

This module provides vehicle registration data from the state database.
In DEV-MODE, returns mock data based on plate pattern.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import Any


# DEV-MODE: Mock data patterns
MOCK_PLATE_PREFIXES = [
    "AAA",
    "BBB",
    "CCC",
    "DDD",
    "EEE",
    "FFF",
    "GGG",
    "HHH",
    "III",
    "JJJ",
]
MOCK_OWNERS = [
    "SILVA SOUZA",
    "SANTOS OLIVEIRA",
    "PEREIRA RODRIGUES",
    "ALMEIDA MACHADO",
    "FERREIRA LIMA",
    "CARVALHO DIAS",
    "RODRIGUES MARTINS",
    "ANDRADE FERREIRA",
    "SOUZA NETO",
    "LIMA CASTRO",
]
MOCK_MODELS = [
    ("FIAT", "PALIO"),
    ("FIAT", "UNO"),
    ("VOLKSWAGEN", "GOL"),
    ("VOLKSWAGEN", "POLO"),
    ("CHEVROLET", "ONIX"),
    ("CHEVROLET", "PRISMA"),
    ("FORD", "KA"),
    ("FORD", "FIESTA"),
    ("TOYOTA", "COROLLA"),
    ("HONDA", "CIVIC"),
    ("RENAULT", "LOGAN"),
    ("NISSAN", "FRONTIER"),
]
MOCK_COLORS = ["BRANCA", "PRETA", "PRATA", "VERMELHA", "AZUL", "VERDE", "AMARELA"]


def _generate_mock_data(plate_number: str) -> dict[str, Any]:
    """Generate mock vehicle data based on plate pattern."""
    # Normalize plate
    normalized = plate_number.upper().replace("-", "").strip()

    # Generate consistent data based on plate hash
    random.seed(hash(normalized) % 1000000)

    prefix_idx = random.randint(0, len(MOCK_PLATE_PREFIXES) - 1)
    owner_idx = random.randint(0, len(MOCK_OWNERS) - 1)
    model_idx = random.randint(0, len(MOCK_MODELS) - 1)
    color_idx = random.randint(0, len(MOCK_COLORS) - 1)
    year = random.randint(2015, 2024)

    # Determine plate type based on pattern
    if len(normalized) == 7:  # Mercosul: AAA-1A11
        plate_type = "mercosur"
    elif len(normalized) == 6 and normalized[:3].isalpha():  # Old: AAA1234
        plate_type = "old"
    else:
        plate_type = "unknown"

    return {
        "provider": "detran_rs_mock",
        "plate_number": plate_number.upper(),
        "connected": True,
        "status": "active",
        "message": "Dados retornados em modo desenvolvimento",
        "queried_at": datetime.utcnow().isoformat() + "Z",
        # Vehicle details
        "vehicle": {
            "owner": MOCK_OWNERS[owner_idx],
            "owner_cpf": f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}",
            "brand": MOCK_MODELS[model_idx][0],
            "model": MOCK_MODELS[model_idx][1],
            "year": year,
            "color": MOCK_COLORS[color_idx],
            "plate_type": plate_type,
        },
        # Registration status
        "registration": {
            "status": "regular",
            "status_code": 0,
            "message": "Veículo com IPVA pago",
            "ipva_expiry": f"{year + 1}-04-{random.randint(10, 28):02d}",
            "licensing_expiry": f"2026-{random.randint(1, 12):02d}-{random.randint(10, 28):02d}",
        },
        # Restrictions
        "restrictions": {
            "has_restrictions": False,
            "restriction_types": [],
        },
        # Theft status
        "theft": {
            "reported_stolen": False,
            "theft_report_date": None,
        },
    }


async def query_state_vehicle_registry(
    *,
    plate_number: str,
    use_mock: bool = True,
) -> dict[str, Any]:
    """
    Query state vehicle registry (DETRAN/RENAVAM).

    In DEV-MODE (use_mock=True), returns generated mock data.
    In production, would call actual DETRAN API.

    Args:
        plate_number: Vehicle plate to query (e.g., "AAA-1A11")
        use_mock: If True, return mock data (DEV-MODE)

    Returns:
        dict with vehicle registration details
    """
    if not plate_number:
        return {
            "provider": "detran_rs_mock",
            "connected": False,
            "status": "error",
            "message": "Placa não fornecida",
            "queried_at": datetime.utcnow().isoformat() + "Z",
        }

    if use_mock:
        return _generate_mock_data(plate_number)

    # PRODUCTION: Would call actual DETRAN API
    # Example:
    # async with httpx.AsyncClient(timeout=30.0) as client:
    #     response = await client.post(
    #         f"{DETRAN_ENDPOINT}/consulta/veiculo",
    #         json={"placa": plate_number},
    #         headers={"Authorization": f"Bearer {token}"}
    #     )
    #     return response.json()

    # For now, if not using mock, return error
    return {
        "provider": "detran_rs",
        "plate_number": plate_number.upper(),
        "connected": False,
        "status": "not_configured",
        "message": "DETRAN integration not configured. Use use_mock=True for dev-mode.",
        "queried_at": datetime.utcnow().isoformat() + "Z",
    }


async def query_renavam_by_chassi(
    *,
    chassi: str,
    use_mock: bool = True,
) -> dict[str, Any]:
    """
    Query vehicle by chassis number (RENAVAM).

    Args:
        chassi: 17-character chassis/VIN number
        use_mock: If True, return mock data (DEV-MODE)

    Returns:
        dict with vehicle details from RENAVAM
    """
    if not chassi or len(chassi) < 17:
        return {
            "provider": "renavam_mock",
            "connected": False,
            "status": "error",
            "message": "Chassi inválido",
            "queried_at": datetime.utcnow().isoformat() + "Z",
        }

    if use_mock:
        random.seed(hash(chassi[:8]) % 1000000)
        owner_idx = random.randint(0, len(MOCK_OWNERS) - 1)
        model_idx = random.randint(0, len(MOCK_MODELS) - 1)

        return {
            "provider": "renavam_mock",
            "chassi": chassi.upper(),
            "connected": True,
            "status": "active",
            "message": "Dados retornados em modo desenvolvimento",
            "queried_at": datetime.utcnow().isoformat() + "Z",
            "vehicle": {
                "owner": MOCK_OWNERS[owner_idx],
                "brand": MOCK_MODELS[model_idx][0],
                "model": MOCK_MODELS[model_idx][1],
                "year": random.randint(2015, 2024),
                "chassi": chassi.upper(),
            },
        }

    # Production implementation would go here
    return {
        "provider": "renavam",
        "connected": False,
        "status": "not_configured",
        "message": "RENAVAM integration not configured",
        "queried_at": datetime.utcnow().isoformat() + "Z",
    }
