"""
Script para simular inserção de dados do mobile e algoritmos
Gera dados de vehicle observations e resultados de algoritmos para testar o banco de dados
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
    "Honda CG 160", "Yamaha Fazer", "Honda Biz", "Yamaha MT-07"
]

# Coordenadas aproximadas de São Paulo
SAO_PAULO_BOUNDS = {
    "lat_min": -23.6,
    "lat_max": -23.5,
    "lon_min": -46.8,
    "lon_max": -46.6
}

# IDs de usuários e agências (do seed_data.py)
DEFAULT_AGENCY_ID = "11111111-1111-1111-1111-111111111111"
DEFAULT_USER_ID = "admin@faro.pol"  # Será substituído pelo ID real


def generate_random_plate():
    """Gera uma placa aleatória no formato brasileiro"""
    return random.choice(PLATES)


def generate_random_point():
    """Gera um ponto aleatório em São Paulo"""
    lat = random.uniform(SAO_PAULO_BOUNDS["lat_min"], SAO_PAULO_BOUNDS["lat_max"])
    lon = random.uniform(SAO_PAULO_BOUNDS["lon_min"], SAO_PAULO_BOUNDS["lon_max"])
    return Point(lon, lat)


def generate_random_datetime(days_back=30):
    """Gera uma data/hora aleatória nos últimos N dias"""
    now = datetime.utcnow()
    random_days = random.randint(0, days_back)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    return now - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)


def generate_today_datetime():
    """Gera uma data/hora aleatória de hoje"""
    now = datetime.utcnow()
    random_hours = random.randint(0, 23)
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


async def get_existing_devices(db: AsyncSession, count: int = 10):
    """Obtém dispositivos existentes do banco"""
    print(f"\n📱 Buscando {count} dispositivos existentes...")
    
    result = await db.execute(
        text("SELECT id FROM device WHERE is_active = true LIMIT :limit"),
        {"limit": count}
    )
    devices = result.fetchall()
    
    if not devices:
        print("❌ Nenhum dispositivo encontrado no banco.")
        return []
    
    device_ids = [str(device[0]) for device in devices]
    print(f"✅ {len(device_ids)} dispositivos encontrados!")
    return device_ids


async def create_vehicle_observations(db: AsyncSession, device_ids: list, count: int = 100):
    """Cria observações de veículos simuladas"""
    print(f"\n📸 Criando {count} vehicle observations...")
    
    if not device_ids:
        print("❌ Nenhum dispositivo disponível. Crie dispositivos primeiro.")
        return 0
    
    # Obter o mesmo usuário usado em create_devices
    result = await db.execute(
        text("SELECT id FROM \"user\" LIMIT 1")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print("❌ Nenhum usuário encontrado. Não é possível criar observações.")
        return 0
    
    user_id = str(user)
    print(f"✓ Usando usuário ID: {user_id}")
    
    created_count = 0
    
    print("📸 Criando vehicle observations...")
    for i in range(400):
        plate = random.choice(PLATES)
        # 20% das observações são de hoje
        if i < 80:
            observed_at = generate_today_datetime()
        else:
            observed_at = generate_random_datetime(days_back=30)
        
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
        
        created_count += 1
        
        if (i + 1) % 20 == 0:
            print(f"  ✓ {i + 1}/{count} observações criadas")
    
    except Exception as e:
        print(f"  ❌ Erro ao criar observação {i + 1}: {e}")
        await db.rollback()

await db.commit()
print(f"✅ {created_count} vehicle observations criadas com sucesso!")
return created_count


async def create_suspicion_reports(db: AsyncSession, count: int = 50):
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
    print(f"✅ {created_count} suspicion reports criados com sucesso!")
    return created_count


async def create_intelligence_reviews(db: AsyncSession, count: int = 30):
    """Cria revisões de inteligência simuladas"""
    print(f"\n🔍 Criando {count} intelligence reviews...")
    
    # Obter observações para associar
    result = await db.execute(
        text("SELECT id FROM vehicleobservation ORDER BY RANDOM() LIMIT :limit"),
        {"limit": count}
    )
    observations = result.fetchall()
    
    if not observations:
        print("❌ Nenhuma observação encontrada. Crie vehicle observations primeiro.")
        return 0
    
    # Obter usuário para reviewer_id
    result = await db.execute(
        text("SELECT id FROM \"user\" LIMIT 1")
    )
    reviewer = result.scalar_one_or_none()
    
    if not reviewer:
        print("❌ Nenhum usuário encontrado. Não é possível criar intelligence reviews.")
        return 0
    
    from app.db.base import ReviewStatus
    
    created_count = 0
    
    for (obs_id,) in observations:
        try:
            review = IntelligenceReview(
                observation_id=obs_id,
                reviewer_id=reviewer,
                status=random.choice(list(ReviewStatus)),
                justification=random.choice([
                    "Confirmação baseada em watchlist",
                    "Falso positivo - veículo não relacionado",
                    "Padrão de comportamento suspeito",
                    "Rota compatível com perfil",
                    "Aguardando mais informações"
                ])
            )
            
            db.add(review)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar intelligence review: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} intelligence reviews criados com sucesso!")
    return created_count


async def create_watchlist_entries(db: AsyncSession, count: int = 20):
    """Cria entradas de watchlist simuladas"""
    print(f"\n📋 Criando {count} watchlist entries...")
    
    # Obter usuário para created_by
    result = await db.execute(
        text("SELECT id FROM \"user\" LIMIT 1")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print("❌ Nenhum usuário encontrado. Não é possível criar watchlist entries.")
        return 0
    
    from app.db.base import WatchlistCategory
    
    created_count = 0
    
    for i in range(count):
        try:
            entry = WatchlistEntry(
                created_by=user,
                agency_id=DEFAULT_AGENCY_ID,
                plate_number=generate_random_plate(),
                interest_reason=random.choice([
                    "Veículo roubado",
                    "Suspeito de crime",
                    "Procurado pela polícia",
                    "Envolvido em tráfico",
                    "Ordem de prisão"
                ]),
                information_source=random.choice(["polícia", "detran", "inteligência", "interpol"]),
                category=random.choice(list(WatchlistCategory)),
                sensitivity_level=random.choice(["public", "reserved", "confidential", "secret"]),
            )
            
            db.add(entry)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar watchlist entry: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} watchlist entries criados com sucesso!")
    return created_count


async def create_alerts(db: AsyncSession, count: int = 15):
    """Cria alertas simulados"""
    print(f"\n⚠️  Criando {count} alerts...")
    
    # Obter suspicion reports para associar
    result = await db.execute(
        text("SELECT id FROM suspicionreport ORDER BY RANDOM() LIMIT :limit"),
        {"limit": count}
    )
    suspicions = result.fetchall()
    
    if not suspicions:
        print("❌ Nenhum suspicion report encontrado. Crie suspicion reports primeiro.")
        return 0
    
    created_count = 0
    
    for (suspicion_id,) in suspicions:
        try:
            alert = Alert(
                suspicion_report_id=suspicion_id,
                alert_type=random.choice(list(AlertType)),
                severity=random.choice(list(AlertSeverity)),
                title=random.choice([
                    "Watchlist Match",
                    "Suspicious Route",
                    "Hotspot Detection",
                    "Behavioral Anomaly"
                ]),
                description=random.choice([
                    "Placa encontrada na watchlist",
                    "Veículo em rota suspeita",
                    "Localização em hotspot de criminalidade",
                    "Comportamento anormal detectado"
                ])
            )
            
            db.add(alert)
            created_count += 1
            
        except Exception as e:
            print(f"  ❌ Erro ao criar alert: {e}")
            await db.rollback()
    
    await db.commit()
    print(f"✅ {created_count} alerts criados com sucesso!")
    return created_count


async def print_database_stats(db: AsyncSession):
    """Imprime estatísticas do banco de dados"""
    print("\n📊 Estatísticas do banco de dados:")
    
    tables = [
        ("vehicleobservation", "Vehicle Observations"),
        ("plateread", "Plate Reads"),
        ("suspicionreport", "Suspicion Reports"),
        ("intelligencereview", "Intelligence Reviews"),
        ("watchlistentry", "Watchlist Entries"),
        ("alert", "Alerts")
    ]
    
    for table_name, display_name in tables:
        result = await db.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        )
        count = result.scalar()
        print(f"  • {display_name}: {count}")


async def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 Simulação de Dados do Mobile e Algoritmos FARO")
    print("=" * 60)
    
    async for db in get_db():
        try:
            # Criar dados na ordem correta (respeitando foreign keys)
            device_ids = await get_existing_devices(db, count=10)
            
            watchlist_count = await create_watchlist_entries(db, count=20)

            obs_count = await create_vehicle_observations(db, device_ids, count=100)

            suspicion_count = await create_suspicion_reports(db, count=50)

            review_count = await create_intelligence_reviews(db, count=30)

            alert_count = await create_alerts(db, count=15)

            # Imprimir estatísticas finais
            await print_database_stats(db)

            print("\n" + "=" * 60)
            print("✅ Simulação concluída com sucesso!")
            print("=" * 60)
            print(f"\nResumo:")
            print(f"  • Devices: {len(device_ids)}")
            print(f"  • Watchlist Entries: {watchlist_count}")
            print(f"  • Vehicle Observations: {obs_count}")
            print(f"  • Suspicion Reports: {suspicion_count}")
            print(f"  • Intelligence Reviews: {review_count}")
            print(f"  • Alerts: {alert_count}")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Erro durante a simulação: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
