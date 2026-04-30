# F.A.R.O. - Verificação de Instalação
# Este script verifica se todos os serviços estão UP e saudáveis
# Uso: .\verify-installation.ps1

param(
    [string]$PostgresPort = "5432",
    [string]$ServerPort = "8000",
    [string]$WebConsolePort = "3000",
    [string]$AnalyticsPort = "9002"
)

$ErrorActionPreference = "Stop"
$FARO_HOME = $PSScriptRoot

$allChecksPassed = $true

function Log-Check {
    param([string]$Message, [bool]$Passed)
    if ($Passed) {
        Write-Host "  ✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $Message" -ForegroundColor Red
        $script:allChecksPassed = $false
    }
}

function Log-Info {
    param([string]$Message)
    Write-Host "  ℹ️  $Message" -ForegroundColor Cyan
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  F.A.R.O. - Verificação de Instalação" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. Verificar PostgreSQL
# ============================================================================
Write-Host "1. Verificando PostgreSQL..." -ForegroundColor Yellow
$pgPath = "C:\Program Files\PostgreSQL\16\bin\psql.exe"

if (Test-Path $pgPath) {
    Log-Check "PostgreSQL 16 instalado" $true
    
    $pgService = Get-Service -Name "postgresql-x64-16" -ErrorAction SilentlyContinue
    if ($pgService -and $pgService.Status -eq "Running") {
        Log-Check "PostgreSQL service rodando" $true
    } else {
        Log-Check "PostgreSQL service rodando" $false
    }
    
    # Testar conexão
    try {
        & $pgPath -U postgres -d faro_db -c "SELECT 1;" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Log-Check "PostgreSQL connection funcionando" $true
        } else {
            Log-Check "PostgreSQL connection funcionando" $false
        }
    } catch {
        Log-Check "PostgreSQL connection funcionando" $false
    }
    
    # Verificar PostGIS
    try {
        $result = & $pgPath -U postgres -d faro_db -c "SELECT extname FROM pg_extension WHERE extname='postgis';" 2>$null
        if ($LASTEXITCODE -eq 0 -and $result -match "postgis") {
            Log-Check "PostGIS extension habilitada" $true
        } else {
            Log-Check "PostGIS extension habilitada" $false
        }
    } catch {
        Log-Check "PostGIS extension habilitada" $false
    }
} else {
    Log-Check "PostgreSQL 16 instalado" $false
}

# ============================================================================
# 2. Verificar Database Schema
# ============================================================================
Write-Host "2. Verificando Database Schema..." -ForegroundColor Yellow

try {
    $tableCount = & $pgPath -U postgres -d faro_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" -t 2>$null
    $tableCount = $tableCount.Trim()
    Log-Info "Tabelas encontradas: $($tableCount)"
    if ([int]$tableCount -ge 30) {
        Log-Check "Schema criado (30+ tabelas)" $true
    } else {
        Log-Check "Schema criado (30+ tabelas)" $false
    }
} catch {
    Log-Check "Schema criado" $false
}

# Verificar migrations
try {
    cd "$FARO_HOME\server-core"
    $currentVersion = alembic current 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log-Info "Versão atual: $currentVersion"
        Log-Check "Migrations aplicadas" $true
    } else {
        Log-Check "Migrations aplicadas" $false
    }
} catch {
    Log-Check "Migrations aplicadas" $false
}

# ============================================================================
# 3. Verificar Seed Data
# ============================================================================
Write-Host "3. Verificando Seed Data..." -ForegroundColor Yellow

try {
    $agencyCount = & $pgPath -U postgres -d faro_db -c "SELECT COUNT(*) FROM agency;" -t 2>$null
    $agencyCount = $agencyCount.Trim()
    Log-Info "Agências criadas: $agencyCount"
    if ([int]$agencyCount -ge 3) {
        Log-Check "Agências criadas (3+)" $true
    } else {
        Log-Check "Agências criadas (3+)" $false
    }
} catch {
    Log-Check "Agências criadas" $false
}

try {
    $userCount = & $pgPath -U postgres -d faro_db -c "SELECT COUNT(*) FROM ""user"";" -t 2>$null
    $userCount = $userCount.Trim()
    Log-Info "Usuários criados: $userCount"
    if ([int]$userCount -ge 3) {
        Log-Check "Usuários criados (3+)" $true
    } else {
        Log-Check "Usuários criados (3+)" $false
    }
} catch {
    Log-Check "Usuários criados" $false
}

# ============================================================================
# 4. Verificar Server Core
# ============================================================================
Write-Host "4. Verificando Server Core..." -ForegroundColor Yellow

# Testar porta
$portCheck = netstat -ano | findstr ":$ServerPort"
if ($portCheck) {
    Log-Check "Server Core rodando na porta $ServerPort" $true
} else {
    Log-Check "Server Core rodando na porta $ServerPort" $false
}

# Testar health endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort/health" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Log-Check "Server Core health check (HTTP 200)" $true
        
        $content = $response.Content | ConvertFrom-Json
        if ($content.status -eq "healthy") {
            Log-Check "Server Core status: healthy" $true
        } else {
            Log-Check "Server Core status: healthy" $false
        }
    } else {
        Log-Check "Server Core health check (HTTP 200)" $false
    }
} catch {
    Log-Check "Server Core health check" $false
}

# Testar root endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Log-Check "Server Core root endpoint (HTTP 200)" $true
    } else {
        Log-Check "Server Core root endpoint (HTTP 200)" $false
    }
} catch {
    Log-Check "Server Core root endpoint" $false
}

# Testar API docs
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort/docs" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Log-Check "Server Core API docs acessíveis" $true
    } else {
        Log-Check "Server Core API docs acessíveis" $false
    }
} catch {
    Log-Check "Server Core API docs acessíveis" $false
}

# ============================================================================
# 5. Verificar Web Intelligence Console
# ============================================================================
Write-Host "5. Verificando Web Intelligence Console..." -ForegroundColor Yellow

# Testar porta
$portCheck = netstat -ano | findstr ":$WebConsolePort"
if ($portCheck) {
    Log-Check "Web Console rodando na porta $WebConsolePort" $true
} else {
    Log-Check "Web Console rodando na porta $WebConsolePort" $false
}

# Testar endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$WebConsolePort" -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Log-Check "Web Console acessível (HTTP 200)" $true
    } else {
        Log-Check "Web Console acessível (HTTP 200)" $false
    }
} catch {
    Log-Check "Web Console acessível" $false
}

# ============================================================================
# 6. Verificar Analytics Dashboard
# ============================================================================
Write-Host "6. Verificando Analytics Dashboard..." -ForegroundColor Yellow

# Verificar se directory foi renomeado
if (Test-Path "$FARO_HOME\server-core\analytics_dashboard") {
    Log-Check "Analytics dashboard directory renomeado" $true
} elseif (Test-Path "$FARO_HOME\server-core\analytics-dashboard") {
    Log-Check "Analytics dashboard directory renomeado" $false
    Log-Info "  Directory ainda usa hífen (analytics-dashboard)"
} else {
    Log-Info "Analytics dashboard não encontrado (opcional)"
}

# Testar porta
$portCheck = netstat -ano | findstr ":$AnalyticsPort"
if ($portCheck) {
    Log-Check "Analytics Dashboard rodando na porta $AnalyticsPort" $true
} else {
    Log-Check "Analytics Dashboard rodando na porta $AnalyticsPort" $false
}

# Testar endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$AnalyticsPort/api/v1/health" -Method Get -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Log-Check "Analytics Dashboard health check (HTTP 200)" $true
    } else {
        Log-Check "Analytics Dashboard health check (HTTP 200)" $false
    }
} catch {
    Log-Check "Analytics Dashboard health check" $false
}

# ============================================================================
# 7. Verificar Login
# ============================================================================
Write-Host "7. Verificando Autenticação..." -ForegroundColor Yellow

try {
    $body = @{
        email = "admin@faro.pol"
        password = "password"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "http://localhost:$ServerPort/api/v1/auth/login" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Log-Check "Login funcionando (admin@faro.pol)" $true
        
        $content = $response.Content | ConvertFrom-Json
        if ($content.access_token) {
            Log-Check "Access token gerado" $true
        } else {
            Log-Check "Access token gerado" $false
        }
    } else {
        Log-Check "Login funcionando" $false
    }
} catch {
    Log-Check "Login funcionando" $false
}

# ============================================================================
# Relatório Final
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allChecksPassed) {
    Write-Host "  ✅ TODAS AS VERIFICAÇÕES PASSARAM!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Sistema FARO está pronto para uso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Acesso:" -ForegroundColor Yellow
    Write-Host "  - Server Core:           http://localhost:$ServerPort" -ForegroundColor White
    Write-Host "  - API Docs:              http://localhost:$ServerPort/docs" -ForegroundColor White
    Write-Host "  - Web Intelligence Console: http://localhost:$WebConsolePort" -ForegroundColor White
    Write-Host "  - Analytics Dashboard:   http://localhost:$AnalyticsPort/dashboard" -ForegroundColor White
    Write-Host ""
    Write-Host "Login:" -ForegroundColor Yellow
    Write-Host "  Email: admin@faro.pol" -ForegroundColor White
    Write-Host "  Password: password" -ForegroundColor White
} else {
    Write-Host "  ❌ ALGUMAS VERIFICAÇÕES FALHARAM" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Revise os itens marcados com ❌ acima." -ForegroundColor Red
    Write-Host ""
    Write-Host "Soluções comuns:" -ForegroundColor Yellow
    Write-Host "  - Se PostgreSQL não rodar: Start-Service postgresql-x64-16" -ForegroundColor White
    Write-Host "  - Se Server Core não responder: Iniciar com uvicorn app.main:app --reload" -ForegroundColor White
    Write-Host "  - Se Web Console não responder: cd web-intelligence-console && npm run dev" -ForegroundColor White
    Write-Host "  - Se Analytics não responder: Renomear analytics-dashboard -> analytics_dashboard" -ForegroundColor White
}
Write-Host ""

exit $(if ($allChecksPassed) { 0 } else { 1 })
