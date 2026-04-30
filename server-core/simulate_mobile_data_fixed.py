"""
Script completo para simular inserção de dados do mobile F.A.R.O.
Gera dados realistas com todos os campos que o mobile envia para o servidor
"""
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
    WatchlistEntry,
    Alert,
    AlertSeverity,
    AlertType,
    Device,
    AgentLocationLog,
    User,
    UserRole,
    Agency,
    Unit,
)

# Dados simulados de placas brasileiras
PLATES = [
    "ABC1234", "DEF5678", "GHI9012", "JKL3456", "MNO7890",
    "PQR2345", "STU6789", "VWX0123", "YZA4567", "BCD8901",
    "EFG1234", "HIJ5678", "KLM9012", "NOP3456", "QRS7890",
    "TUV2345", "WXY6789", "ZAB0123", "CDE4567", "FGH8901",
]

# Estados brasileiros
STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE", "CE", "DF"]

# Cores de veículos
VEHICLE_COLORS = ["Branco", "Preto", "Cinza", "Prata", "Vermelho", "Azul", "Verde", "Amarelo"]

# Tipos de veículos
VEHICLE_TYPES = ["Carro", "Moto", "Caminhão", "Van", "SUV", "Utilitário"]

# Modelos de veículos
VEHICLE_MODELS = [
    "Corolla", "Civic", "Gol", "Onix", "HB20", "Fiat Uno", "Renault Logan",
    "Honda Fit", "Toyota Etios", "Chevrolet Spin", "Volkswagen Voyage",
    "Ford Ka", "Fiat Palio", "Chevrolet Onix", "Hyundai HB20", "Nissan Kicks"
]

# Device IDs simulados
DEVICE_IDS = [
    "android-12345", "android-67890", "ios-54321", "android-98765", 
    "ios-24680", "android-13579", "ios-86420", "android-11223",
    "ios-44556", "android-99887", "ios-33445", "android-77665"
]

# App versions
APP_VERSIONS = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]

# Connectivity types
CONNECTIVITY_TYPES = ["wifi", "4g", "3g", "offline"]

# Regiões metropolitanas do RS (coordenadas aproximadas)
RS_REGIONS = [
    {"name": "Porto Alegre", "lat": -30.0346, "lng": -51.2177, "radius": 0.1},
    {"name": "Caxias do Sul", "lat": -29.1684, "lng": -51.1794, "radius": 0.08},
    {"name": "Gramado", "lat": -29.6553, "lng": -50.8835, "radius": 0.05},
    {"name": "Canoas", "lat": -29.9177, "lng": -51.1836, "radius": 0.08},
    {"name": "Novo Hamburgo", "lat": -29.7778, "lng": -51.1448, "radius": 0.07},
    {"name": "Santa Maria", "lat": -29.6843, "lng": -53.0713, "radius": 0.09},
]

def generate_random_location(region):
    """Gera coordenadas aleatórias dentro de uma região"""
    lat = region["lat"] + random.uniform(-region["radius"], region["radius"])
    lng = region["lng"] + random.uniform(-region["radius"], region["radius"])
    return lat, lng

async def create_vehicle_observations(db: AsyncSession, count: int = 50):
    """Cria observações de veículos com dados completos do mobile"""
    print(f"\n📱 Criando {count} observações de veículos com dados mobile completos...")
    
    # Primeiro, verificar se existe um usuário FIELD_AGENT
    result = await db.execute(
        text("SELECT id FROM user WHERE role = 'field_agent' LIMIT 1")
    )
    user_data = result.fetchone()
    
    if not user_data:
        print("⚠️  Nenhum usuário FIELD_AGENT encontrado. Criando um novo...")
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
        user_id = new_user.id
    else:
        user_id = user_data[0]
    
    created_count = 0
    
    for i in range(count):
        try:
            # Escolher região aleatória do RS
            region = random.choice(RS_REGIONS)
            lat, lng = generate_random_location(region)
            
            # Gerar dados aleatórios
            client_id = str(uuid.uuid4())
            plate_number = random.choice(PLATES)
            plate_state = random.choice(STATES)
            observed_at = datetime.utcnow() - timedelta(
                minutes=random.randint(0, 1440),  # até 24 horas atrás
                seconds=random.randint(0, 3600)
            )
            
            # Criar observação no banco
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
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))
            )
            
            db.add(observation)
            await db.flush()
            
            # Criar plate read (OCR)
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
            
            # Criar ou registrar dispositivo
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
            
            # Criar log de localização do agente
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
            
            created_count += 1
            
            if (i + 1) % 20 == 0:
                print(f"  ✓ {i + 1}/{count} observações criadas")
        
        except Exception as e:
            print(f"  ❌ Erro ao criar observação {i + 1}: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} vehicle observations criadas com sucesso!")
    return created_count

async def create_suspicion_reports(db: AsyncSession, count: int = 25):
    """Cria relatórios de suspeição simulados"""
    print(f"\n🚨 Criando {count} suspicion reports...")
    
    # Obter observações que ainda não têm suspicion reports
    result = await db.execute(
        text("""
            SELECT vo.id 
            FROM vehicleobservation vo
            LEFT JOIN suspicionreport sr ON vo.id = sr.observation_id
            WHERE sr.id IS NULL
            ORDER BY RANDOM()
            LIMIT :limit
        """),
        {"limit": count}
    )
    observations = result.fetchall()
    
    if not observations:
        print("⚠️  Nenhuma observação disponível (todas já têm suspicion reports).")
        return 0
    
    created_count = 0
    
    for obs_row in observations:
        try:
            suspicion_report = SuspicionReport(
                observation_id=obs_row[0],
                level=random.choice(list(SuspicionLevel)),
                reason=random.choice(list(SuspicionReason)),
                urgency=random.choice(list(UrgencyLevel)),
                confidence=random.uniform(0.3, 0.95),
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))
            )
            db.add(suspicion_report)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar suspicion report: {e}")
    
    await db.commit()
    print(f"✅ {created_count} suspicion reports criados com sucesso!")
    return created_count

async def create_watchlist_entries(db: AsyncSession, count: int = 15):
    """Cria entradas na watchlist"""
    print(f"\n🎯 Criando {count} watchlist entries...")
    
    result = await db.execute(
        text("SELECT id FROM user WHERE role = 'field_agent' AND is_active = True LIMIT 1")
    )
    user_data = result.fetchone()
    
    if not user_data:
        print("⚠️  Nenhum usuário FIELD_AGENT encontrado.")
        return 0
    
    user_id = user_data[0]
    created_count = 0
    
    for i in range(count):
        try:
            watchlist = WatchlistEntry(
                plate_number=random.choice(PLATES),
                plate_state=random.choice(STATES),
                reason=f"Suspeita de atividade ilícita - #{i+1}",
                risk_level=random.choice(["low", "medium", "high"]),
                created_by=user_id,
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=random.randint(30, 365))
            )
            db.add(watchlist)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar watchlist entry: {e}")
    
    await db.commit()
    print(f"✅ {created_count} watchlist entries criadas com sucesso!")
    return created_count

async def main():
    """Função principal para executar todas as simulações"""
    print("🚀 Iniciando simulação completa de dados mobile F.A.R.O.")
    print("=" * 60)
    
    async for db in get_db():
        try:
            # Criar observações de veículos
            obs_count = await create_vehicle_observations(db, count=50)
            
            # Criar suspicion reports
            suspicion_count = await create_suspicion_reports(db, count=25)
            
            # Criar watchlist entries
            watchlist_count = await create_watchlist_entries(db, count=15)
            
            print("\n" + "=" * 60)
            print("📊 RESUMO DA SIMULAÇÃO:")
            print(f"  📱 Vehicle Observations: {obs_count}")
            print(f"  🚨 Suspicion Reports: {suspicion_count}")
            print(f"  🎯 Watchlist Entries: {watchlist_count}")
            print(f"  🔍 Total de registros: {obs_count + suspicion_count + watchlist_count}")
            print("\n✅ Simulação concluída com sucesso!")
            print("💡 Os dados estão prontos para testar os algoritmos e a interface web.")
            
        except Exception as e:
            print(f"❌ Erro durante a simulação: {e}")
            await db.rollback()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(main())
