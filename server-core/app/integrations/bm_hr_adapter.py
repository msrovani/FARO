"""
BM HR Adapter - Recursos Humanos da Brigada Militar.

Validates operational credentials against BM HR database.
In DEV-MODE, returns OK for any valid CPF format.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


BM_HR_ENDPOINT: Optional[str] = None
BM_HR_CONNECTED: bool = False
DEV_MODE: bool = True


MOCK_UNITS = [
    {
        "code": "1º BPM",
        "name": "1º Batalhão de Policamento Militar",
        "city": "Porto Alegre",
    },
    {
        "code": "2º BPM",
        "name": "2º Batalhão de Policamento Militar",
        "city": "Caxias do Sul",
    },
    {"code": "3º BPM", "name": "3º Batalhão de Policamento Militar", "city": "Pelotas"},
    {
        "code": "4º BPM",
        "name": "4º Batalhão de Policamento Militar",
        "city": "Santa Maria",
    },
    {"code": "5º BPM", "name": "5º Batalhão de Policamento Militar", "city": "Canoas"},
    {
        "code": "1º RPMon",
        "name": "1º Regimento de Policiamento Montado",
        "city": "Porto Alegre",
    },
    {
        "code": "2º RPMon",
        "name": "2º Regimento de Policiamento Montado",
        "city": "Pelotas",
    },
    {
        "code": "BOPE",
        "name": "Batalhão de Operações Policiais Especiais",
        "city": "Porto Alegre",
    },
    {
        "code": "BPChoque",
        "name": "Batalhão de Policiamento de Choque",
        "city": "Porto Alegre",
    },
    {
        "code": "BPAT",
        "name": "Batalhão de Policiamento de Áreas Turísticas",
        "city": "Gramado",
    },
]

MOCK_RANKS = [
    "Soldado",
    "Cabo",
    "Sargento",
    "Subtenente",
    "Tenente",
    "Capitão",
    "Major",
    "Tenente-Coronel",
    "Coronel",
]


def _validate_cpf(cpf: str) -> bool:
    """Validate CPF format (not algorithm)."""
    digits = re.sub(r"\D", "", cpf)
    return len(digits) == 11


def _generate_mock_hr_data(
    cpf: str, badge_number: Optional[str] = None
) -> dict[str, Any]:
    """Generate mock HR data for a PM."""
    import random

    random.seed(hash(cpf) % 1000000)

    unit_idx = random.randint(0, len(MOCK_UNITS) - 1)
    rank_idx = random.randint(0, len(MOCK_RANKS) - 3)  # Prefer lower ranks

    badge = (
        badge_number
        if badge_number
        else f"{random.randint(100, 999)}-{random.randint(100, 999)}"
    )

    return {
        "provider": "bm_hr_mock",
        "connected": True,
        "status": "active",
        "message": "Dados retornados em modo desenvolvimento",
        "verified_at": datetime.utcnow().isoformat() + "Z",
        "cpf": cpf,
        "badge_number": badge,
        "operational": {
            "name": f"SOLDADO PM {random.choice(['SILVA', 'SANTOS', 'OLIVEIRA', 'PEREIRA'])}",
            "rank": MOCK_RANKS[rank_idx],
            "unit": MOCK_UNITS[unit_idx],
            "status": "active",
            "status_code": 1,
            "status_message": "Ativo no serviço",
        },
        "credentials": {
            "badge_valid": True,
            "credential_expiry": f"2027-12-31",
            "weapon_permit": True,
            "vehicle_permit": True,
        },
    }


async def verify_bm_operational(
    *,
    cpf: str,
    badge_number: Optional[str] = None,
    dev_mode: bool = True,
) -> dict[str, Any]:
    """
    Verify if CPF belongs to an active BM operational.

    In DEV-MODE (dev_mode=True), returns OK for any valid CPF.
    In production, would query BM HR database.

    Args:
        cpf: CPF number (with or without formatting)
        badge_number: Optional badge/matrícula number
        dev_mode: If True, use mock data

    Returns:
        dict with operational verification result
    """
    if not cpf:
        return {
            "provider": "bm_hr_mock",
            "connected": False,
            "status": "error",
            "message": "CPF não fornecido",
            "verified_at": datetime.utcnow().isoformat() + "Z",
        }

    if not _validate_cpf(cpf):
        return {
            "provider": "bm_hr_mock",
            "connected": False,
            "status": "error",
            "message": "CPF inválido",
            "verified_at": datetime.utcnow().isoformat() + "Z",
        }

    if dev_mode or DEV_MODE:
        return _generate_mock_hr_data(cpf, badge_number)

    # PRODUCTION: Would call actual BM HR API
    # Example:
    # async with httpx.AsyncClient(timeout=30.0) as client:
    #     response = await client.post(
    #         f"{BM_HR_ENDPOINT}/api/operacional/verificar",
    #         json={"cpf": cpf, "matricula": badge_number},
    #         headers={"Authorization": f"Bearer {token}"}
    #     )
    #     return response.json()

    return {
        "provider": "bm_hr",
        "connected": False,
        "status": "not_configured",
        "message": "BM HR integration not configured. Use dev_mode=True for dev-mode.",
        "verified_at": datetime.utcnow().isoformat() + "Z",
    }


async def get_operational_by_badge(
    *,
    badge_number: str,
    dev_mode: bool = True,
) -> dict[str, Any]:
    """
    Get operational details by badge/matrícula number.

    Args:
        badge_number: Badge/matrícula (e.g., "1234-5678")
        dev_mode: If True, use mock data

    Returns:
        dict with operational details
    """
    if not badge_number:
        return {
            "provider": "bm_hr_mock",
            "connected": False,
            "status": "error",
            "message": "Matrícula não fornecida",
            "verified_at": datetime.utcnow().isoformat() + "Z",
        }

    if dev_mode or DEV_MODE:
        import random

        random.seed(hash(badge_number) % 1000000)

        unit_idx = random.randint(0, len(MOCK_UNITS) - 1)
        rank_idx = random.randint(0, len(MOCK_RANKS) - 3)

        return {
            "provider": "bm_hr_mock",
            "connected": True,
            "status": "active",
            "message": "Dados retornados em modo desenvolvimento",
            "verified_at": datetime.utcnow().isoformat() + "Z",
            "badge_number": badge_number,
            "operational": {
                "name": f"PM {random.choice(['SILVA', 'SANTOS', 'OLIVEIRA', 'PEREIRA', 'CARVALHO'])}",
                "rank": MOCK_RANKS[rank_idx],
                "unit": MOCK_UNITS[unit_idx],
                "status": "active",
            },
        }

    return {
        "provider": "bm_hr",
        "connected": False,
        "status": "not_configured",
        "message": "BM HR integration not configured",
        "verified_at": datetime.utcnow().isoformat() + "Z",
    }


async def list_active_operationals(
    *,
    unit_code: Optional[str] = None,
    dev_mode: bool = True,
) -> dict[str, Any]:
    """
    List active operationals, optionally filtered by unit.

    Args:
        unit_code: Optional unit code filter (e.g., "1º BPM")
        dev_mode: If True, use mock data

    Returns:
        dict with list of active operationals
    """
    if dev_mode or DEV_MODE:
        import random

        operationals = []

        for i in range(min(random.randint(10, 30), 50)):
            random.seed(i * 1000 + (hash(unit_code or "") % 1000))
            unit_idx = random.randint(0, len(MOCK_UNITS) - 1)
            rank_idx = random.randint(0, len(MOCK_RANKS) - 3)

            if unit_code and MOCK_UNITS[unit_idx]["code"] != unit_code:
                continue

            operationals.append(
                {
                    "badge_number": f"{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "name": f"PM {random.choice(['SILVA', 'SANTOS', 'OLIVEIRA', 'PEREIRA', 'CARVALHO', 'RODRIGUES'])}",
                    "rank": MOCK_RANKS[rank_idx],
                    "unit": MOCK_UNITS[unit_idx]["code"],
                    "status": "active",
                }
            )

        return {
            "provider": "bm_hr_mock",
            "connected": True,
            "status": "success",
            "message": f"{len(operationals)} operacionais ativos",
            "verified_at": datetime.utcnow().isoformat() + "Z",
            "unit_filter": unit_code,
            "operationals": operationals,
            "total": len(operationals),
        }

    return {
        "provider": "bm_hr",
        "connected": False,
        "status": "not_configured",
        "message": "BM HR integration not configured",
        "verified_at": datetime.utcnow().isoformat() + "Z",
    }
