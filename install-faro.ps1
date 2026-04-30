# F.A.R.O. - Instalação Automatizada por IA
# Este script realiza a instalação completa do FARO sem intervenção manual
# Uso: .\install-faro.ps1

param(
    [switch]$SkipDocker = $false,
    [switch]$SkipWebConsole = $false,
    [switch]$SkipAnalytics = $false,
    [string]$PostgresPort = "5432",
    [string]$ServerPort = "8000",
    [string]$WebConsolePort = "3000",
    [string]$AnalyticsPort = "9002"
)

$ErrorActionPreference = "Stop"
$FARO_HOME = $PSScriptRoot
$env:FARO_HOME = $FARO_HOME

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  F.A.R.O. - Instalação Automatizada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Função de log
function Log-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor Green
}

function Log-Error {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ $Message" -ForegroundColor Red
}

function Log-Warning {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  $Message" -ForegroundColor Yellow
}

function Log-Success {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ $Message" -ForegroundColor Green
}

# Função para verificar se comando existe
function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Função para verificar porta disponível
function Test-Port {
    param([string]$Port)
    $connection = netstat -ano | findstr ":$Port"
    return ($null -eq $connection)
}

# Função para matar processo em porta específica
function Kill-PortProcess {
    param([string]$Port)
    $process = netstat -ano | findstr ":$port" | Select-String "LISTENING"
    if ($process) {
        $pid = ($process -split '\s+')[-1]
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Log-Warning "Processo na porta $port terminado (PID: $pid)"
    }
}

# ============================================================================
# PASSO 1: Verificar Pré-Requisitos
# ============================================================================
Log-Step "Passo 1/10: Verificando pré-requisitos..."

# Verificar Git
if (-not (Test-Command "git")) {
    Log-Error "Git não encontrado. Instale Git em https://git-scm.com/"
    exit 1
}
Log-Success "Git encontrado"

# Verificar Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Log-Error "Python não encontrado. Instale Python 3.12 LTS em https://www.python.org/"
    exit 1
}
if ($pythonVersion -notmatch "3\.12\.") {
    Log-Warning "Python versão $pythonVersion (recomendado: 3.12.x)"
} else {
    Log-Success "Python $pythonVersion encontrado"
}

# Verificar pip
if (-not (Test-Command "pip")) {
    Log-Error "pip não encontrado"
    exit 1
}
Log-Success "pip encontrado"

# Verificar PostgreSQL
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"
if (-not (Test-Path $pgPath)) {
    Log-Error "PostgreSQL 16 não encontrado em $pgPath"
    Log-Error "Instale PostgreSQL 16 em https://www.postgresql.org/download/windows/"
    exit 1
}
Log-Success "PostgreSQL 16 encontrado"

# Verificar Node.js (para Web Console)
if (-not $SkipWebConsole) {
    if (-not (Test-Command "node")) {
        Log-Error "Node.js não encontrado. Instale Node.js 18.x+ em https://nodejs.org/"
        exit 1
    }
    $nodeVersion = node --version
    if ($nodeVersion -notmatch "v1[8-9]\.|v2[0-9]\.") {
        Log-Warning "Node.js versão $nodeVersion (recomendado: 18.x+)"
    } else {
        Log-Success "Node.js $nodeVersion encontrado"
    }
    
    if (-not (Test-Command "npm")) {
        Log-Error "npm não encontrado"
        exit 1
    }
    Log-Success "npm encontrado"
}

# Verificar Docker (opcional)
if (-not $SkipDocker) {
    if (Test-Command "docker") {
        $dockerVersion = docker --version
        Log-Success "Docker encontrado: $dockerVersion"
        try {
            $null = docker ps 2>&1
            if ($LASTEXITCODE -eq 0) {
                Log-Success "Docker Desktop está rodando"
            } else {
                Log-Warning "Docker Desktop não está rodando"
            }
        } catch {
            Log-Warning "Docker Desktop não está rodando"
        }
    } else {
        Log-Warning "Docker não encontrado (opcional - usando PostgreSQL manual)"
        $SkipDocker = $true
    }
}

# ============================================================================
# PASSO 2: Verificar Portas Disponíveis
# ============================================================================
Log-Step "Passo 2/10: Verificando portas disponíveis..."

$ports = @{
    "PostgreSQL" = $PostgresPort
    "Server Core" = $ServerPort
    "Web Console" = $WebConsolePort
    "Analytics Dashboard" = $AnalyticsPort
}

$portConflicts = @()
foreach ($name in $ports.Keys) {
    $port = $ports[$name]
    if (-not (Test-Port $port)) {
        Log-Warning "Porta $port ($name) já está em uso"
        $portConflicts += $name
    } else {
        Log-Success "Porta $port ($name) disponível"
    }
}

if ($portConflicts.Count -gt 0) {
    Log-Error "Portas em conflito: $($portConflicts -join ', ')"
    Log-Error "Encerre os processos ou use parâmetros para especificar portas alternativas"
    exit 1
}

# ============================================================================
# PASSO 3: Instalar Dependências Python
# ============================================================================
Log-Step "Passo 3/10: Instalando dependências Python..."

cd "$FARO_HOME\server-core"
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Dependências Python instaladas"
    } else {
        Log-Error "Falha ao instalar dependências Python"
        exit 1
    }
} else {
    Log-Error "requirements.txt não encontrado"
    exit 1
}

# ============================================================================
# PASSO 4: Verificar PostgreSQL Service
# ============================================================================
Log-Step "Passo 4/10: Verificando PostgreSQL service..."

$pgService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
if ($pgService) {
    if ($pgService.Status -ne "Running") {
        Log-Warning "PostgreSQL service não está rodando, iniciando..."
        Start-Service postgresql-x64-16
        Start-Sleep -Seconds 5
        $pgService.Refresh()
        if ($pgService.Status -eq "Running") {
            Log-Success "PostgreSQL service iniciado"
        } else {
            Log-Error "Falha ao iniciar PostgreSQL service"
            exit 1
        }
    } else {
        Log-Success "PostgreSQL service rodando"
    }
} else {
    Log-Error "PostgreSQL service não encontrado"
    exit 1
}

# ============================================================================
# PASSO 5: Configurar PostgreSQL Authentication (Development)
# ============================================================================
Log-Step "Passo 5/10: Configurando PostgreSQL authentication..."

$pg_hba = "C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
if (Test-Path $pg_hba) {
    $content = Get-Content $pg_hba
    $hasTrust = $content -match "trust"
    if (-not $hasTrust) {
        Log-Warning "Configurando trust authentication (development only)..."
        (Get-Content $pg_hba) -replace 'scram-sha-256', 'trust' | Set-Content $pg_hba
        Restart-Service postgresql-x64-16
        Start-Sleep -Seconds 5
        Log-Success "PostgreSQL authentication configurado"
    } else {
        Log-Success "PostgreSQL authentication já configurado"
    }
} else {
    Log-Error "pg_hba.conf não encontrado"
    exit 1
}

# ============================================================================
# PASSO 6: Criar Database e User
# ============================================================================
Log-Step "Passo 6/10: Criando database e user..."

& $pgPath -U postgres -c "SELECT 1 FROM pg_database WHERE datname='faro_db';" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Log-Success "Database faro_db já existe"
} else {
    Log-Warning "Criando database faro_db..."
    & $pgPath -U postgres -c "CREATE DATABASE faro_db;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "Database faro_db criado"
    } else {
        Log-Error "Falha ao criar database"
        exit 1
    }
}

& $pgPath -U postgres -c "SELECT 1 FROM pg_user WHERE usename='faro';" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Log-Success "User faro já existe"
} else {
    Log-Warning "Criando user faro..."
    & $pgPath -U postgres -c "CREATE USER faro WITH PASSWORD 'faro';" 2>$null
    & $pgPath -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE faro_db TO faro;" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Log-Success "User faro criado"
    } else {
        Log-Error "Falha ao criar user"
        exit 1
    }
}

# ============================================================================
# PASSO 7: Habilitar PostGIS
# ============================================================================
Log-Step "Passo 7/10: Habilitando PostGIS extension..."

& $pgPath -U postgres -d faro_db -c "CREATE EXTENSION IF NOT EXISTS postgis;" 2>$null
if ($LASTEXITCODE -eq 0) {
    Log-Success "PostGIS extension habilitada"
} else {
    Log-Error "Falha ao habilitar PostGIS"
    exit 1
}

# ============================================================================
# PASSO 8: Executar Migrations
# ============================================================================
Log-Step "Passo 8/10: Executando database migrations..."

cd "$FARO_HOME\server-core"
alembic upgrade head
if ($LASTEXITCODE -eq 0) {
    Log-Success "Migrations executadas com sucesso"
} else {
    Log-Error "Falha ao executar migrations"
    exit 1
}

# ============================================================================
# PASSO 9: Criar Seed Data
# ============================================================================
Log-Step "Passo 9/10: Criando seed data..."

cd "$FARO_HOME\database\seeds"
python seed_data.py
if ($LASTEXITCODE -eq 0) {
    Log-Success "Seed data criada com sucesso"
} else {
    Log-Warning "Seed data pode já existir ou houve erro (continuando...)"
}

# ============================================================================
# PASSO 10: Iniciar Serviços
# ============================================================================
Log-Step "Passo 10/10: Iniciando serviços..."

# Iniciar Server Core
Log-Warning "Iniciando Server Core (porta $ServerPort)..."
$serverProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\server-core'; uvicorn app.main:app --host 0.0.0.0 --port $ServerPort --reload" -PassThru -WindowStyle Minimized
Start-Sleep -Seconds 5

# Verificar Server Core
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort/health" -Method Get -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Log-Success "Server Core rodando em http://localhost:$ServerPort"
    } else {
        Log-Error "Server Core não respondeu corretamente"
    }
} catch {
    Log-Error "Server Core não respondeu: $_"
}

# Iniciar Web Console (se não skip)
if (-not $SkipWebConsole) {
    Log-Warning "Iniciando Web Intelligence Console (porta $WebConsolePort)..."
    $consoleProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\web-intelligence-console'; npm run dev" -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$WebConsolePort" -Method Get -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Log-Success "Web Intelligence Console rodando em http://localhost:$WebConsolePort"
        } else {
            Log-Error "Web Intelligence Console não respondeu corretamente"
        }
    } catch {
        Log-Error "Web Intelligence Console não respondeu: $_"
    }
}

# Iniciar Analytics Dashboard (se não skip)
if (-not $SkipAnalytics) {
    # Renomear directory se necessário
    if (Test-Path "$FARO_HOME\server-core\analytics-dashboard") {
        Log-Warning "Renomeando analytics-dashboard -> analytics_dashboard..."
        Rename-Item -Path "$FARO_HOME\server-core\analytics-dashboard" -NewName "analytics_dashboard" -Force
    }
    
    # Instalar dependências do analytics dashboard
    if (Test-Path "$FARO_HOME\server-core\analytics_dashboard\requirements.txt") {
        cd "$FARO_HOME\server-core\analytics_dashboard"
        pip install -r requirements.txt
    }
    
    Log-Warning "Iniciando Analytics Dashboard (porta $AnalyticsPort)..."
    $dashboardProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FARO_HOME\server-core'; uvicorn analytics_dashboard.app:app --host 0.0.0.0 --port $AnalyticsPort --reload" -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 5
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$AnalyticsPort/api/v1/health" -Method Get -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Log-Success "Analytics Dashboard rodando em http://localhost:$AnalyticsPort"
        } else {
            Log-Error "Analytics Dashboard não respondeu corretamente"
        }
    } catch {
        Log-Error "Analytics Dashboard não respondeu: $_"
    }
}

# ============================================================================
# Relatório Final
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Instalação Concluída!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Serviços Ativos:" -ForegroundColor Green
Write-Host "  - Server Core:           http://localhost:$ServerPort" -ForegroundColor White
Write-Host "  - API Documentation:     http://localhost:$ServerPort/docs" -ForegroundColor White
if (-not $SkipWebConsole) {
    Write-Host "  - Web Intelligence Console: http://localhost:$WebConsolePort" -ForegroundColor White
}
if (-not $SkipAnalytics) {
    Write-Host "  - Analytics Dashboard:   http://localhost:$AnalyticsPort/dashboard" -ForegroundColor White
}
Write-Host ""
Write-Host "Credenciais de Login:" -ForegroundColor Yellow
Write-Host "  Email: admin@faro.pol" -ForegroundColor White
Write-Host "  Password: password" -ForegroundColor White
Write-Host ""
Write-Host "Para encerrar os serviços:" -ForegroundColor Yellow
Write-Host "  1. Feche as janelas do PowerShell abertas" -ForegroundColor White
Write-Host "  2. Ou execute: .\stop-services.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Para verificação completa:" -ForegroundColor Yellow
Write-Host "  Execute: .\verify-installation.ps1" -ForegroundColor White
Write-Host ""
