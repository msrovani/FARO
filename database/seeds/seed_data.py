"""
Seed Data Script for FARO Database
Populates the database with test data for development and testing.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, Polygon
import random

# Database connection
DATABASE_URL = "postgresql+psycopg2://faro:faro@localhost:5432/faro_db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Helper function to generate UUIDs
def generate_uuid():
    return str(uuid.uuid4())

# Helper function to generate random coordinates around São Paulo
def generate_sao_paulo_point():
    # São Paulo approximate bounds
    lat = random.uniform(-23.6, -23.5)
    lon = random.uniform(-46.8, -46.6)
    return Point(lon, lat)

# Create Agency (already created by migration, but we'll add more)
def create_agencies():
    agencies = [
        {
            "id": "11111111-1111-1111-1111-111111111111",  # Bootstrap agency
            "name": "Agencia Padrao FARO",
            "code": "FARO-DEFAULT",
            "is_active": True,
            "type": "LOCAL",
            "parent_agency_id": None
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",  # DINT - Agência Principal
            "name": "DINT - Departamento de Inteligência",
            "code": "DINT",
            "is_active": True,
            "type": "REGIONAL",  # DINT é agência principal/regional
            "parent_agency_id": None
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",  # ARI - Sub-agência do DINT
            "name": "ARI - Análise de Risco",
            "code": "ARI",
            "is_active": True,
            "type": "LOCAL",
            "parent_agency_id": "22222222-2222-2222-2222-222222222222"  # DINT
        },
        {
            "id": "44444444-4444-4444-4444-444444444444",  # ALI - Sub-agência do DINT
            "name": "ALI - Análise de Inteligência",
            "code": "ALI",
            "is_active": True,
            "type": "LOCAL",
            "parent_agency_id": "22222222-2222-2222-2222-222222222222"  # DINT
        }
    ]
    
    for agency in agencies:
        session.execute(text("""
            INSERT INTO agency (id, name, code, is_active, type, parent_agency_id)
            VALUES (:id, :name, :code, :is_active, :type, :parent_agency_id)
            ON CONFLICT (code) DO NOTHING
        """), agency)
    
    print(f"Created {len(agencies)} agencies")

# Create Units - skip for now due to schema differences
def create_units():
    print("Skipping units creation - schema differs from expected")
    return []

# Create Users
def create_users():
    # Get agency IDs
    default_agency_id = "11111111-1111-1111-1111-111111111111"
    dint_agency_id = "22222222-2222-2222-2222-222222222222"
    ari_agency_id = "33333333-3333-3333-3333-333333333333"
    ali_agency_id = "44444444-4444-4444-4444-444444444444"

    users = [
        # Default FARO users
        {
            "id": generate_uuid(),
            "email": "admin@faro.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Administrador FARO",
            "badge_number": "00000",
            "role": "ADMIN",
            "agency_id": default_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": False
        },
        {
            "id": generate_uuid(),
            "email": "supervisor@faro.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Supervisor Oliveira",
            "badge_number": "00001",
            "role": "SUPERVISOR",
            "agency_id": default_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": True
        },
        {
            "id": generate_uuid(),
            "email": "agente1@faro.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Agente Silva",
            "badge_number": "12345",
            "role": "FIELD_AGENT",
            "agency_id": default_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": True
        },
        # DINT users
        {
            "id": generate_uuid(),
            "email": "admin@dint.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Administrador DINT",
            "badge_number": "D001",
            "role": "ADMIN",
            "agency_id": dint_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": True
        },
        # ARI users
        {
            "id": generate_uuid(),
            "email": "admin@ari.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Administrador ARI",
            "badge_number": "A001",
            "role": "ADMIN",
            "agency_id": ari_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": True
        },
        # ALI users
        {
            "id": generate_uuid(),
            "email": "admin@ali.pol",
            "hashed_password": "$2b$12$ylXrwszv.tCamQsAXli8A.y7nfKhK.1sjYMOqg3E04PgInlz8Fsyu",  # "password"
            "full_name": "Administrador ALI",
            "badge_number": "L001",
            "role": "ADMIN",
            "agency_id": ali_agency_id,
            "is_active": True,
            "is_verified": True,
            "is_on_duty": True
        }
    ]
    
    for user in users:
        session.execute(text("""
            INSERT INTO "user" (id, email, hashed_password, full_name, badge_number, role, agency_id, is_active, is_verified, is_on_duty)
            VALUES (:id, :email, :hashed_password, :full_name, :badge_number, :role, :agency_id, :is_active, :is_verified, :is_on_duty)
            ON CONFLICT (email) DO UPDATE SET
                hashed_password = EXCLUDED.hashed_password,
                full_name = EXCLUDED.full_name,
                badge_number = EXCLUDED.badge_number,
                role = EXCLUDED.role,
                agency_id = EXCLUDED.agency_id,
                is_active = EXCLUDED.is_active,
                is_verified = EXCLUDED.is_verified,
                is_on_duty = EXCLUDED.is_on_duty
        """), user)
    
    print(f"Created {len(users)} users")
    return users

# Create Devices - skip for now
def create_devices(users):
    print("Skipping devices creation")
    return []

# Create Vehicle Observations - skip due to complex schema differences
def create_vehicle_observations(users):
    print("Skipping vehicle observations creation - schema differs significantly from ORM model")
    return []

# Create Watchlist Entries - skip for now
def create_watchlist_entries(users):
    print("Skipping watchlist entries creation")
    return []

# Create Route Patterns - skip for now
def create_route_patterns(users):
    print("Skipping route patterns creation")
    return []

# Main execution
def main():
    try:
        print("Starting seed data creation...")
        
        # Create data in order respecting foreign keys
        create_agencies()
        units = create_units()
        users = create_users()
        create_devices(users)
        create_vehicle_observations(users)
        create_watchlist_entries(users)
        create_route_patterns(users)
        
        session.commit()
        print("\n✅ Seed data created successfully!")
        print("\nLogin credentials:")
        print("\n  --- FARO Default Agency ---")
        print("  Email: admin@faro.pol")
        print("  Password: password")
        print("\n  --- DINT Agency ---")
        print("  Email: admin@dint.pol")
        print("  Password: password")
        print("\n  --- ARI Agency ---")
        print("  Email: admin@ari.pol")
        print("  Password: password")
        print("\n  --- ALI Agency ---")
        print("  Email: admin@ali.pol")
        print("  Password: password")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error creating seed data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
