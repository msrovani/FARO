# FARO Installation Guide

This guide documents the complete installation process for FARO on Windows. It includes instructions for both LLM agents and human operators.

## 🤖 Rotina de Verificação assistida por IA/LLM (OBRIGATÓRIO)

Antes de qualquer instalação, executar rotinas de verificação assistidas:

### 1. Verificar Dados Existentes no DB

```powershell
# Verificar tabelas existentes
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "\dt"

# Contar usuários
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "SELECT COUNT(*) FROM user;"

# Listar usuários existentes
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "SELECT email, role, agency_id FROM public.user;"

# Listar agências
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "SELECT id::text, name, type, parent_agency_id::text FROM agency;"

# Contar observações
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "SELECT COUNT(*) FROM vehicleobservation;"

# Contar alertas
$env:PGPASSWORD="faro_secret"; & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U faro -d faro_db -c "SELECT COUNT(*) FROM alert;"
```

### 2. Rotina de Decisão (OBRIGATÓRIO)

| Cenário | Ação |
|---------|------|
| DB vazio (0 usuários) | Criar admin DINT/ACI do zero |
| DB com dados existentes | Perguntar: "Manter dados ou limpar?" |
| DB com admin DINT existente | Manter, apenas verificar acesso |
| DB sem admin DINT | Criar admin DINT vinculado à agência central |

### 3. Fluxo de Decisão para LLM/AI

```
Pergunta Obrigatória ao Usuário:
"O DB já tem dados existentes. Você quer limpar os dados e criar um ambiente fresco, OU manter os dados existentes?"

Opções:
- Manter dados existentes (Recomendado)
- Limpar e recomeçar
```

**Se usuário选择 "Manter":**
- Verificar se admin@dint.pol existe
- Se não existir, criar admin DINT vinculado à agência DINT

**Se usuário选择 "Limpar":**
- TRUNCATE TABLE user, agency, vehicleobservation, alert, suspicionreport, watchlistentry, intelligencecase, feedbackevent CASCADE;
- Criar hierarquia de agências (DINT → ARI → ALI)
- Criar usuário admin DINT

### 4. Criar Admin DINT/ACI (se necessário após verificação)

```python
# Admin DINT deve ser vinculado à agência DINT
admin_dint = User(
    email="admin@dint.pol",
    full_name="Administrador DINT -ACI",
    role="ADMIN",
    agency_id=agency_dint.id,  # ID da agência DINT
    is_active=True,
    is_verified=True
)
```

### 5. Checklist Pré-Instalação

- [ ] Verificar DB existente (perguntar ao usuário)
- [ ] Verificar dados existentes (usuários, agências)
- [ ] Decidir: manter ou limpar
- [ ] Criar admin DINT/ACI (se necessário)
- [ ] Iniciar infraestrutura
- [ ] Verificar/migrar schema
- [ ] Iniciar server-core
- [ ] Iniciar frontend
- [ ] Iniciar analytics dashboard
- [ ] Testar endpoints

## 🤖 LLM Execution Mode

When executed by an LLM, this guide provides:
- ✅ Visual progress indicators for each step
- 🔍 Automatic verification before each step
- 🔄 Automatic workarounds for common issues
- 📊 Final installation report with workarounds applied

The installation will continue even if some components fail, with graceful degradation.

## 📋 Installation Report

After completion, the LLM will generate a report including:
- ✅ Components successfully installed
- 🔧 Workarounds applied for controllable issues
- ⚠️ Critical issues that prevented full installation
- 📝 Alternative options for manual resolution

---

## Prerequisites

### System Requirements
- Windows 10/11
- Minimum 8GB RAM
- 20GB free disk space
- Administrative privileges (for some components)
- Git (for cloning repository)

### Required Software
- Python 3.12 LTS
- PostgreSQL 16
- PostGIS Extension for PostgreSQL 16

### Installation Location
The FARO project can be installed in any directory. Common locations:
- `C:\Users\[username]\FARO`
- `C:\Projects\FARO`
- `D:\Development\FARO`

**For this guide, we'll use:** `$FARO_HOME` (replace with your actual path)

### Clone from GitHub (Recommended)

**For Humans:**
```powershell
# Clone the repository
git clone https://github.com/your-org/FARO.git
# Or use SSH:
git clone git@github.com:your-org/FARO.git
```

**For LLM:**
```powershell
# Clone the repository
git clone https://github.com/your-org/FARO.git $env:USERPROFILE\FARO
# Set environment variable (optional)
$env:FARO_HOME = "$env:USERPROFILE\FARO"
```

## Installation Steps

### 🔍 Standard Verification Pattern

For each software component, the LLM should execute the following verification pattern:

**Step 1: Check if installed**
```powershell
# Check if software is in PATH
<software-command> --version 2>$null
$inPath = ($LASTEXITCODE -eq 0)
```

**Step 2: If installed, gather details**
```powershell
if ($inPath) {
    # Get version
    $version = <software-command> --version

    # Get installation location
    $location = Get-Command <software-command> | Select-Object -ExpandProperty Source

    # Check compatibility
    # Compare $version against required version
}
```

**Step 3: If not installed, install compatible version**
```powershell
if (-not $inPath) {
    # Download and install compatible version
    # Follow installation instructions
}
```

**Step 4: Verify PATH after installation**
```powershell
# Refresh PATH and verify
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
<software-command> --version
```

### Progress Tracking

Each step includes:
- **🔍 Pre-check:** Verify prerequisites, check if installed, gather version/location/compatibility info
- **⚙️ Execution:** Main installation command (only if not installed or incompatible)
- **✅ Verification:** Confirm successful completion and PATH availability
- **🔄 Workaround:** Alternative if step fails (when available)

---

### 1. 🔍 Install Python 3.12 LTS

**Required Version:** Python 3.12.x (LTS)

**🔍 Pre-check:**
```powershell
# Check if Python is in PATH
python --version 2>$null
$inPath = ($LASTEXITCODE -eq 0)

if ($inPath) {
    Write-Host "✅ Python found in PATH"

    # Get version
    $version = python --version
    Write-Host "📍 Version: $version"

    # Get installation location
    $location = Get-Command python | Select-Object -ExpandProperty Source
    Write-Host "📍 Location: $location"

    # Check compatibility (requires 3.12.x)
    if ($version -match "3\.12\.") {
        Write-Host "✅ Python 3.12.x - Compatible version"
    } else {
        Write-Host "⚠️  Python version $version is not 3.12.x - may not be compatible"
    }

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $pythonDir = Split-Path $location -Parent
    if ($pythonDir -in $pathDirs) {
        Write-Host "✅ Python directory is in PATH"
    } else {
        Write-Host "⚠️  Python directory not in PATH - may need to add manually"
    }
} else {
    Write-Host "❌ Python not found in PATH - will install"
}
```

**For Humans:**
1. Download Python 3.12 LTS from https://www.python.org/downloads/
2. Run the installer
3. Check "Add Python to PATH"
4. Install at: `C:\Users\[username]\AppData\Local\Programs\Python\Python312\`

**For LLM:**
```powershell
# Download Python 3.12 LTS installer
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe" -OutFile "python-3.12.0-amd64.exe"
# Install silently
.\python-3.12.0-amd64.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
```

**✅ Verification:**
```powershell
python --version
# Expected: Python 3.12.0
```

**🔄 Workaround:** If installation fails, Python may already be installed. Check alternative paths:
```powershell
python --version
py --version
```

---

### 2. 📦 Install Project Dependencies

**🔍 Pre-check:**
```powershell
cd $env:FARO_HOME\server-core
if (Test-Path "requirements.txt") { Write-Host "✅ requirements.txt found" } else { Write-Host "❌ requirements.txt not found" }
```

**For Humans:**
1. Open PowerShell in `server-core` directory
2. Install dependencies:
```powershell
cd $env:FARO_HOME\server-core
pip install -r requirements.txt
```

**For LLM:**
```powershell
cd $env:FARO_HOME\server-core
pip install -r requirements.txt
```

**✅ Verification:**
```powershell
pip list | Select-String fastapi
# Expected: fastapi listed
```

---

### 3. 🗄️ Install PostgreSQL 16

**Required Version:** PostgreSQL 16.x

**🔍 Pre-check:**
```powershell
# Check if PostgreSQL 16 is installed in standard location
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
$pgInstalled = Test-Path $pgPath

if ($pgInstalled) {
    Write-Host "✅ PostgreSQL 16 found in standard location"

    # Get version
    $version = & $pgPath --version
    Write-Host "📍 Version: $version"

    # Get installation location
    Write-Host "📍 Location: C:\Program Files\PostgreSQL\16"

    # Check compatibility (requires 16.x)
    if ($version -match "16\.") {
        Write-Host "✅ PostgreSQL 16.x - Compatible version"
    } else {
        Write-Host "⚠️  PostgreSQL version $version is not 16.x - may not be compatible"
    }

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $pgBinDir = "C:\Program Files\PostgreSQL\16\bin"
    if ($pgBinDir -in $pathDirs) {
        Write-Host "✅ PostgreSQL bin directory is in PATH"
    } else {
        Write-Host "⚠️  PostgreSQL bin directory not in PATH - may need to add manually"
    }

    # Check if service is running
    $service = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "📍 Service Status: $($service.Status)"
        if ($service.Status -eq "Running") {
            Write-Host "✅ PostgreSQL service is running"
        } else {
            Write-Host "⚠️  PostgreSQL service is not running - will start later"
        }
    } else {
        Write-Host "⚠️  PostgreSQL service not found"
    }
} else {
    # Check for other PostgreSQL versions
    $otherVersions = @("15", "14", "13", "12")
    foreach ($v in $otherVersions) {
        $altPath = "C:\Program Files\PostgreSQL\$v\bin\psql.exe"
        if (Test-Path $altPath) {
            $altVersion = & $altPath --version
            Write-Host "⚠️  Found PostgreSQL $v at $altPath (version: $altVersion) - not compatible, requires 16.x"
        }
    }
    Write-Host "❌ PostgreSQL 16 not found - will install"
}
```

**For Humans:**
1. Download PostgreSQL 16 from https://www.postgresql.org/download/windows/
2. Run the installer
3. Set password for postgres user (remember it)
4. Install at: `C:\Program Files\PostgreSQL\16`
5. Ensure pgAdmin 4 is installed (optional but helpful)

**For LLM:**
```powershell
# Download PostgreSQL 16 installer
Invoke-WebRequest -Uri "https://get.enterprisedb.com/postgresql/postgresql-16.3-1-windows-x64.exe" -OutFile "postgresql-16.3-1-windows-x64.exe"
# Install silently (requires admin)
.\postgresql-16.3-1-windows-x64.exe --mode unattended --superpassword "your_password" --servicename "postgresql-x64-16"
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" --version
# Expected: psql (PostgreSQL) 16.x
```

**🔄 Workaround:** If installation fails, PostgreSQL may already be installed. Check alternative versions:
```powershell
Get-Service postgresql* | Select-Object Name, Status
```

---

### 4. 🔐 Configure PostgreSQL Authentication (Development Only)

**⚠️ IMPORTANT:** This is for development only. For production, use proper authentication.

**🔍 Pre-check:**
```powershell
$pg_hba = "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
if (Test-Path $pg_hba) { Write-Host "✅ pg_hba.conf found" } else { Write-Host "❌ pg_hba.conf not found" }
```

**For Humans:**
1. Edit `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
2. Change authentication from `scram-sha-256` to `trust` for local connections:
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
```
3. Restart PostgreSQL service:
```powershell
Restart-Service postgresql-x64-16
```

**For LLM:**
```powershell
# Edit pg_hba.conf to use trust authentication
$pg_hba = "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
(Get-Content $pg_hba) -replace 'scram-sha-256', 'trust' | Set-Content $pg_hba
# Restart PostgreSQL service
Restart-Service postgresql-x64-16
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d postgres -c "SELECT 1;"
# Expected: Returns 1 without password prompt
```

**🔄 Workaround:** If trust is already configured, skip this step.

---

### 5. 🏗️ Create Database and User

**🔍 Pre-check:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d postgres -c "SELECT 1 FROM pg_database WHERE datname='faro_db';" 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Database faro_db already exists" } else { Write-Host "⚠️  Database not found - creating" }
```

**For Humans:**
1. Open pgAdmin or use psql
2. Run:
```sql
CREATE DATABASE faro_db;
CREATE USER faro WITH PASSWORD 'faro';
GRANT ALL PRIVILEGES ON DATABASE faro_db TO faro;
```

**For LLM:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE faro_db;" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE USER faro WITH PASSWORD 'faro';" 2>$null
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE faro_db TO faro;" 2>$null
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT current_database();"
# Expected: faro_db
```

**🔄 Workaround:** If database already exists, skip creation. If user exists, skip user creation.

---

### 6. 🌍 Install PostGIS Extension

**Required Version:** PostGIS 3.4.x (for PostgreSQL 16)

**🔍 Pre-check:**
```powershell
# Check if PostGIS extension is available in PostgreSQL
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (Test-Path $pgPath) {
    # Check if extension is available in pg_available_extensions
    $result = & $pgPath -U postgres -d postgres -c "SELECT 1 FROM pg_available_extensions WHERE name='postgis';" 2>$null
    $extensionAvailable = ($LASTEXITCODE -eq 0)

    if ($extensionAvailable) {
        Write-Host "✅ PostGIS extension available in PostgreSQL"

        # Get PostGIS version if already installed
        $versionResult = & $pgPath -U postgres -d postgres -c "SELECT extversion FROM pg_extension WHERE extname='postgis';" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "📍 PostGIS Version: $versionResult"
            Write-Host "✅ PostGIS already installed in database"
        } else {
            Write-Host "📍 PostGIS available but not yet installed in database"
        }
    } else {
        Write-Host "❌ PostGIS extension not available - needs to be installed"
    }

    # Check if PostGIS files exist in PostgreSQL directory
    $postgisDir = "C:\Program Files\PostgreSQL\16\share\contrib\postgis-3.4"
    if (Test-Path $postgisDir) {
        Write-Host "✅ PostGIS 3.4 files found in PostgreSQL directory"
        Write-Host "📍 Location: $postgisDir"
    } else {
        Write-Host "⚠️  PostGIS files not found - may need to install PostGIS bundle"
    }
} else {
    Write-Host "❌ PostgreSQL not found - install PostgreSQL first"
}
```

**For Humans:**
1. Download PostGIS Bundle for PostgreSQL 16 from https://download.osgeo.org/postgis/windows/pg16/
2. Run the installer
3. Select PostgreSQL 16 installation directory
4. Complete installation

**For LLM:**
```powershell
# Download PostGIS Bundle for PostgreSQL 16
Invoke-WebRequest -Uri "https://download.osgeo.org/postgis/windows/pg16/postgis-bundle-3.4.5x64.zip" -OutFile "postgis-bundle-3.4.5x64.zip"
# Extract
Expand-Archive -Path "postgis-bundle-3.4.5x64.zip" -DestinationPath "postgis"
# Run installer
.\postgis\postgis-bundle-3.4.5x64\postgis-pg16-setup.exe
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT PostGIS_Version();"
# Expected: Returns PostGIS version
```

**🔄 Workaround:** If PostGIS installer fails, try to enable extension if already bundled with PostgreSQL.

---

### 7. 🔗 Configure Alembic Connection String

**🔍 Pre-check:**
```powershell
$alembic_ini = "$env:FARO_HOME\server-core\alembic.ini"
if (Test-Path $alembic_ini) { Write-Host "✅ alembic.ini found" } else { Write-Host "❌ alembic.ini not found" }
```

**For Both:**
1. Edit `server-core\alembic.ini`
2. Update connection string:
```ini
sqlalchemy.url = postgresql+psycopg2://faro:faro@localhost:5432/faro_db
```

**✅ Verification:**
```powershell
Select-String -Path $alembic_ini -Pattern "sqlalchemy.url"
# Expected: Contains postgresql+psycopg2://faro:faro@localhost:5432/faro_db
```

---

### 8. 🚀 Run Database Migrations

**⚠️ CRITICAL:** The migrations have been pre-corrected for Windows. Do NOT modify them unless necessary.

**Migration Corrections Applied:**
- Migration 0006: Removed problematic UPDATE with enum
- Migration 0007: Removed CONCURRENTLY from index creation (not supported in transactions)
- Migration 0008: Removed ALTER SYSTEM commands (not supported in transactions)
- Migration 0009: Materialized views enabled (requires data in vehicleobservation)
- Migration 0010: TimescaleDB optional (gracefully skips if TimescaleDB not available)
- Migration 0011: Citus optional (gracefully skips if Citus not available)

**Note:** Migrations 0010 and 0011 will gracefully skip if extensions are not available.

**🔍 Pre-check:**
```powershell
cd $env:FARO_HOME\server-core
alembic current
# Expected: Shows current migration version
```

**For Humans:**
```powershell
cd $env:FARO_HOME\server-core
alembic upgrade head
```

**For LLM:**
```powershell
cd $env:FARO_HOME\server-core
alembic upgrade head
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "\dt"
# Should show 42 tables
```

**🔄 Workaround:** If migrations fail, check error message. Common issues:
- PostGIS not installed: Run step 6
- Database connection failed: Check PostgreSQL service
- Permission errors: Run PowerShell as administrator

---

### 9. 🌱 Create Seed Data

**🔍 Pre-check:**
```powershell
$seed_script = "$env:FARO_HOME\database\seeds\seed_data.py"
if (Test-Path $seed_script) { Write-Host "✅ seed_data.py found" } else { Write-Host "❌ seed_data.py not found" }
```

**For Humans:**
```powershell
cd $env:FARO_HOME\database\seeds
python seed_data.py
```

**For LLM:**
```powershell
cd $env:FARO_HOME\database\seeds
python seed_data.py
```

**✅ Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT COUNT(*) FROM agency;"
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT COUNT(*) FROM \"user\";"
# Expected: 3 agencies, 3 users
```

**🔄 Workaround:** If seed script fails, database may already have data. Check:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT COUNT(*) FROM agency;"
```

---

### 10. 🐳 Install Docker Desktop OR Configure Manual Extensions

**Required Version:** Docker Desktop 24.x or higher

**🔍 Pre-check:**
```powershell
# Check if Docker is in PATH
docker --version 2>$null
$inPath = ($LASTEXITCODE -eq 0)

if ($inPath) {
    Write-Host "✅ Docker found in PATH"

    # Get version
    $version = docker --version
    Write-Host "📍 Version: $version"

    # Get installation location
    $location = Get-Command docker | Select-Object -ExpandProperty Source
    Write-Host "📍 Location: $location"

    # Check compatibility (requires 24.x or higher)
    if ($version -match "24\.|25\.|26\.") {
        Write-Host "✅ Docker version compatible (24.x or higher)"
    } else {
        Write-Host "⚠️  Docker version may be outdated - consider upgrading"
    }

    # Check if Docker Desktop is running
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker Desktop is running"
            Write-Host "📍 Docker Engine Status: Active"
        } else {
            Write-Host "⚠️  Docker command found but Docker Desktop not running"
        }
    } catch {
        Write-Host "⚠️  Docker Desktop not running - needs to be started"
    }

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $dockerDir = Split-Path $location -Parent
    if ($dockerDir -in $pathDirs) {
        Write-Host "✅ Docker directory is in PATH"
    } else {
        Write-Host "⚠️  Docker directory not in PATH - may need to add manually"
    }
} else {
    Write-Host "❌ Docker not found in PATH - will install or use manual option"
}
```

**Option A: Docker Desktop (Recommended)**

**For Humans:**
1. Download Docker Desktop for Windows: https://www.docker.com/products/docker-desktop
2. Run the installer
3. Enable WSL 2 backend when prompted
4. Restart computer after installation
5. Start Docker Desktop

**Verification:**
```powershell
docker --version
# Expected: Docker version 24.x.x or higher
```

**Option B: Manual Extension Installation (If Docker is unavailable)**

**For Humans:**
If Docker cannot be installed (corporate policy, WSL 2 issues, etc.), install extensions directly in PostgreSQL:

1. Download TimescaleDB for Windows: https://github.com/timescale/timescaledb/releases/download/2.26.2/TimescaleDB.Windows.PG16.zip
2. Run setup.exe as administrator
3. Restart PostgreSQL service:
```powershell
Restart-Service postgresql-x64-16
```

4. Citus requires complex compilation on Windows - skip Citus for manual installation
5. Continue with step 14 (migrations will gracefully skip Citus)

**🔄 Workaround:** If Docker cannot be installed, use Option B. If both fail, system will work without TimescaleDB/Citus (reduced performance but functional).

---

### 10.5 💾 Install MinIO for Asset Storage (Optional)

**⚠️ IMPORTANT:** MinIO is **OPTIONAL**. The FARO system works perfectly without MinIO using local storage fallback.

**🔍 Pre-check:**
```powershell
docker --version 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Docker available - MinIO can be installed" } else { Write-Host "⚠️  Docker not available - will use local storage fallback" }
```

**Purpose of MinIO:**
- Storage for observation assets (images, audio, video)
- Evidence retention and audit trails
- Scalable storage for production deployments
- Web UI for asset management (Console on port 9001)

**Default Behavior (Without MinIO):**
- Assets stored in `./local_assets/` directory
- Automatic fallback when MinIO is not available
- No additional setup required
- Works out of the box

**Option A: Install MinIO via Docker (Recommended for Production)**

**For Humans:**
1. Ensure Docker Desktop is running
2. Navigate to `infra/docker` directory
3. Start MinIO:
```powershell
cd $env:FARO_HOME\infra\docker
docker-compose up -d minio
```
4. Access MinIO Console: http://localhost:9001 (user: minioadmin, password: minioadmin)

**For LLM:**
```powershell
cd $env:FARO_HOME\infra\docker
docker-compose up -d minio
```

**Option B: Skip MinIO (Use Local Storage - Default)**

If you don't need MinIO, simply skip this step. The system will automatically use local storage.

**Verification:**
```powershell
# If MinIO is installed
docker ps | findstr minio
# Expected: Shows minio container running

# If using local storage (default)
Test-Path "$env:FARO_HOME\server-core\local_assets"
# Expected: True (directory will be created on first upload)
```

**Configuration:**

To enable MinIO after installation, set environment variable:
```powershell
$env:S3_ENABLED="true"
```

Or add to `.env` file in server-core:
```
S3_ENABLED=true
S3_ENDPOINT=http://localhost:9000
```

**Port Notes:**
- **Port 9000**: MinIO S3 API (reserved for MinIO)
- **Port 9001**: MinIO Console UI (reserved for MinIO)
- **Port 9002**: Analytics Dashboard (uses 9002 to avoid MinIO conflicts)

**🔄 Workaround:** If MinIO installation fails, system automatically falls back to local storage. No action required.

---

### 11. ⏱️ Install TimescaleDB Extension (Optional)

**Required Version:** TimescaleDB 2.14.x or higher (for PostgreSQL 16)

**🔍 Pre-check:**
```powershell
# Check if TimescaleDB extension is available in PostgreSQL
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (Test-Path $pgPath) {
    # Check if extension is available in pg_available_extensions
    $result = & $pgPath -U postgres -d postgres -c "SELECT 1 FROM pg_available_extensions WHERE name='timescaledb';" 2>$null
    $extensionAvailable = ($LASTEXITCODE -eq 0)

    if ($extensionAvailable) {
        Write-Host "✅ TimescaleDB extension available in PostgreSQL"

        # Get TimescaleDB version if already installed
        $versionResult = & $pgPath -U postgres -d postgres -c "SELECT extversion FROM pg_extension WHERE extname='timescaledb';" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "📍 TimescaleDB Version: $versionResult"
            Write-Host "✅ TimescaleDB already installed in database"
        } else {
            Write-Host "📍 TimescaleDB available but not yet installed in database"
        }
    } else {
        Write-Host "❌ TimescaleDB extension not available - needs to be installed (optional)"
    }

    # Check if TimescaleDB files exist in PostgreSQL directory
    $timescaleDir = "C:\Program Files\PostgreSQL\16\share\extension\timescaledb.control"
    if (Test-Path $timescaleDir) {
        Write-Host "✅ TimescaleDB files found in PostgreSQL directory"
        Write-Host "📍 Location: C:\Program Files\PostgreSQL\16\share\extension\"
    } else {
        Write-Host "⚠️  TimescaleDB files not found - may need to install TimescaleDB"
    }
} else {
    Write-Host "❌ PostgreSQL not found - install PostgreSQL first"
}
```

**If using Docker (Option A from step 10):**
```powershell
docker run -d --name timescaledb -p 5433:5432 `
  -e POSTGRES_PASSWORD=password `
  timescale/timescaledb-ha:pg16
```

**If using Manual Installation (Option B from step 10):**
TimescaleDB is already installed in PostgreSQL 16. Verify installation:
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT * FROM pg_available_extensions WHERE name='timescaledb';"
# Should show timescaledb in the list
```

**🔄 Workaround:** If TimescaleDB cannot be installed, system will work without time-series optimization (reduced performance for large time-series queries).

---

### 12. 🔄 Install Citus Extension (Optional - Skip if Docker unavailable)

**Required Version:** Citus 12.x or higher (for PostgreSQL 16)

**🔍 Pre-check:**
```powershell
# Check if Docker is available (Citus requires Docker on Windows)
docker ps 2>$null
$dockerAvailable = ($LASTEXITCODE -eq 0)

if ($dockerAvailable) {
    Write-Host "✅ Docker available - can install Citus via Docker"

    # Check if Citus container is already running
    $citusRunning = docker ps --filter "name=citus" --format "{{.Names}}" 2>$null
    if ($citusRunning) {
        Write-Host "✅ Citus container already running: $citusRunning"

        # Get Citus version from container
        $citusVersion = docker exec citus psql -U postgres -c "SELECT extversion FROM pg_extension WHERE extname='citus';" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "📍 Citus Version: $citusVersion"
        }
    } else {
        Write-Host "⚠️  Citus container not running - will install if needed"
    }
} else {
    Write-Host "❌ Docker not available - Citus requires Docker on Windows (optional component)"
    Write-Host "⚠️  Will skip Citus installation - system will work without horizontal scaling"
}

# Alternative: Check if Citus is installed directly in PostgreSQL (rare on Windows)
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (Test-Path $pgPath) {
    $result = & $pgPath -U postgres -d postgres -c "SELECT 1 FROM pg_available_extensions WHERE name='citus';" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Citus extension available in PostgreSQL (manual installation)"
    }
}
```

**If using Docker (Option A from step 10):**
```powershell
docker run -d --name citus-coordinator `
  -p 5500:5432 `
  -e POSTGRES_PASSWORD=password `
  citusdata/citus:postgres16
```

**If using Manual Installation (Option B from step 10):**
Citus requires complex compilation on Windows and is not available for manual installation. Skip Citus and continue with step 14. The system will work without Citus, but without horizontal scaling capabilities.

**🔄 Workaround:** If Citus cannot be installed, system will work without horizontal scaling (reduced performance for multi-tenant scenarios).

---

### 13. 🔍 Automatic Detection and Configuration

**🔍 Pre-check:**
```powershell
docker ps 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Docker available" } else { Write-Host "⚠️  Docker not available" }
```

Run this script to detect which option to use and configure migrations accordingly:

```powershell
.\detect_environment.ps1
```

**Based on output:**
- **Exit code 0:** Use Docker (Option A) - Full installation with TimescaleDB and Citus
- **Exit code 1:** Use Manual (Option B) - TimescaleDB available, skip Citus
- **Exit code 2:** Install either Docker or TimescaleDB first

**🔄 Workaround:** Script already provides guidance based on environment. Follow recommendations.

---

### 14. 🎱 Configure PgBouncer (Recommended)

**Required Version:** PgBouncer 1.21.x or higher

**🔍 Pre-check:**
```powershell
# Check if PgBouncer is installed
$pgbouncerPaths = @(
    "$env:FARO_HOME\pgbouncer\pgbouncer-1.24.1-windows-x86_64\pgbouncer.exe",
    "C:\Program Files\PgBouncer\pgbouncer.exe",
    "C:\pgbouncer\pgbouncer.exe"
)

$pgbouncerInstalled = $false
$pgbouncerLocation = $null

foreach ($path in $pgbouncerPaths) {
    if (Test-Path $path) {
        $pgbouncerInstalled = $true
        $pgbouncerLocation = $path
        break
    }
}

if ($pgbouncerInstalled) {
    Write-Host "✅ PgBouncer found"
    Write-Host "📍 Location: $pgbouncerLocation"

    # Get version
    $version = & $pgbouncerLocation --version 2>$null
    Write-Host "📍 Version: $version"

    # Check compatibility (requires 1.21.x or higher)
    if ($version -match "1\.2[1-9]\.|1\.[3-9]\.|2\.") {
        Write-Host "✅ PgBouncer version compatible (1.21.x or higher)"
    } else {
        Write-Host "⚠️  PgBouncer version may be outdated - consider upgrading"
    }

    # Check if PgBouncer is running
    $process = Get-Process -Name "pgbouncer" -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "✅ PgBouncer is running (PID: $($process.Id))"
    } else {
        Write-Host "⚠️  PgBouncer not running - will start later"
    }

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $pgbouncerDir = Split-Path $pgbouncerLocation -Parent
    if ($pgbouncerDir -in $pathDirs) {
        Write-Host "✅ PgBouncer directory is in PATH"
    } else {
        Write-Host "⚠️  PgBouncer directory not in PATH - may need to add manually"
    }
} else {
    Write-Host "❌ PgBouncer not found - will install (optional component)"
}
```

**For Humans:**
1. Download PgBouncer for Windows: https://github.com/pgbouncer/pgbouncer/releases/download/pgbouncer_1_24_1/pgbouncer-1.24.1-windows-x86_64.zip
2. Extract to `$env:FARO_HOME\pgbouncer`
3. Create `pgbouncer-faro.ini` with content:
```ini
[databases]
faro_db = host=localhost port=5432 dbname=faro_db user=faro password=faro

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = userlist.txt

# Pool configuration
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1

# Timeouts
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15
query_timeout = 0
client_idle_timeout = 0
```

4. Create `userlist.txt` with MD5 hash:
```
"faro" "md5b68ae84b7b54ad52dda52f3c16792cc1"
```

5. Start PgBouncer:
```powershell
cd $env:FARO_HOME\pgbouncer
.\pgbouncer-1.24.1-windows-x86_64\pgbouncer.exe pgbouncer-faro.ini
```

**For LLM:**
```powershell
cd $env:FARO_HOME
# Download PgBouncer
Invoke-WebRequest -Uri "https://github.com/pgbouncer/pgbouncer/releases/download/pgbouncer_1_24_1/pgbouncer-1.24.1-windows-x86_64.zip" -OutFile "pgbouncer-1.24.1-windows-x86_64.zip"
# Extract
Expand-Archive -Path "pgbouncer-1.24.1-windows-x86_64.zip" -DestinationPath "pgbouncer"
# Configuration files are already created in pgbouncer directory
# Start PgBouncer
cd pgbouncer
.\pgbouncer-1.24.1-windows-x86_64\pgbouncer.exe pgbouncer-faro.ini
```

**Verification:**
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p 6432 -U faro -d faro_db
# Should connect successfully
```

---

### 15. 📊 Configure Prometheus (Recommended)

**Required Version:** Prometheus 2.53.x or higher

**🔍 Pre-check:**
```powershell
# Check if Prometheus is installed
$prometheusPaths = @(
    "$env:FARO_HOME\prometheus\prometheus-2.53.1.windows-amd64\prometheus.exe",
    "C:\Program Files\Prometheus\prometheus.exe",
    "C:\prometheus\prometheus.exe"
)

$prometheusInstalled = $false
$prometheusLocation = $null

foreach ($path in $prometheusPaths) {
    if (Test-Path $path) {
        $prometheusInstalled = $true
        $prometheusLocation = $path
        break
    }
}

if ($prometheusInstalled) {
    Write-Host "✅ Prometheus found"
    Write-Host "📍 Location: $prometheusLocation"

    # Get version
    $version = & $prometheusLocation --version 2>$null
    Write-Host "📍 Version: $version"

    # Check compatibility (requires 2.53.x or higher)
    if ($version -match "2\.5[3-9]\.|2\.[6-9]\.|3\.") {
        Write-Host "✅ Prometheus version compatible (2.53.x or higher)"
    } else {
        Write-Host "⚠️  Prometheus version may be outdated - consider upgrading"
    }

    # Check if Prometheus is running
    $process = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "✅ Prometheus is running (PID: $($process.Id))"
        Write-Host "📍 Prometheus UI should be available at http://localhost:9090"
    } else {
        Write-Host "⚠️  Prometheus not running - will start later"
    }

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $prometheusDir = Split-Path $prometheusLocation -Parent
    if ($prometheusDir -in $pathDirs) {
        Write-Host "✅ Prometheus directory is in PATH"
    } else {
        Write-Host "⚠️  Prometheus directory not in PATH - may need to add manually"
    }
} else {
    Write-Host "❌ Prometheus not found - will install (optional component)"
}
```

**For Humans:**
1. Download Prometheus for Windows: https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.windows-amd64.zip
2. Extract to `$env:FARO_HOME\prometheus`
3. Copy `infra\observability\prometheus\prometheus.yml` to prometheus directory
4. Start Prometheus:
```powershell
cd $env:FARO_HOME\prometheus\prometheus-2.53.1.windows-amd64
.\prometheus.exe
```
5. Access Prometheus UI: http://localhost:9090

**For LLM:**
```powershell
cd $env:FARO_HOME
# Download Prometheus
Invoke-WebRequest -Uri "https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.windows-amd64.zip" -OutFile "prometheus-2.53.1.windows-amd64.zip"
# Extract
Expand-Archive -Path "prometheus-2.53.1.windows-amd64.zip" -DestinationPath "prometheus"
# Copy configuration
Copy-Item "infra\observability\prometheus\prometheus.yml" "prometheus\prometheus-2.53.1.windows-amd64\prometheus.yml" -Force
# Start Prometheus
cd prometheus\prometheus-2.53.1.windows-amd64
.\prometheus.exe
```

---

## Verification Steps

### Database Verification
```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "\dt"
# Expected: 42 tables

& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT COUNT(*) FROM agency;"
# Expected: 3

& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT COUNT(*) FROM \"user\";"
# Expected: 3
```

### PgBouncer Verification
```powershell
# Test PgBouncer connection
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p 6432 -U faro -d faro_db -c "SELECT 1;"
# Expected: Returns 1
```

### Prometheus Verification
```powershell
# Access Prometheus UI
# Open browser to: http://localhost:9090
# Check targets status in UI
```

---

## Server Startup and Verification

### 16. 🚀 Start FARO Server

**For Humans:**
1. Open PowerShell in `server-core` directory
2. Start the server:
```powershell
cd $env:FARO_HOME\server-core
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**For LLM:**
```powershell
cd $env:FARO_HOME\server-core
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\...\\FARO\\server-core']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**CRITICAL:** If you see errors during startup:
- Check for missing dependencies: `pip install -r requirements.txt`
- Check database connection: Ensure PostgreSQL is running and faro_db exists
- Check for import errors: Verify all imports are correct in code

---

### 17. ✅ Verify Server Health Check

**For Both:**
```powershell
# Test health check endpoint
Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "FARO Server Core",
  "version": "1.0.0"
}
```

**Alternative using curl (if available):**
```powershell
curl http://localhost:8000/health
```

**For LLM (PowerShell):**
```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get
$response.Content | ConvertFrom-Json
# Expected: status = "healthy"
```

**Verification Criteria:**
- ✅ HTTP status code: 200
- ✅ Response contains "status": "healthy"
- ✅ Response contains service name
- ✅ Response contains version

---

### 18. 🌐 Verify Web Interface (Intelligence Console)

**For Humans:**
1. Open browser
2. Navigate to: http://localhost:8000
3. Verify page loads successfully
4. Check for API documentation at: http://localhost:8000/docs

**For LLM:**
```powershell
# Test root endpoint
$response = Invoke-WebRequest -Uri "http://localhost:8000" -Method Get
$response.Content | ConvertFrom-Json
# Expected: Contains name, version, description, docs

# Test API documentation endpoint
$docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get
# Expected: HTTP status code 200
```

**Expected Output from Root Endpoint:**
```json
{
  "name": "FARO Server Core",
  "version": "1.0.0",
  "description": "FARO - Sistema de Análise de Risco Operacional",
  "docs": "/docs"
}
```

**Verification Criteria:**
- ✅ HTTP status code: 200
- ✅ Response contains service name
- ✅ Response contains version
- ✅ Response contains docs path
- ✅ Browser displays page without errors

---

### 19. 📱 Verify Mobile Agent Connection

**For Humans:**
1. Ensure FARO Server is running on http://localhost:8000
2. Start Android app (if available) or use API simulation
3. Test mobile endpoint:
```powershell
# Test mobile health check
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/mobile/health" -Method Get
```

**For LLM:**
```powershell
# Test mobile endpoint
$mobileResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/mobile/health" -Method Get
$mobileResponse.Content | ConvertFrom-Json
# Expected: Mobile health check response
```

**Test Authentication Endpoint:**
```powershell
# Test login endpoint
$body = @{
    email = "admin@faro.pol"
    password = "password"
} | ConvertTo-Json

$authResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method Post -Body $body -ContentType "application/json"
$authResponse.Content | ConvertFrom-Json
# Expected: Returns access token
```

**Verification Criteria:**
- ✅ Mobile health endpoint returns HTTP 200
- ✅ Authentication endpoint accepts credentials
- ✅ Access token is returned on successful login
- ✅ Server responds to mobile requests without errors

**Note:** For full mobile testing, you would need:
- Android app installed on device/emulator
- App configured with server URL (http://localhost:8000 or IP address)
- Network connectivity between device and server

---

### 20. 🔬 Complete System Verification

**For Both:**
```powershell
# Run all verification checks in sequence

# 1. Server Health
Write-Host "Checking server health..."
$health = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get
if ($health.StatusCode -eq 200) { Write-Host "✅ Server health check passed" } else { Write-Host "❌ Server health check failed" }

# 2. Root Endpoint
Write-Host "Checking root endpoint..."
$root = Invoke-WebRequest -Uri "http://localhost:8000" -Method Get
if ($root.StatusCode -eq 200) { Write-Host "✅ Root endpoint passed" } else { Write-Host "❌ Root endpoint failed" }

# 3. API Documentation
Write-Host "Checking API documentation..."
$docs = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get
if ($docs.StatusCode -eq 200) { Write-Host "✅ API documentation accessible" } else { Write-Host "❌ API documentation failed" }

# 4. Database Connection
Write-Host "Checking database connection..."
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT 1;" -o db_check.txt
$dbCheck = Get-Content db_check.txt
if ($dbCheck -match "1") { Write-Host "✅ Database connection passed" } else { Write-Host "❌ Database connection failed" }
Remove-Item db_check.txt

Write-Host "Verification complete!"
```

**Success Criteria:**
- ✅ Server running on port 8000
- ✅ Health check returns "healthy"
- ✅ Web interface accessible via browser
- ✅ API documentation accessible
- ✅ Database connection working
- ✅ Mobile endpoints responding
- ✅ Authentication working with seed credentials

---

## Web Services Startup and Verification

### 21. 🌐 Start Web Intelligence Console

**Required Version:** Node.js 18.x or higher (for Next.js 15.x)

**🔍 Pre-check:**
```powershell
# Check if Node.js is in PATH
node --version 2>$null
$inPath = ($LASTEXITCODE -eq 0)

if ($inPath) {
    Write-Host "✅ Node.js found in PATH"

    # Get version
    $version = node --version
    Write-Host "📍 Node.js Version: $version"

    # Get installation location
    $location = Get-Command node | Select-Object -ExpandProperty Source
    Write-Host "📍 Location: $location"

    # Check compatibility (requires 18.x or higher for Next.js 15.x)
    if ($version -match "v18\.|v19\.|v20\.|v21\.|v22\.") {
        Write-Host "✅ Node.js version compatible (18.x or higher)"
    } else {
        Write-Host "⚠️  Node.js version $version may not be compatible - Next.js 15.x requires 18.x or higher"
    }

    # Check npm version
    $npmVersion = npm --version
    Write-Host "📍 npm Version: $npmVersion"

    # Check if in PATH
    $pathDirs = $env:Path -split ';'
    $nodeDir = Split-Path $location -Parent
    if ($nodeDir -in $pathDirs) {
        Write-Host "✅ Node.js directory is in PATH"
    } else {
        Write-Host "⚠️  Node.js directory not in PATH - may need to add manually"
    }
} else {
    Write-Host "❌ Node.js not found in PATH - needs to be installed"
    Write-Host "⚠️  Download from: https://nodejs.org/ (LTS version recommended)"
}

# Check if port 3000 is available
netstat -ano | findstr ":3000"
if ($LASTEXITCODE -eq 0) { Write-Host "⚠️  Port 3000 already in use" } else { Write-Host "✅ Port 3000 available" }
```

**For Humans:**
1. Open PowerShell in `web-intelligence-console` directory
2. Install dependencies (if not already installed):
```powershell
cd $env:FARO_HOME\web-intelligence-console
npm install
```
3. Start the development server:
```powershell
npm run dev
```

**For LLM:**
```powershell
cd $env:FARO_HOME\web-intelligence-console
# Install dependencies if needed
if (-not (Test-Path "node_modules")) { npm install }
# Start development server
npm run dev
```

**Expected Output:**
```
> faro-web-intelligence@1.0.0 dev
> next dev

▲ Next.js 15.5.15
- Local:        http://localhost:3000
- Environments: .env.local
```

**✅ Verification:**
```powershell
# Test web console
$webConsole = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -UseBasicParsing
if ($webConsole.StatusCode -eq 200) { Write-Host "✅ Web Intelligence Console running" } else { Write-Host "❌ Web Intelligence Console failed" }
```

**🔄 Workaround:** If port 3000 is in use:
```powershell
# Option A: Kill process using port 3000
$port3000 = netstat -ano | findstr ":3000"
if ($port3000) {
    $pid = ($port3000 -split '\s+')[-1]
    Stop-Process -Id $pid -Force
    npm run dev
}

# Option B: Use different port
$env:PORT=3001
npm run dev
```

---

### 22. 📊 Start Analytics Dashboard

**⚠️ CRITICAL CORRECTION:** The directory `analytics-dashboard` uses a hyphen, but Python modules require underscores. The directory must be renamed before starting.

**⚠️ PORT NOTE:** Port 9000 is reserved for MinIO S3 and port 9001 for MinIO Console. This dashboard uses port 9002 to avoid conflicts.

**🔍 Pre-check:**
```powershell
# Check if directory needs renaming
if (Test-Path "$env:FARO_HOME\server-core\analytics-dashboard") {
    Write-Host "⚠️  Directory uses hyphen - needs renaming to underscore"
} elseif (Test-Path "$env:FARO_HOME\server-core\analytics_dashboard") {
    Write-Host "✅ Directory already renamed to underscore"
} else {
    Write-Host "❌ Analytics dashboard directory not found"
}

# Check if port 9002 is available
netstat -ano | findstr ":9002"
if ($LASTEXITCODE -eq 0) { Write-Host "⚠️  Port 9002 already in use" } else { Write-Host "✅ Port 9002 available" }
```

**For Humans:**
1. Open PowerShell in `server-core` directory
2. Rename directory (if needed):
```powershell
cd $env:FARO_HOME\server-core
if (Test-Path "analytics-dashboard") {
    mv analytics-dashboard analytics_dashboard
    Write-Host "✅ Directory renamed from analytics-dashboard to analytics_dashboard"
}
```
3. Install dashboard dependencies:
```powershell
cd analytics_dashboard
pip install -r requirements.txt
```
4. Start the dashboard:
```powershell
cd $env:FARO_HOME\server-core
uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload
```

**For LLM:**
```powershell
cd $env:FARO_HOME\server-core
# Rename directory if needed
if (Test-Path "analytics-dashboard") {
    mv analytics-dashboard analytics_dashboard
}
# Install dependencies
cd analytics_dashboard
pip install -r requirements.txt
# Start dashboard
cd $env:FARO_HOME\server-core
uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload
```

**Expected Output:**
```
[DASHBOARD] Dashboard: http://localhost:9002/dashboard
[API] API: http://localhost:9002/api/v1
[WS] WebSocket: ws://localhost:9002/ws
INFO:     Uvicorn running on http://0.0.0.0:9002 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Verification:**
```powershell
# Test dashboard endpoint
$dashboard = Invoke-WebRequest -Uri "http://localhost:9002/api/v1/health" -Method Get
if ($dashboard.StatusCode -eq 200) { Write-Host "✅ Analytics Dashboard running" } else { Write-Host "❌ Analytics Dashboard failed" }

# Test dashboard UI
$dashboardUI = Invoke-WebRequest -Uri "http://localhost:9002/dashboard" -Method Get -UseBasicParsing
if ($dashboardUI.StatusCode -eq 200) { Write-Host "✅ Dashboard UI accessible" } else { Write-Host "❌ Dashboard UI failed" }
```

**🔄 Workaround:** If port 9002 is in use:
```powershell
# Kill process using port 9002
$port9002 = netstat -ano | findstr ":9002"
if ($port9002) {
    $pid = ($port9002 -split '\s+')[-1]
    Stop-Process -Id $pid -Force
    uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload
}

# Or use different port
uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9003 --reload
```

**Alternative Method (if uvicorn fails):**
```powershell
cd $env:FARO_HOME\server-core\analytics_dashboard
python app.py
```

**Note:** The `python app.py` method may show deprecation warnings but should still work.

---

### 23. 🚀 Start All Web Services (Complete Startup)

**For Humans:**
To start all three services simultaneously, open three separate PowerShell windows:

**Window 1 - Server Core:**
```powershell
cd $env:FARO_HOME\server-core
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Window 2 - Web Intelligence Console:**
```powershell
cd $env:FARO_HOME\web-intelligence-console
npm run dev
```

**Window 3 - Analytics Dashboard:**
```powershell
cd $env:FARO_HOME\server-core
# Ensure directory is renamed
if (Test-Path "analytics-dashboard") { mv analytics-dashboard analytics_dashboard }
uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload
```

**For LLM (Background Processes):**
```powershell
# Start Server Core
$serverJob = Start-Job -ScriptBlock {
    cd $env:FARO_HOME\server-core
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Start Web Intelligence Console
$consoleJob = Start-Job -ScriptBlock {
    cd $env:FARO_HOME\web-intelligence-console
    npm run dev
}

# Start Analytics Dashboard
$dashboardJob = Start-Job -ScriptBlock {
    cd $env:FARO_HOME\server-core
    if (Test-Path "analytics-dashboard") { mv analytics-dashboard analytics_dashboard }
    uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload
}

# Wait a few seconds for services to start
Start-Sleep -Seconds 10

# Check status
Get-Job | Select-Object Name, State
```

---

### 24. ✅ Complete Web Services Verification

**For Both:**
```powershell
# Verify all three services are running

Write-Host "=== FARO Web Services Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Server Core (Port 8000)
Write-Host "Checking Server Core (port 8000)..."
try {
    $server = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    if ($server.StatusCode -eq 200) { Write-Host "✅ Server Core running" -ForegroundColor Green } else { Write-Host "❌ Server Core failed" -ForegroundColor Red }
} catch {
    Write-Host "❌ Server Core not responding" -ForegroundColor Red
}

# 2. Web Intelligence Console (Port 3000)
Write-Host "Checking Web Intelligence Console (port 3000)..."
try {
    $console = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($console.StatusCode -eq 200) { Write-Host "✅ Web Intelligence Console running" -ForegroundColor Green } else { Write-Host "❌ Web Intelligence Console failed" -ForegroundColor Red }
} catch {
    Write-Host "❌ Web Intelligence Console not responding" -ForegroundColor Red
}

# 3. Analytics Dashboard (Port 9002)
Write-Host "Checking Analytics Dashboard (port 9002)..."
try {
    $dashboard = Invoke-WebRequest -Uri "http://localhost:9002/api/v1/health" -Method Get -TimeoutSec 5
    if ($dashboard.StatusCode -eq 200) { Write-Host "✅ Analytics Dashboard running" -ForegroundColor Green } else { Write-Host "❌ Analytics Dashboard failed" -ForegroundColor Red }
} catch {
    Write-Host "❌ Analytics Dashboard not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Service URLs ===" -ForegroundColor Cyan
Write-Host "Server Core API:           http://localhost:8000"
Write-Host "Server API Docs:          http://localhost:8000/docs"
Write-Host "Web Intelligence Console: http://localhost:3000"
Write-Host "Analytics Dashboard:       http://localhost:9002/dashboard"
Write-Host "Analytics API:            http://localhost:9002/api/v1"
Write-Host "Analytics WebSocket:      ws://localhost:9002/ws"
```

**Success Criteria:**
- ✅ Server Core responding on port 8000
- ✅ Web Intelligence Console responding on port 3000
- ✅ Analytics Dashboard responding on port 9002
- ✅ All three services accessible via browser
- ✅ API documentation accessible
- ✅ Dashboard UI loads without errors

---

### 25. 🔧 Common Issues and Solutions for Web Services

**Issue: "ModuleNotFoundError: No module named 'analytics_dashboard'"**
- **Cause:** Directory name uses hyphen (`analytics-dashboard`) but Python requires underscore
- **Solution:** Rename directory before starting:
```powershell
cd $env:FARO_HOME\server-core
mv analytics-dashboard analytics_dashboard
```

**Issue: Port already in use (8000, 3000, or 9002)**
- **Cause:** Previous instance still running or another service using the port
- **Solution A:** Kill the process:
```powershell
# Find and kill process on specific port
$port = 8000  # Change to 3000 or 9002 as needed
$process = netstat -ano | findstr ":$port"
if ($process) {
    $pid = ($process -split '\s+')[-1]
    Stop-Process -Id $pid -Force
}
```
- **Solution B:** Use different port:
```powershell
# Server Core
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Web Console
$env:PORT=3001
npm run dev

# Analytics Dashboard
uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9003 --reload
```

**Issue: npm install fails for Web Intelligence Console**
- **Cause:** Missing Node.js or network issues
- **Solution A:** Install Node.js from https://nodejs.org/
- **Solution B:** Clear npm cache and retry:
```powershell
npm cache clean --force
npm install
```
- **Solution C:** Use npm legacy peer deps (if dependency conflicts):
```powershell
npm install --legacy-peer-deps
```

**Issue: Next.js shows "Invalid next.config.js options detected"**
- **Cause:** Deprecated configuration option in next.config.js
- **Solution:** This is a warning, not an error. The console will still work. To fix:
```powershell
# Edit web-intelligence-console/next.config.js
# Remove or update deprecated options like 'swcMinify'
```

**Issue: Analytics Dashboard shows deprecation warnings**
- **Cause:** Using deprecated `@app.on_event("startup")` instead of lifespan
- **Solution:** This is a warning, not an error. The dashboard will still work. To fix, update app.py to use lifespan context manager.

**Issue: Services start but browser shows "Connection refused"**
- **Cause:** Firewall blocking or services not actually running
- **Solution A:** Check Windows Firewall:
```powershell
# Allow ports through Windows Firewall (run as admin)
New-NetFirewallRule -DisplayName "FARO Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "FARO Web Console" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "FARO Dashboard" -Direction Inbound -LocalPort 9002 -Protocol TCP -Action Allow
```
- **Solution B:** Verify services are actually running:
```powershell
netstat -ano | findstr ":8000"
netstat -ano | findstr ":3000"
netstat -ano | findstr ":9002"
```

**Issue: Analytics Dashboard dependencies missing**
- **Cause:** requirements.txt not installed
- **Solution:**
```powershell
cd $env:FARO_HOME\server-core\analytics_dashboard
pip install -r requirements.txt
```

---

### 26. 🔄 Alternative Startup Methods

**Method A: Using Docker Compose (If Available)**

If you have Docker Desktop installed and prefer containerized deployment:

```powershell
cd $env:FARO_HOME
docker-compose up -d
```

This will start all services in containers with automatic networking.

**Method B: Using PowerShell Background Jobs**

Run all services in background without separate windows:

```powershell
cd $env:FARO_HOME\server-core
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

cd $env:FARO_HOME\web-intelligence-console
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

cd $env:FARO_HOME\server-core
if (Test-Path "analytics-dashboard") { mv analytics-dashboard analytics_dashboard }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload"
```

**Method C: Using Windows Terminal Profiles**

Create Windows Terminal profiles for each service for quick access:

1. Open Windows Terminal settings
2. Add new profile for Server Core:
```json
{
    "name": "FARO Server Core",
    "commandline": "powershell.exe -NoExit -Command \"cd $env:FARO_HOME\\server-core; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\"",
    "startingDirectory": "%USERPROFILE%\\FARO\\server-core"
}
```
3. Add new profile for Web Console:
```json
{
    "name": "FARO Web Console",
    "commandline": "powershell.exe -NoExit -Command \"cd $env:FARO_HOME\\web-intelligence-console; npm run dev\"",
    "startingDirectory": "%USERPROFILE%\\FARO\\web-intelligence-console"
}
```
4. Add new profile for Analytics Dashboard:
```json
{
    "name": "FARO Dashboard",
    "commandline": "powershell.exe -NoExit -Command \"cd $env:FARO_HOME\\server-core; if (Test-Path analytics-dashboard) { mv analytics-dashboard analytics_dashboard }; uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload\"",
    "startingDirectory": "%USERPROFILE%\\FARO\\server-core"
}
```

**Method D: Startup Script**

Create a batch file or PowerShell script to start all services at once:

**start-faro-services.bat:**
```batch
@echo off
start "FARO Server Core" cmd /k "cd /d %USERPROFILE%\FARO\server-core && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "FARO Web Console" cmd /k "cd /d %USERPROFILE%\FARO\web-intelligence-console && npm run dev"
start "FARO Dashboard" cmd /k "cd /d %USERPROFILE%\FARO\server-core && if exist analytics-dashboard (mv analytics-dashboard analytics_dashboard) && uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload"
```

**start-faro-services.ps1:**
```powershell
$FARO_HOME = "$env:USERPROFILE\FARO"

# Start Server Core
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\server-core'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WindowStyle Normal

# Start Web Console
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\web-intelligence-console'; npm run dev" -WindowStyle Normal

# Start Analytics Dashboard
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\server-core'; if (Test-Path 'analytics-dashboard') { mv analytics-dashboard analytics_dashboard }; uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port 9002 --reload" -WindowStyle Normal

Write-Host "All FARO services started. Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

---

### 27. 📝 Service Dependencies and Startup Order

**Critical Dependency Chain:**
1. **PostgreSQL** must be running before Server Core
2. **Server Core** must be running before Web Intelligence Console (for API calls)
3. **Analytics Dashboard** can run independently but benefits from Server Core metrics

**Recommended Startup Order:**
1. Start PostgreSQL service (if not running)
2. Start Server Core (port 8000)
3. Start Web Intelligence Console (port 3000)
4. Start Analytics Dashboard (port 9002)

**Verification Order:**
1. Verify PostgreSQL connection
2. Verify Server Core health check
3. Verify Web Intelligence Console loads
4. Verify Analytics Dashboard connects to Server Core

**Graceful Shutdown Order:**
1. Stop Analytics Dashboard (port 9002)
2. Stop Web Intelligence Console (port 3000)
3. Stop Server Core (port 8000)
4. Stop PostgreSQL (if needed)

---

### 28. 🔍 Advanced Troubleshooting

**Check Service Logs:**

**Server Core Logs:**
- Console output in the PowerShell window where uvicorn is running
- Check for database connection errors
- Check for import errors

**Web Intelligence Console Logs:**
- Console output in the PowerShell window where npm run dev is running
- Check browser console (F12) for frontend errors
- Check for API connection errors

**Analytics Dashboard Logs:**
- Console output in the PowerShell window where uvicorn is running
- Check for WebSocket connection errors
- Check for metrics collection errors

**Database Connection Issues:**
```powershell
# Test PostgreSQL connection directly
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d faro_db -c "SELECT 1;"
# If this fails, PostgreSQL service may not be running
Get-Service postgresql*
# Start PostgreSQL if needed
Start-Service postgresql-x64-16
```

**Redis Connection Issues (if using cache):**
```powershell
# Check if Redis is running
redis-cli ping
# Expected: PONG
# If Redis not installed, cache features will gracefully fallback to direct queries
```

**Network Issues:**
```powershell
# Test localhost connectivity
Test-NetConnection -ComputerName localhost -Port 8000
Test-NetConnection -ComputerName localhost -Port 3000
Test-NetConnection -ComputerName localhost -Port 9002

# If TcpTestSucceeded is False, check firewall
```

**Performance Issues:**
- Server Core slow: Check database query performance, enable PgBouncer
- Web Console slow: Check browser console for render issues, enable React DevTools
- Dashboard slow: Check WebSocket connection, reduce refresh interval

---

## 📊 Installation Report (LLM Generated)

**After completing the installation, the LLM should generate a report with the following structure:**

```powershell
Write-Host "=== FARO Installation Report ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Components Successfully Installed:" -ForegroundColor Green
Write-Host "  - Python 3.12 LTS"
Write-Host "  - PostgreSQL 16"
Write-Host "  - PostGIS Extension"
Write-Host "  - Database Migrations"
Write-Host "  - Seed Data"
Write-Host "  - FARO Server"
Write-Host ""
Write-Host "🔧 Workarounds Applied:" -ForegroundColor Yellow
Write-Host "  - [List any workarounds applied during installation]"
Write-Host ""
Write-Host "⚠️  Components Skipped (Optional):" -ForegroundColor Yellow
Write-Host "  - TimescaleDB: [Installed/Skipped - Reason]"
Write-Host "  - Citus: [Installed/Skipped - Reason]"
Write-Host "  - PgBouncer: [Installed/Skipped - Reason]"
Write-Host "  - Prometheus: [Installed/Skipped - Reason]"
Write-Host ""
Write-Host "❌ Critical Issues (if any):" -ForegroundColor Red
Write-Host "  - [List any critical issues that prevented full installation]"
Write-Host ""
Write-Host "📝 Alternative Options for Manual Resolution:" -ForegroundColor Cyan
Write-Host "  - [List manual steps to resolve skipped components]"
Write-Host ""
Write-Host "🎯 Installation Status: [SUCCESS/PARTIAL/FAILED]" -ForegroundColor $(if ($success) { "Green" } else { "Red" })
```

**Example Report:**
```
=== FARO Installation Report ===

✅ Components Successfully Installed:
  - Python 3.12 LTS
  - PostgreSQL 16
  - PostGIS Extension
  - Database Migrations (11/11)
  - Seed Data
  - FARO Server
  - Health Check Verified

🔧 Workarounds Applied:
  - Docker Desktop not running: Used manual extension installation
  - Citus compilation not available: Skipped Citus (graceful degradation)
  - Database already existed: Skipped database creation

⚠️  Components Skipped (Optional):
  - MinIO: Skipped - Using local storage fallback (default behavior)
  - TimescaleDB: Skipped - Docker not running, manual installation not completed
  - Citus: Skipped - Not available on Windows without Docker
  - PgBouncer: Skipped - Optional component
  - Prometheus: Skipped - Optional component

❌ Critical Issues:
  - None (system functional without optional components)

📝 Alternative Options for Manual Resolution:
  - To enable MinIO: Run `cd infra/docker && docker-compose up -d minio` and set S3_ENABLED=true
  - To enable TimescaleDB: Install Docker Desktop or download TimescaleDB for Windows
  - To enable Citus: Install Docker Desktop and run Citus container
  - To enable PgBouncer: Download PgBouncer for Windows and configure connection pooling
  - To enable Prometheus: Download Prometheus for Windows and configure monitoring

🎯 Installation Status: SUCCESS (Core system functional)
```

---

## Troubleshooting

### Common Issues

**Issue: "InvalidTextRepresentation" enum error during migration**
- **Solution:** Already fixed in migration 0006. Ensure you're using the corrected migrations.

**Issue: "CREATE INDEX CONCURRENTLY" error during migration**
- **Solution:** Already fixed in migration 0007. CONCURRENTLY removed.

**Issue: "ALTER SYSTEM" error during migration**
- **Solution:** Already fixed in migration 0008. ALTER SYSTEM commands removed.

**Issue: Permission denied when copying files to PostgreSQL directory**
- **Solution:** Run PowerShell as administrator.

**Issue: Docker Desktop fails to start (virtualization not detected)**
- **Solution:** Enable virtualization in BIOS or skip Docker components.

**Issue: PgBouncer connection refused**
- **Solution:** Ensure PgBouncer is running and listening on port 6432.

### Log Locations
- PostgreSQL logs: `C:\Program Files\PostgreSQL\16\data\log\`
- PgBouncer logs: Console output (can be redirected to file)
- Prometheus logs: Console output (can be redirected to file)

---

## Architecture Notes

### Database Schema
- **Tables:** 42 tables created by migrations
- **Extensions:** PostGIS installed and enabled
- **Indexes:** BRIN indexes for vehicle_observations (time-series optimization)
- **Enums:** 24 enums defined for type safety

### Connection Pooling
- **PgBouncer:** Transaction pooling mode
- **Pool Size:** 25 default, 10 reserve
- **Port:** 6432 (vs PostgreSQL 5432)

### Monitoring
- **Prometheus:** Metrics collection from server, PostgreSQL, Redis, PgBouncer
- **Port:** 9090
- **Scrape Interval:** 15s

---

## Production Deployment Notes

### Security
- **CRITICAL:** Change default passwords before production
- **CRITICAL:** Remove trust authentication from pg_hba.conf
- **CRITICAL:** Use SSL/TLS for all connections
- **CRITICAL:** Enable firewall rules
- **CRITICAL:** Use proper secrets management

### Performance
- **CRITICAL:** Configure PostgreSQL settings for production
- **CRITICAL:** Enable connection pooling (PgBouncer)
- **CRITICAL:** Set up proper monitoring and alerting
- **CRITICAL:** Configure backup strategy
- **CRITICAL:** Enable TimescaleDB for time-series data (if applicable)

### High Availability
- **CRITICAL:** Set up PostgreSQL replication
- **CRITICAL:** Configure load balancing
- **CRITICAL:** Implement failover strategy
- **CRITICAL:** Test disaster recovery procedures

---

## Support

For issues or questions:
1. Check this guide first
2. Review migration files in `server-core/alembic/versions/`
3. Check PostgreSQL logs
4. Check application logs
5. Consult project documentation in `docs/` directory

---

## Summary

**Minimum Required for Basic Operation:**
1. Python 3.12 LTS
2. PostgreSQL 16
3. PostGIS Extension
4. Database migrations (alembic)
5. Seed data
6. FARO Server startup (uvicorn)
7. Health check verification
8. Web interface verification

**Complete Installation and Verification (LLM/Human):**
1. Install Python 3.12 LTS
2. Install project dependencies
3. Install PostgreSQL 16
4. Configure PostgreSQL authentication (development)
5. Create database and user
6. Install PostGIS Extension
7. Configure Alembic connection string
8. Run database migrations
9. Create seed data
10. Install MinIO (OPTIONAL - system works with local storage fallback)
11. Start FARO Server
12. Verify server health check (HTTP 200, status: healthy)
13. Verify web interface (HTTP 200, page loads)
14. Verify mobile endpoints (HTTP 200, authentication working)

**Complete Installation and Verification (LLM/Human):**
1. Install Python 3.12 LTS
2. Install project dependencies
3. Install PostgreSQL 16
4. Configure PostgreSQL authentication (development)
5. Create database and user
6. Install PostGIS Extension
7. Configure Alembic connection string
8. Run database migrations
9. Create seed data
10. Start FARO Server
11. Verify server health check (HTTP 200, status: healthy)
12. Verify web interface (HTTP 200, page loads)
13. Verify mobile endpoints (HTTP 200, authentication working)

**Recommended for Production:**
1. All minimum requirements
2. PgBouncer (connection pooling)
3. Prometheus (monitoring)
4. TimescaleDB (time-series optimization)
5. Proper security configuration
6. Backup strategy

**Optional Advanced Features:**
1. Citus (horizontal scaling)
2. Materialized views (requires data)
3. Grafana (visualization)
4. Alertmanager (alerting)

---

**Last Updated:** 2026-04-17
**Tested On:** Windows 11, PostgreSQL 16, Python 3.12
