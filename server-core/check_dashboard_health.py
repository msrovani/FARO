"""Verifica o endpoint /api/v1/health do analytics dashboard"""
import asyncio
import httpx
import json


async def check_health():
    """Verifica o endpoint /api/v1/health"""
    print("📊 Verificando endpoint /api/v1/health do analytics dashboard...\n")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get("http://localhost:9002/api/v1/health")
            if resp.status_code == 200:
                data = resp.json()
                print("Status:", data.get("status"))
                print("\nMétricas:")
                metrics = data.get("metrics", {})
                for key, value in metrics.items():
                    print(f"  • {key}: {value}")
                
                print("\nAlerts:")
                alerts = data.get("alerts", [])
                for alert in alerts:
                    print(f"  • {alert.get('name')}: {alert.get('severity')}")
                
                print("\nRecommendations:")
                recommendations = data.get("recommendations", [])
                for rec in recommendations:
                    print(f"  • {rec}")
            else:
                print(f"Erro: Status {resp.status_code}")
        except Exception as e:
            print(f"Erro ao conectar: {e}")


if __name__ == "__main__":
    asyncio.run(check_health())
