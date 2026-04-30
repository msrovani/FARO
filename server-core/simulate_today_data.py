"""Script para simular dados de hoje para o dashboard"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.base import (
    VehicleObservation,
    PlateRead,
    SyncStatus,
    SuspicionReport,
    SuspicionLevel,
    SuspicionReason,
    UrgencyLevel,
    IntelligenceReview,
    Alert,
    AlertSeverity,
    AlertType,
)

DEFAULT_AGENCY_ID = "11111111-1111-1111-1111-111111111111"

PLATES = [
    "ABC1234", "DEF5678", "GHI9012", "JKL3456", "MNO7890",
    "PQR2345", "STU6789", "VWX0123", "YZA4567", "BCD8901",
]

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE", "DF"]

VEHICLE_COLORS = ["Branco", "Preto", "Cinza", "Prata", "Vermelho", "Azul", "Verde", "Amarelo"]

VEHICLE_TYPES = ["Carro", "Moto", "Caminhão", "Van", "SUV", "Utilitário"]

VEHICLE_MODELS = [
    "Corolla", "Civic", "Gol", "Onix", "HB20", "Fiat Uno", "Renault Logan",
    "Honda Fit", "Toyota Etios", "Chevrolet Spin", "Volkswagen Voyage",
]


def generate_random_point():
    """Gera um ponto aleatório em São Paulo"""
    lat = -23.5505 + random.uniform(-0.1, 0.1)
    lon = -46.6333 + random.uniform(-0.1, 0.1)
    return Point(lon, lat)


def generate_today_datetime():
    """Gera uma data/hora aleatória de hoje (no passado)"""
    now = datetime.utcnow()
    random_hours = random.randint(0, now.hour - 1 if now.hour > 0 else 0)
    random_minutes = random.randint(0, 59)
    return now.replace(hour=random_hours, minute=random_minutes, second=random.randint(0, 59), microsecond=random.randint(0, 999999))


async def get_user_id(db: AsyncSession, email: str) -> str:
    """Obtém o ID do usuário pelo email"""
    result = await db.execute(
        text("SELECT id FROM \"user\" WHERE email = :email"),
        {"email": email}
    )
    user = result.scalar_one_or_none()
    if user:
        return str(user)
    return None


async def get_any_user_id(db: AsyncSession) -> str:
    """Obtém qualquer ID de usuário"""
    result = await db.execute(text("SELECT id FROM \"user\" LIMIT 1"))
    user = result.scalar_one_or_none()
    if user:
        return str(user)
    return None


async def get_device_ids(db: AsyncSession) -> list:
    """Obtém IDs de dispositivos existentes"""
    result = await db.execute(text("SELECT id FROM device LIMIT 10"))
    devices = result.fetchall()
    return [str(d[0]) for d in devices] if devices else []


async def create_today_observations(db: AsyncSession, count: int = 50):
    """Cria vehicle observations de hoje"""
    print(f"\n📸 Criando {count} vehicle observations de hoje...")
    
    user_id = await get_any_user_id(db)
    if not user_id:
        print("❌ Nenhum usuário encontrado. Não é possível criar observações.")
        return 0
    
    device_ids = await get_device_ids(db)
    if not device_ids:
        print("❌ Nenhum dispositivo encontrado. Não é possível criar observações.")
        return 0
    
    print(f"✓ Usando usuário ID: {user_id}")
    print(f"✓ Usando {len(device_ids)} dispositivos")
    
    created_count = 0
    
    for i in range(count):
        try:
            plate = random.choice(PLATES)
            observed_at = generate_today_datetime()
            
            observation = VehicleObservation(
                client_id=str(uuid.uuid4()),
                agent_id=user_id,
                agency_id=DEFAULT_AGENCY_ID,
                device_id=random.choice(device_ids),
                plate_number=plate,
                plate_state=random.choice(STATES),
                plate_country="BR",
                observed_at_local=observed_at,
                observed_at_server=observed_at + timedelta(seconds=random.randint(0, 60)),
                location=from_shape(generate_random_point(), srid=4326),
                location_accuracy=random.uniform(5.0, 50.0),
                heading=random.uniform(0, 360),
                speed=random.uniform(0, 120),
                vehicle_color=random.choice(VEHICLE_COLORS),
                vehicle_type=random.choice(VEHICLE_TYPES),
                vehicle_model=random.choice(VEHICLE_MODELS),
                vehicle_year=random.randint(2010, 2024),
                connectivity_type=random.choice(["wifi", "4g", "3g"]),
                sync_status=SyncStatus.COMPLETED,
                sync_attempts=1,
                synced_at=datetime.utcnow(),
                metadata_snapshot={
                    "origin": "simulation",
                    "device_id": str(random.choice(device_ids)),
                    "app_version": "1.0.0",
                    "connectivity_type": random.choice(["wifi", "4g", "3g"])
                }
            )
            
            db.add(observation)
            await db.flush()
            
            created_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"  ✓ {i + 1}/{count} observações criadas")
                
            # Adicionar OCR plate read (70% das observações)
            if random.random() < 0.7:
                plate_read = PlateRead(
                    observation_id=observation.id,
                    ocr_raw_text=plate,
                    ocr_confidence=random.uniform(0.7, 0.99),
                    ocr_engine=random.choice(["mlkit_v2", "tesseract", "custom"]),
                    image_width=random.randint(640, 1920),
                    image_height=random.randint(480, 1080),
                    processing_time_ms=random.randint(100, 500),
                    device_id=random.choice(device_ids),
                    plate_number=plate,
                    plate_state=random.choice(STATES),
                    plate_country="BR",
                    observed_at_local=observed_at,
                    observed_at_server=observed_at + timedelta(seconds=random.randint(0, 60)),
                    location=from_shape(generate_random_point(), srid=4326),
                    location_accuracy=random.uniform(5.0, 50.0),
                    heading=random.uniform(0, 360),
                    speed=random.uniform(0, 120),
                    vehicle_color=random.choice(VEHICLE_COLORS),
                    vehicle_type=random.choice(VEHICLE_TYPES),
                    vehicle_model=random.choice(VEHICLE_MODELS),
                    vehicle_year=random.randint(2010, 2024),
                    connectivity_type=random.choice(["wifi", "4g", "3g"]),
                    sync_status=SyncStatus.COMPLETED,
                    sync_attempts=1,
                    synced_at=datetime.utcnow(),
                    metadata_snapshot={
                        "origin": "simulation",
                        "device_id": str(random.choice(device_ids)),
                        "app_version": "1.0.0",
                        "connectivity_type": random.choice(["wifi", "4g", "3g"])
                    }
                )
                
                db.add(plate_read)
                await db.flush()
            
        except Exception as e:
            print(f"  ❌ Erro ao criar observação {i + 1}: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} vehicle observations de hoje criadas com sucesso!")
    return created_count


async def create_today_suspicion_reports(db: AsyncSession, count: int = 20):
    """Cria relatórios de suspeição de hoje"""
    print(f"\n🚨 Criando {count} suspicion reports de hoje...")
    
    # Obter observações de hoje que ainda não têm suspicion reports
    result = await db.execute(
        text("""
            SELECT vo.id 
            FROM vehicleobservation vo
            LEFT JOIN suspicionreport sr ON vo.id = sr.observation_id
            WHERE sr.id IS NULL
            AND vo.observed_at_local >= CURRENT_DATE
            ORDER BY RANDOM()
            LIMIT :limit
        """),
        {"limit": count}
    )
    observations = result.fetchall()
    
    if not observations:
        print("⚠️  Nenhuma observação de hoje disponível.")
        return 0
    
    created_count = 0
    
    for (obs_id,) in observations:
        try:
            suspicion = SuspicionReport(
                observation_id=obs_id,
                reason=random.choice(list(SuspicionReason)),
                level=random.choice(list(SuspicionLevel)),
                urgency=random.choice(list(UrgencyLevel)),
                notes=random.choice([
                    "Comportamento suspeito detectado",
                    "Veículo em área de risco",
                    "Padrão de movimento anormal",
                    "Correspondência com perfil de interesse"
                ])
            )
            
            db.add(suspicion)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar suspicion report: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} suspicion reports de hoje criados com sucesso!")
    return created_count


async def create_today_intelligence_reviews(db: AsyncSession, count: int = 10):
    """Cria revisões de inteligência de hoje"""
    print(f"\n🔍 Criando {count} intelligence reviews de hoje...")
    
    # Obter observações de hoje
    result = await db.execute(
        text("""
            SELECT id FROM vehicleobservation 
            WHERE observed_at_local >= CURRENT_DATE
            ORDER BY RANDOM() 
            LIMIT :limit
        """),
        {"limit": count}
    )
    observations = result.fetchall()
    
    if not observations:
        print("❌ Nenhuma observação de hoje encontrada.")
        return 0
    
    # Obter usuário para reviewer_id
    result = await db.execute(
        text("SELECT id FROM \"user\" LIMIT 1")
    )
    reviewer = result.scalar_one_or_none()
    
    if not reviewer:
        print("❌ Nenhum usuário encontrado.")
        return 0
    
    created_count = 0
    
    for (obs_id,) in observations:
        try:
            status = random.choice(["confirmed", "discarded"])
            review = IntelligenceReview(
                observation_id=obs_id,
                reviewer_id=str(reviewer),
                status=status,
                justification=random.choice([
                    "Confirmado como suspeito",
                    "Falso positivo",
                    "Requer mais investigação",
                    "Correspondência válida"
                ])
            )
            
            db.add(review)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar intelligence review: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} intelligence reviews de hoje criadas com sucesso!")
    return created_count


async def create_today_alerts(db: AsyncSession, count: int = 10):
    """Cria alertas de hoje"""
    print(f"\n🔔 Criando {count} alerts de hoje...")
    
    # Obter observações de hoje para associar
    result = await db.execute(
        text("""
            SELECT id FROM vehicleobservation 
            WHERE observed_at_local >= CURRENT_DATE
            ORDER BY RANDOM() 
            LIMIT :limit
        """),
        {"limit": count}
    )
    observations = result.fetchall()
    
    if not observations:
        print("❌ Nenhuma observação de hoje encontrada.")
        return 0
    
    created_count = 0
    
    for (obs_id,) in observations:
        try:
            alert = Alert(
                alert_type=random.choice(list(AlertType)),
                severity=random.choice(list(AlertSeverity)),
                observation_id=obs_id
            )
            
            db.add(alert)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar alert: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} alerts de hoje criados com sucesso!")
    return created_count


async def main():
    """Função principal"""
    print("🚀 Iniciando simulação de dados de hoje...\n")
    
    async for db in get_db():
        try:
            # Criar dados de hoje
            obs_count = await create_today_observations(db, count=50)
            susp_count = await create_today_suspicion_reports(db, count=20)
            review_count = await create_today_intelligence_reviews(db, count=10)
            alert_count = await create_today_alerts(db, count=10)
            
            print(f"\n📊 Resumo da simulação:")
            print(f"  • Vehicle Observations (hoje): {obs_count}")
            print(f"  • Suspicion Reports (hoje): {susp_count}")
            print(f"  • Intelligence Reviews (hoje): {review_count}")
            print(f"  • Alerts (hoje): {alert_count}")
            
        except Exception as e:
            print(f"❌ Erro na simulação: {e}")
            await db.rollback()
        
        break


if __name__ == "__main__":
    asyncio.run(main())
