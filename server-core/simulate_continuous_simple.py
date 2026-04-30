"""
Script de simulação contínua simples de dados mobile F.A.R.O.
Roda continuamente inserindo dados com tempos aleatórios entre inserções
"""
import asyncio
import random
import uuid
import signal
import sys
from datetime import datetime, timedelta, timezone
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
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
    Device,
    AgentLocationLog,
    User,
    UserRole,
    Agency,
    Unit,
)

# Dados simulados
PLATES = [
    "ABC1234", "DEF5678", "GHI9012", "JKL3456", "MNO7890",
    "PQR2345", "STU6789", "VWX0123", "YZA4567", "BCD8901",
]

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE", "DF"]
VEHICLE_COLORS = ["Branco", "Preto", "Cinza", "Prata", "Vermelho", "Azul", "Verde", "Amarelo"]
VEHICLE_TYPES = ["Carro", "Moto", "Caminhão", "Van", "SUV", "Utilitário"]

DEVICE_IDS = ["android-12345", "android-67890", "ios-54321", "android-98765"]
APP_VERSIONS = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
CONNECTIVITY_TYPES = ["wifi", "4g", "3g", "offline"]

RS_REGIONS = [
    {"name": "Porto Alegre", "lat": -30.0346, "lng": -51.2177, "radius": 0.1},
    {"name": "Caxias do Sul", "lat": -29.1684, "lng": -51.1794, "radius": 0.08},
    {"name": "Gramado", "lat": -29.6553, "lng": -50.8835, "radius": 0.05},
]

running = True

def signal_handler(sig, frame):
    global running
    print("\n\n🛑 Parando simulação gracefulmente...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def generate_random_location(region):
    lat = region["lat"] + random.uniform(-region["radius"], region["radius"])
    lng = region["lng"] + random.uniform(-region["radius"], region["radius"])
    return lat, lng

async def get_or_create_user(db: AsyncSession):
    result = await db.execute(
        select(User).where(User.role == UserRole.FIELD_AGENT).limit(1)
    )
    user_data = result.scalar_one_or_none()
    
    if user_data:
        return user_data.id, user_data.agency_id
    
    # Criar Agency primeiro
    agency_result = await db.execute(select(Agency).limit(1))
    agency_data = agency_result.scalar_one_or_none()
    
    if not agency_data:
        agency = Agency(
            name="Agência Simulada",
            code="SIM001",
            jurisdiction="Rio Grande do Sul",
            type="local",
            is_active=True
        )
        db.add(agency)
        await db.flush()
        agency_id = agency.id
    else:
        agency_id = agency_data.id
    
    # Criar Unit
    unit_result = await db.execute(select(Unit).limit(1))
    unit_data = unit_result.scalar_one_or_none()
    
    if not unit_data:
        unit = Unit(
            name="Unidade Simulada",
            code="UNIT001",
            agency_id=agency_id
        )
        db.add(unit)
        await db.flush()
        unit_id = unit.id
    else:
        unit_id = unit_data.id
    
    new_user = User(
        email=f"agent.{uuid.uuid4().hex[:8]}@faro.pol",
        cpf=f"{random.randint(10000000000, 99999999999)}",
        hashed_password="$2b$12$hashed_password_placeholder",
        full_name=f"Agente Campo {random.randint(1, 999)}",
        role=UserRole.FIELD_AGENT,
        is_active=True,
        agency_id=agency_id,
        unit_id=unit_id,
    )
    db.add(new_user)
    await db.flush()
    await db.commit()
    return new_user.id, agency_id

async def create_single_observation(db: AsyncSession, user_id: str, agency_id: str):
    region = random.choice(RS_REGIONS)
    lat, lng = generate_random_location(region)
    
    # Criar device primeiro
    device_id_str = random.choice(DEVICE_IDS)
    device_result = await db.execute(
        select(Device).where(Device.device_id == device_id_str).limit(1)
    )
    device_data = device_result.scalar_one_or_none()
    
    if not device_data:
        device = Device(
            device_id=device_id_str,
            user_id=user_id,
            agency_id=agency_id,
            device_model="Android Emulator",
            os_version="Android 13",
            app_version=random.choice(APP_VERSIONS),
            is_active=True
        )
        db.add(device)
        await db.flush()
        device_uuid = device.id
    else:
        device_uuid = device_data.id
    
    # Criar observation com device_id correto
    observation = VehicleObservation(
        client_id=str(uuid.uuid4()),
        agent_id=user_id,
        agency_id=agency_id,
        device_id=device_uuid,
        plate_number=random.choice(PLATES),
        plate_state=random.choice(STATES),
        plate_country="BR",
        observed_at_local=datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60)),
        location=from_shape(Point(lng, lat)),
        heading=random.uniform(0, 360) if random.random() > 0.3 else None,
        speed=random.uniform(0, 120) if random.random() > 0.4 else None,
        vehicle_color=random.choice(VEHICLE_COLORS) if random.random() > 0.2 else None,
        vehicle_type=random.choice(VEHICLE_TYPES) if random.random() > 0.3 else None,
        sync_status=SyncStatus.COMPLETED,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(1, 60))
    )
    
    db.add(observation)
    await db.flush()
    
    if random.random() > 0.3:
        plate_read = PlateRead(
            observation_id=observation.id,
            ocr_raw_text=observation.plate_number,
            ocr_confidence=random.uniform(0.7, 0.99),
            ocr_engine="mlkit_v2",
            image_width=random.randint(640, 1920),
            image_height=random.randint(480, 1080),
            processing_time_ms=random.randint(50, 500),
            image_hash=f"hash_{uuid.uuid4().hex[:16]}",
            processed_at=datetime.now(timezone.utc)
        )
        db.add(plate_read)
    
    # Agent location log
    agent_location = AgentLocationLog(
        agent_id=user_id,
        location=from_shape(Point(lng, lat)),
        recorded_at=observation.observed_at_local,
        connectivity_status=random.choice(CONNECTIVITY_TYPES)
    )
    db.add(agent_location)
    
    if random.random() < 0.3:
        suspicion_report = SuspicionReport(
            observation_id=observation.id,
            level=random.choice(list(SuspicionLevel)),
            reason=random.choice(list(SuspicionReason)),
            urgency=random.choice(list(UrgencyLevel)),
            confidence=random.uniform(0.3, 0.95),
            created_at=datetime.now(timezone.utc)
        )
        db.add(suspicion_report)
    
    if random.random() < 0.15:
        review = IntelligenceReview(
            observation_id=observation.id,
            reviewed_by=user_id,
            conclusion=random.choice(["confirmed", "rejected", "inconclusive"]),
            notes=f"Revisão automática - {datetime.now(timezone.utc).strftime('%H:%M:%S')}",
            created_at=datetime.now(timezone.utc)
        )
        db.add(review)
    
    return observation

async def continuous_simulation():
    print("🚀 Iniciando simulação contínua de dados mobile F.A.R.O.")
    print("=" * 60)
    print("⚠️  Pressione Ctrl+C para parar a simulação")
    print("=" * 60)
    
    observation_count = 0
    suspicion_count = 0
    review_count = 0
    
    async for db in get_db():
        try:
            user_id, agency_id = await get_or_create_user(db)
            print(f"✅ Usuário FIELD_AGENT obtido/criado: {user_id}")
            
            while running:
                try:
                    sleep_time = random.uniform(2, 8)
                    await asyncio.sleep(sleep_time)
                    
                    if not running:
                        break
                    
                    observation = await create_single_observation(db, user_id, agency_id)
                    observation_count += 1
                    
                    if random.random() < 0.3:
                        suspicion_count += 1
                    
                    if random.random() < 0.15:
                        review_count += 1
                    
                    await db.commit()
                    
                    if observation_count % 10 == 0:
                        print(f"📊 Status: {observation_count} obs | {suspicion_count} sus | {review_count} rev")
                    
                except Exception as e:
                    print(f"❌ Erro na iteração: {e}")
                    await db.rollback()
                    await asyncio.sleep(1)
            
            print("\n" + "=" * 60)
            print("📊 RESUMO FINAL:")
            print(f"  📱 Vehicle Observations: {observation_count}")
            print(f"  🚨 Suspicion Reports: {suspicion_count}")
            print(f"  📋 Intelligence Reviews: {review_count}")
            print(f"  🔍 Total: {observation_count + suspicion_count + review_count}")
            print("\n✅ Simulação concluída!")
            
        except Exception as e:
            print(f"❌ Erro fatal: {e}")
            await db.rollback()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    try:
        asyncio.run(continuous_simulation())
    except KeyboardInterrupt:
        print("\n\n🛑 Simulação interrompida")
        sys.exit(0)
