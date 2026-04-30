"""Verifica se o web-inteligence está refletindo os dados enviados"""
import asyncio
import httpx


async def check_queue():
    """Verifica a fila de inteligência"""
    # Login
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'http://localhost:8000/api/v1/auth/login',
            json={'identifier': 'admin@faro.test', 'password': 'password123'}
        )
        token = resp.json().get('access_token')
        print(f"✅ Token obtido")
        
        # Verificar queue
        resp = await client.get(
            'http://localhost:8000/api/v1/intelligence/queue?page=1&page_size=10',
            headers={'Authorization': f'Bearer {token}'}
        )
        data = resp.json()
        print(f"\n📊 Fila de Inteligência:")
        
        # Verificar se data é uma lista ou um dicionário
        if isinstance(data, list):
            items = data
            print(f"Total: {len(items)}")
        elif isinstance(data, dict):
            items = data.get('items', [])
            print(f"Total: {data.get('total', 0)}")
            print(f"Page: {data.get('page', 0)}")
            print(f"Page size: {data.get('page_size', 0)}")
        else:
            items = []
            print(f"Formato desconhecido: {type(data)}")
        
        print(f"\nItens na fila ({len(items)}):")
        for item in items[:5]:
            print(f"  • ID: {item.get('id', 'N/A')}")
            print(f"    Placa: {item.get('plate_number', 'N/A')}")
            print(f"    Status: {item.get('status', 'N/A')}")
            print(f"    Criado em: {item.get('created_at', 'N/A')}")
            print()


if __name__ == "__main__":
    asyncio.run(check_queue())
