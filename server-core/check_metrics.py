"""Verifica o endpoint /api/v1/metrics do server-core"""
import asyncio
import httpx


async def check_metrics():
    """Verifica o endpoint /api/v1/metrics"""
    print("📊 Verificando endpoint /api/v1/metrics do server-core...\n")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("http://localhost:8000/api/v1/metrics")
            if resp.status_code == 200:
                data = resp.json()
                print("Métricas retornadas:")
                for key, value in data.items():
                    print(f"  • {key}: {value}")
            else:
                print(f"Erro: Status {resp.status_code}")
        except Exception as e:
            print(f"Erro ao conectar: {e}")


if __name__ == "__main__":
    asyncio.run(check_metrics())
