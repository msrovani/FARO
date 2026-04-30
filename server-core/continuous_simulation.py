"""Script de simulação contínua de veículos abordados"""
import asyncio
import random
import uuid
import time
from datetime import datetime, timezone as tz
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

# Configurações
SERVER_URL = "http://localhost:8000"
DEFAULT_AGENCY_ID = "11111111-1111-1111-1111-111111111111"
FIELD_AGENT_EMAIL = "admin@faro.test"
FIELD_AGENT_PASSWORD = "password123"
INTELLIGENCE_EMAIL = "admin@faro.test"
INTELLIGENCE_PASSWORD = "password123"

# Dados simulados
PLATES = [
    "ABC1234", "DEF5678", "GHI9012", "JKL3456", "MNO7890",
    "PQR2345", "STU6789", "VWX0123", "YZA4567", "BCD8901",
    "EFG1234", "HIJ5678", "KLM9012", "NOP3456", "QRS7890",
    "TUV2345", "WXY6789", "ZAB0123", "CDE4567", "FGH8901",
]

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE", "DF"]

VEHICLE_COLORS = ["Branco", "Preto", "Cinza", "Prata", "Vermelho", "Azul", "Verde", "Amarelo"]

VEHICLE_TYPES = ["Carro", "Moto", "Caminhão", "Van", "SUV", "Utilitário"]

VEHICLE_MODELS = [
    "Corolla", "Civic", "Gol", "Onix", "HB20", "Fiat Uno", "Renault Logan",
    "Honda Fit", "Toyota Etios", "Chevrolet Spin", "Volkswagen Voyage",
]

CONNECTIVITY_TYPES = ["wifi", "4g", "3g", "offline"]


def generate_random_point():
    """Gera um ponto aleatório em São Paulo"""
    lat = -23.5505 + random.uniform(-0.1, 0.1)
    lon = -46.6333 + random.uniform(-0.1, 0.1)
    return Point(lon, lat)


async def get_auth_token():
    """Obtém token de autenticação para field agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVER_URL}/api/v1/auth/login",
            json={"identifier": FIELD_AGENT_EMAIL, "password": FIELD_AGENT_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Erro ao fazer login: {response.status_code} - {response.text}")
            return None


async def send_observation(token: str, device_id: str):
    """Envia uma observação de veículo"""
    plate = random.choice(PLATES)
    connectivity = random.choice(CONNECTIVITY_TYPES)
    
    observation_data = {
        "client_id": str(uuid.uuid4()),
        "plate_number": plate,
        "plate_state": random.choice(STATES),
        "plate_country": "BR",
        "observed_at_local": datetime.now(tz.utc).isoformat(),
        "location": {
            "latitude": -23.5505 + random.uniform(-0.1, 0.1),
            "longitude": -46.6333 + random.uniform(-0.1, 0.1)
        },
        "heading": random.uniform(0, 360),
        "speed": random.uniform(0, 120),
        "vehicle_color": random.choice(VEHICLE_COLORS),
        "vehicle_type": random.choice(VEHICLE_TYPES),
        "vehicle_model": random.choice(VEHICLE_MODELS),
        "vehicle_year": random.randint(2010, 2024),
        "device_id": device_id,
        "connectivity_type": connectivity,
        "app_version": "1.0.0"
    }
    
    # Adicionar OCR aleatoriamente (70% das vezes)
    if random.random() < 0.7:
        observation_data["plate_read"] = {
            "ocr_raw_text": plate,
            "ocr_confidence": random.uniform(0.7, 0.99),
            "ocr_engine": random.choice(["mlkit_v2", "tesseract", "custom"]),
            "image_width": random.randint(640, 1920),
            "image_height": random.randint(480, 1080),
            "processing_time_ms": random.randint(100, 500)
        }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SERVER_URL}/api/v1/mobile/observations",
                json=observation_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                print(f"✅ Observação enviada: {plate} ({connectivity})")
                return response.json()
            else:
                print(f"❌ Erro ao enviar observação: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"❌ Erro ao enviar observação: {e}")
            return None


async def get_intelligence_token():
    """Obtém token de autenticação para usuário INTELLIGENCE"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVER_URL}/api/v1/auth/login",
            json={"identifier": INTELLIGENCE_EMAIL, "password": INTELLIGENCE_PASSWORD}
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Erro ao fazer login INTELLIGENCE: {response.status_code}")
            return None


async def get_pending_observations(token: str):
    """Obtém observações pendentes de avaliação"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{SERVER_URL}/api/v1/intelligence/queue?page=1&page_size=50",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                # Verificar se data é uma lista ou um dicionário
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("items", [])
                else:
                    return []
            else:
                print(f"❌ Erro ao obter fila: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erro ao obter fila: {e}")
            return []


async def create_intelligence_review(token: str, observation_id: str):
    """Cria uma revisão de inteligência"""
    review_data = {
        "observation_id": observation_id,
        "status": random.choice(["draft", "final"]),
        "justification": random.choice([
            "Confirmado como suspeito após análise detalhada",
            "Falso positivo - padrão normal de movimento",
            "Requer mais investigação - dados insuficientes",
            "Correspondência válida com perfil de interesse"
        ])
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{SERVER_URL}/api/v1/intelligence/reviews",
                json=review_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                print(f"🔍 Revisão criada para observação {observation_id}")
                return response.json()
            else:
                print(f"❌ Erro ao criar revisão: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return None
        except Exception as e:
            print(f"❌ Erro ao criar revisão: {e}")
            return None


async def main():
    """Função principal - simulação contínua"""
    print("🚀 Iniciando simulação contínua de veículos abordados...")
    print(f"📡 Server: {SERVER_URL}")
    print(f"👤 Field Agent: {FIELD_AGENT_EMAIL}")
    print(f"👤 Intelligence: {INTELLIGENCE_EMAIL}")
    print(f"🌐 Web Intelligence: http://localhost:3000")
    print(f"📊 Dashboard: http://localhost:9002/dashboard")
    print("⏹️  Pressione Ctrl+C para parar\n")
    
    # Obter token de autenticação para field agent
    field_token = await get_auth_token()
    if not field_token:
        print("❌ Não foi possível obter token de autenticação FIELD_AGENT")
        return
    
    print(f"✅ Token FIELD_AGENT obtido com sucesso\n")
    
    # Obter token de autenticação para intelligence
    intel_token = await get_intelligence_token()
    if not intel_token:
        print("❌ Não foi possível obter token de autenticação INTELLIGENCE")
        return
    
    print(f"✅ Token INTELLIGENCE obtido com sucesso\n")
    
    # Dispositivo simulado
    device_id = str(uuid.uuid4())
    print(f"📱 Dispositivo ID: {device_id}\n")
    
    observation_count = 0
    review_count = 0
    
    try:
        while True:
            # Enviar observação
            observation = await send_observation(field_token, device_id)
            if observation:
                observation_count += 1
            
            # A cada 2 observações, avaliar suspeições
            if observation_count % 2 == 0:
                print(f"\n🔍 Avaliando observações pendentes...")
                pending = await get_pending_observations(intel_token)
                
                if pending:
                    # Ordenar por gravidade (score_value) e chegada (observed_at)
                    pending_sorted = sorted(
                        pending,
                        key=lambda x: (
                            -(x.get('score_value') or 0),  # Maior score primeiro
                            x.get('observed_at', '')  # Mais antigo primeiro
                        )
                    )
                    
                    # Avaliar até 3 observações
                    for obs in pending_sorted[:3]:
                        obs_id = obs.get('observation_id')
                        if obs_id:
                            review = await create_intelligence_review(intel_token, obs_id)
                            if review:
                                review_count += 1
                else:
                    print("  Nenhuma observação pendente")
            
            # Esperar aleatoriamente entre 1 e 5 segundos
            sleep_time = random.uniform(1, 5)
            print(f"⏱️  Aguardando {sleep_time:.1f}s antes da próxima observação...")
            await asyncio.sleep(sleep_time)
            
            # Mostrar estatísticas a cada 10 observações
            if observation_count % 10 == 0:
                print(f"\n📊 Estatísticas:")
                print(f"  • Observações enviadas: {observation_count}")
                print(f"  • Revisões criadas: {review_count}")
                print()
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Simulação interrompida pelo usuário")
        print(f"📊 Estatísticas finais:")
        print(f"  • Observações enviadas: {observation_count}")
        print(f"  • Revisões criadas: {review_count}")


if __name__ == "__main__":
    asyncio.run(main())
