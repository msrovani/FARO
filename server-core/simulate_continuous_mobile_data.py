"""
Script de simulação contínua de dados mobile F.A.R.O.
Roda continuamente inserindo dados com tempos aleatórios entre inserções
Gera: observações, suspicion reports, análises de inteligência, algoritmos espaciais
"""
import asyncio
import random
import uuid
import signal
import sys
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
    WatchlistEntry,
    Alert,
    AlertSeverity,
    AlertType,
    Device,
    AgentLocationLog,
    User,
    UserRole,
    ImpossibleTravelEvent,
    RouteAnomalyEvent,
    ConvoyEvent,
    RoamingEvent,
    SensitiveAssetRecurrenceEvent,
    SuspicionScore,
    SuspicionScoreFactor,
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmType,
    AlgorithmDecision,
)

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
    "Ford Ka", "Fiat Palio", "Chevrolet Onix", "Hyundai HB20", "Nissan Kicks"
]

DEVICE_IDS = [
    "android-12345", "android-67890", "ios-54321", "android-98765", 
    "ios-24680", "android-13579", "ios-86420", "android-11223",
    "ios-44556", "android-99887", "ios-33445", "android-77665"
]

APP_VERSIONS = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]
CONNECTIVITY_TYPES = ["wifi", "4g", "3g", "offline"]

RS_REGIONS = [
    {"name": "Porto Alegre", "lat": -30.0346, "lng": -51.2177, "radius": 0.1},
    {"name": "Caxias do Sul", "lat": -29.1684, "lng": -51.1794, "radius": 0.08},
    {"name": "Gramado", "lat": -29.6553, "lng": -50.8835, "radius": 0.05},
    {"name": "Canoas", "lat": -29.9177, "lng": -51.1836, "radius": 0.08},
    {"name": "Novo Hamburgo", "lat": -29.7778, "lng": -51.1448, "radius": 0.07},
    {"name": "Santa Maria", "lat": -29.6843, "lng": -53.0713, "radius": 0.09},
]

# Flag para parar a simulação
running = True

def signal_handler(sig, frame):
    """Handler para parar a simulação gracefulmente"""
    global running
    print("\n\n🛑 Parando simulação gracefulmente...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def generate_random_location(region):
    """Gera coordenadas aleatórias dentro de uma região"""
    lat = region["lat"] + random.uniform(-region["radius"], region["radius"])
    lng = region["lng"] + random.uniform(-region["radius"], region["radius"])
    return lat, lng

async def get_or_create_user(db: AsyncSession):
    """Obtém ou cria um usuário agente de campo"""
    result = await db.execute(
        text("SELECT id FROM user WHERE role = 'field_agent' LIMIT 1")
    )
    user_data = result.fetchone()
    
    if user_data:
        return user_data[0]
    
    new_user = User(
        email=f"agent.{uuid.uuid4().hex[:8]}@faro.pol",
        cpf=f"{random.randint(10000000000, 99999999999)}",
        hashed_password="$2b$12$hashed_password_placeholder",
        full_name=f"Agente Campo {random.randint(1, 999)}",
        role=UserRole.FIELD_AGENT,
        is_active=True,
        agency_id=str(uuid.uuid4()),
        unit_id=str(uuid.uuid4()),
    )
    db.add(new_user)
    await db.flush()
    return new_user.id

async def create_single_observation(db: AsyncSession, user_id: str):
    """Cria uma única observação de veículo"""
    region = random.choice(RS_REGIONS)
    lat, lng = generate_random_location(region)
    
    client_id = str(uuid.uuid4())
    plate_number = random.choice(PLATES)
    plate_state = random.choice(STATES)
    observed_at = datetime.utcnow() - timedelta(
        minutes=random.randint(0, 60),
        seconds=random.randint(0, 3600)
    )
    
    observation = VehicleObservation(
        client_id=client_id,
        agent_id=user_id,
        agency_id=str(uuid.uuid4()),
        plate_number=plate_number,
        plate_state=plate_state,
        plate_country="BR",
        observed_at_local=observed_at,
        location=from_shape(Point(lng, lat)),
        heading=random.uniform(0, 360) if random.random() > 0.3 else None,
        speed=random.uniform(0, 120) if random.random() > 0.4 else None,
        vehicle_color=random.choice(VEHICLE_COLORS) if random.random() > 0.2 else None,
        vehicle_type=random.choice(VEHICLE_TYPES) if random.random() > 0.3 else None,
        vehicle_model=random.choice(VEHICLE_MODELS) if random.random() > 0.5 else None,
        vehicle_year=random.randint(2000, 2024) if random.random() > 0.7 else None,
        sync_status=SyncStatus.SYNCED,
        created_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 60))
    )
    
    db.add(observation)
    await db.flush()
    
    # Plate read (OCR)
    if random.random() > 0.3:
        plate_read = PlateRead(
            observation_id=observation.id,
            ocr_raw_text=plate_number,
            ocr_confidence=random.uniform(0.7, 0.99),
            ocr_engine="mlkit_v2",
            image_width=random.randint(640, 1920),
            image_height=random.randint(480, 1080),
            processing_time_ms=random.randint(50, 500),
            image_hash=f"hash_{uuid.uuid4().hex[:16]}",
            processed_at=datetime.utcnow()
        )
        db.add(plate_read)
    
    # Device
    device_id = random.choice(DEVICE_IDS)
    device_result = await db.execute(
        text("SELECT id FROM devices WHERE device_identifier = :device_id"),
        {"device_id": device_id}
    )
    device_data = device_result.fetchone()
    
    if not device_data:
        device = Device(
            device_identifier=device_id,
            user_id=user_id,
            app_version=random.choice(APP_VERSIONS),
            last_seen_at=datetime.utcnow(),
            is_active=True
        )
        db.add(device)
    
    # Agent location log
    agent_location = AgentLocationLog(
        user_id=user_id,
        location=from_shape(Point(lng, lat)),
        accuracy=random.uniform(5.0, 50.0),
        timestamp=observed_at,
        device_id=device_id,
        connectivity_type=random.choice(CONNECTIVITY_TYPES),
        app_version=random.choice(APP_VERSIONS)
    )
    db.add(agent_location)
    
    return observation

async def create_suspicion_report(db: AsyncSession, observation_id: str):
    """Cria um suspicion report para uma observação"""
    suspicion_report = SuspicionReport(
        observation_id=observation_id,
        level=random.choice(list(SuspicionLevel)),
        reason=random.choice(list(SuspicionReason)),
        urgency=random.choice(list(UrgencyLevel)),
        confidence=random.uniform(0.3, 0.95),
        created_at=datetime.utcnow()
    )
    db.add(suspicion_report)
    await db.flush()
    return suspicion_report

async def create_suspicion_score(db: AsyncSession, observation_id: str):
    """Cria um suspicion score para uma observação"""
    score = SuspicionScore(
        observation_id=observation_id,
        final_score=random.uniform(0.1, 0.95),
        confidence=random.uniform(0.3, 0.95),
        created_at=datetime.utcnow()
    )
    db.add(score)
    await db.flush()
    
    # Adicionar fatores de score
    for _ in range(random.randint(1, 3)):
        factor = SuspicionScoreFactor(
            suspicion_score_id=score.id,
            factor_name=random.choice(["watchlist", "location", "time", "behavior"]),
            factor_value=random.uniform(0.1, 0.9),
            weight=random.uniform(0.1, 0.5)
        )
        db.add(factor)
    
    return score

async def create_algorithm_event(db: AsyncSession, observation_id: str, event_type: str):
    """Cria um evento de algoritmo espacial"""
    event = None
    
    if event_type == "impossible_travel":
        event = ImpossibleTravelEvent(
            observation_id=observation_id,
            previous_observation_id=str(uuid.uuid4()),
            distance_km=random.uniform(50, 500),
            time_minutes=random.uniform(10, 120),
            max_plausible_speed=random.uniform(80, 120),
            decision=random.choice(list(AlgorithmDecision)),
            confidence=random.uniform(0.7, 0.95),
            created_at=datetime.utcnow()
        )
    elif event_type == "route_anomaly":
        event = RouteAnomalyEvent(
            observation_id=observation_id,
            region_id=str(uuid.uuid4()),
            anomaly_score=random.uniform(0.5, 0.95),
            recent_observations_count=random.randint(5, 20),
            decision=random.choice(list(AlgorithmDecision)),
            confidence=random.uniform(0.6, 0.9),
            created_at=datetime.utcnow()
        )
    elif event_type == "convoy":
        event = ConvoyEvent(
            observation_id=observation_id,
            convoy_id=str(uuid.uuid4()),
            vehicle_count=random.randint(2, 5),
            duration_minutes=random.uniform(5, 30),
            decision=random.choice(list(AlgorithmDecision)),
            confidence=random.uniform(0.6, 0.9),
            created_at=datetime.utcnow()
        )
    elif event_type == "roaming":
        event = RoamingEvent(
            observation_id=observation_id,
            recent_observations_count=random.randint(10, 30),
            area_km2=random.uniform(5, 50),
            decision=random.choice(list(AlgorithmDecision)),
            confidence=random.uniform(0.5, 0.85),
            created_at=datetime.utcnow()
        )
    elif event_type == "sensitive_zone":
        event = SensitiveAssetRecurrenceEvent(
            observation_id=observation_id,
            zone_id=str(uuid.uuid4()),
            recurrence_count=random.randint(2, 10),
            time_window_hours=random.randint(24, 168),
            decision=random.choice(list(AlgorithmDecision)),
            confidence=random.uniform(0.6, 0.9),
            created_at=datetime.utcnow()
        )
    
    if event:
        db.add(event)
        await db.flush()
        
        # Criar algorithm run
        algorithm_run = AlgorithmRun(
            algorithm_type=random.choice(list(AlgorithmType)),
            observation_id=observation_id,
            status=AlgorithmRunStatus.COMPLETED,
            decision=event.decision,
            confidence=event.confidence,
            execution_time_ms=random.randint(50, 500),
            created_at=datetime.utcnow()
        )
        db.add(algorithm_run)
    
    return event

async def create_intelligence_review(db: AsyncSession, observation_id: str, user_id: str):
    """Cria uma revisão de inteligência"""
    review = IntelligenceReview(
        observation_id=observation_id,
        reviewed_by=user_id,
        conclusion=random.choice(["confirmed", "rejected", "inconclusive"]),
        notes=f"Revisão automática gerada em {datetime.utcnow().strftime('%H:%M:%S')}",
        created_at=datetime.utcnow()
    )
    db.add(review)
    await db.flush()
    return review

async def continuous_simulation():
    """Simulação contínua de dados mobile"""
    print("🚀 Iniciando simulação contínua de dados mobile F.A.R.O.")
    print("=" * 60)
    print("⚠️  Pressione Ctrl+C para parar a simulação")
    print("=" * 60)
    
    observation_count = 0
    suspicion_count = 0
    algorithm_count = 0
    review_count = 0
    
    async for db in get_db():
        try:
            # Obter ou criar usuário
            user_id = await get_or_create_user(db)
            print(f"✅ Usuário FIELD_AGENT obtido/criado: {user_id}")
            
            while running:
                try:
                    # Tempo aleatório entre inserções (2-10 segundos)
                    sleep_time = random.uniform(2, 10)
                    await asyncio.sleep(sleep_time)
                    
                    if not running:
                        break
                    
                    # Criar observação
                    observation = await create_single_observation(db, user_id)
                    observation_count += 1
                    
                    # Criar suspicion report (30% de chance)
                    if random.random() < 0.3:
                        await create_suspicion_report(db, observation.id)
                        suspicion_count += 1
                    
                    # Criar suspicion score (40% de chance)
                    if random.random() < 0.4:
                        await create_suspicion_score(db, observation.id)
                    
                    # Criar evento de algoritmo espacial (25% de chance)
                    if random.random() < 0.25:
                        event_type = random.choice([
                            "impossible_travel", "route_anomaly", "convoy", 
                            "roaming", "sensitive_zone"
                        ])
                        await create_algorithm_event(db, observation.id, event_type)
                        algorithm_count += 1
                    
                    # Criar revisão de inteligência (15% de chance)
                    if random.random() < 0.15:
                        await create_intelligence_review(db, observation.id, user_id)
                        review_count += 1
                    
                    # Commit das mudanças
                    await db.commit()
                    
                    # Status a cada 10 observações
                    if observation_count % 10 == 0:
                        print(f"📊 Status: {observation_count} obs | {suspicion_count} sus | {algorithm_count} alg | {review_count} rev")
                    
                except Exception as e:
                    print(f"❌ Erro na iteração: {e}")
                    await db.rollback()
                    await asyncio.sleep(1)
            
            print("\n" + "=" * 60)
            print("📊 RESUMO FINAL DA SIMULAÇÃO:")
            print(f"  📱 Vehicle Observations: {observation_count}")
            print(f"  🚨 Suspicion Reports: {suspicion_count}")
            print(f"  🔧 Algorithm Events: {algorithm_count}")
            print(f"  📋 Intelligence Reviews: {review_count}")
            print(f"  🔍 Total de registros: {observation_count + suspicion_count + algorithm_count + review_count}")
            print("\n✅ Simulação concluída!")
            
        except Exception as e:
            print(f"❌ Erro fatal na simulação: {e}")
            await db.rollback()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    try:
        asyncio.run(continuous_simulation())
    except KeyboardInterrupt:
        print("\n\n🛑 Simulação interrompida pelo usuário")
        sys.exit(0)
