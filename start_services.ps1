# F.A.R.O. - Start Services (Unified Script)
# ======================================
# Inicia todos os serviços do F.A.R.O. com as melhores práticas
# Unifica funcionalidades de start-services.ps1 e start_services.ps1
#
# Uso: .\start_services_unified.ps1 [-SkipWeb] [-SkipAnalytics] [-SkipPostgres] [-Port <port>]
#   .\start_services_unified.ps1              # Inicia todos
#   .\start_services_unified.ps1 -SkipWeb     # Inicia server + dashboard
#   .\start_services_unified.ps1 -SkipAnalytics  # Inicia server + web
#   .\start_services_unified.ps1 -Port 8001     # Server na porta 8001
#   .\start_services_unified.ps1 -SkipPostgres # Não verifica PostgreSQL

param(
    [switch]$SkipWeb = $false,
    [switch]$SkipAnalytics = $false,
    [switch]$SkipPostgres = $false,
    [string]$ServerPort = "8000",
    [string]$WebConsolePort = "3000",
    [string]$AnalyticsPort = "9002"
)

$ErrorActionPreference = "Stop"

# Detectar diretório base automaticamente
$FARO_HOME = Split-Path -Parent $PSScriptRoot
if (-not $FARO_HOME) {
    $FARO_HOME = (Get-Location).Path
}

# Detectar Python do PATH
$python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $python) {
    $python = (Get-Command py -ErrorAction SilentlyContinue)?.Source
}
if (-not $python) {
    Write-Host "❌ Python não encontrado no PATH" -ForegroundColor Red
    exit 1
}

# Diretórios
$serverDir = Join-Path $FARO_HOME "server-core"
$webDir = Join-Path $FARO_HOME "web-intelligence-console"
$dashboardDir = Join-Path $FARO_HOME "analytics-dashboard"

# Criar diretório de logs
$logsDir = Join-Path $FARO_HOME "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

# Header
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  F.A.R.O. - Iniciando Serviços (Unified)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Funcoes de utilidade
function Test-Port {
    param([int]$Port)
    $connection = netstat -ano | findstr ":$Port" | findstr "LISTENING"
    return ($null -eq $connection)
}

function Test-PostgresService {
    param([int]$Port = 5432)
    try {
        $result = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        return $result
    } catch {
        return $false
    }
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDir,
        [string]$LogFile,
        [int]$Port
    )
    
    Write-Host "  → Iniciando $Name (porta $Port)..." -ForegroundColor Cyan
    
    try {
        $proc = Start-Process powershell -ArgumentList "-NoProfile", "-Command", "Set-Location '$WorkingDir'; $Command 2>'$LogFile'" -PassThru -WindowStyle Minimized
        Write-Host "    ✅ $Name iniciado (PID: $($proc.Id))" -ForegroundColor Green
        return $proc
    } catch {
        Write-Host "    ❌ Falha ao iniciar $Name : $_" -ForegroundColor Red
        return $null
    }
}

# ============================================================================
# 1. Verificar PostgreSQL (se não pulado)
# ============================================================================
if (-not $SkipPostgres) {
    Write-Host "1. Verificando PostgreSQL..." -ForegroundColor Yellow
    
    if (Test-PostgresService -Port 5432) {
        Write-Host "  ✅ PostgreSQL está rodando na porta 5432" -ForegroundColor Green
    } else {
        Write-Host "  ❌ PostgreSQL não está rodando na porta 5432" -ForegroundColor Red
        Write-Host "     Inicie o PostgreSQL ou use -SkipPostgres" -ForegroundColor Yellow
        exit 1
    }
}

# ============================================================================
# 2. Verificar portas disponíveis
# ============================================================================
Write-Host ""
Write-Host "2. Verificando portas disponíveis..." -ForegroundColor Yellow

$portsToCheck = @(
    @{ Port = [int]$ServerPort; Name = "Server Core"; Required = $true }
)

if (-not $SkipAnalytics) {
    $portsToCheck += @{ Port = [int]$AnalyticsPort; Name = "Analytics Dashboard"; Required = $false }
}

if (-not $SkipWeb) {
    $portsToCheck += @{ Port = [int]$WebConsolePort; Name = "Web Console"; Required = $false }
}

$conflicts = @()
foreach ($portInfo in $portsToCheck) {
    if (-not (Test-Port -Port $portInfo.Port)) {
        Write-Host "    ⚠️  Porta $($portInfo.Port) ($($portInfo.Name)) está em uso" -ForegroundColor Yellow
        if ($portInfo.Required) {
            $conflicts += $portInfo
        }
    } else {
        Write-Host "    ✅ Porta $($portInfo.Port) ($($portInfo.Name)) disponível" -ForegroundColor Green
    }
}

if ($conflicts.Count -gt 0) {
    Write-Host ""
    Write-Host "  ❌ Portas obrigatórias em conflito detectadas" -ForegroundColor Red
    Write-Host "     Execute .\stop-services.ps1 primeiro" -ForegroundColor Yellow
    Write-Host "     Ou use -Port para especificar outra porta" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "  ✅ Todas as portas necessárias disponíveis" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 3. Verificar Analytics Dashboard
# ============================================================================
if (-not $SkipAnalytics) {
    Write-Host "3. Verificando Analytics Dashboard..." -ForegroundColor Yellow
    
    if (Test-Path "$dashboardDir\app.py") {
        Write-Host "  ✅ Analytics Dashboard encontrado em $dashboardDir" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Analytics Dashboard não encontrado em $dashboardDir" -ForegroundColor Yellow
        Write-Host "     Pulando Analytics Dashboard..." -ForegroundColor Yellow
        $SkipAnalytics = $true
    }
}

# ============================================================================
# 4. Iniciar serviços
# ============================================================================
Write-Host ""
Write-Host "4. Iniciando serviços..." -ForegroundColor Yellow

$processes = @()

# Server Core (sempre inicia)
Write-Host ""
Write-Host "  Server Core:" -ForegroundColor Cyan
$serverLog = Join-Path $logsDir "server_core.log"
$serverProc = Start-ServiceProcess -Name "Server Core" -Command "$python -m uvicorn app.main:app --host 127.0.0.1 --port $ServerPort" -WorkingDir $serverDir -LogFile $serverLog -Port $ServerPort
if ($serverProc) { $processes += @{ Name = "Server Core"; Process = $serverProc; Port = $ServerPort } }

Start-Sleep -Seconds 2

# Analytics Dashboard
if (-not $SkipAnalytics) {
    Write-Host ""
    Write-Host "  Analytics Dashboard:" -ForegroundColor Cyan
    $dashLog = Join-Path $logsDir "dashboard.log"
    $dashProc = Start-ServiceProcess -Name "Analytics Dashboard" -Command "$python app.py" -WorkingDir $dashboardDir -LogFile $dashLog -Port $AnalyticsPort
    if ($dashProc) { $processes += @{ Name = "Analytics Dashboard"; Process = $dashProc; Port = $AnalyticsPort } }
    Start-Sleep -Seconds 2
}

# Web Console
if (-not $SkipWeb) {
    Write-Host ""
    Write-Host "  Web Console:" -ForegroundColor Cyan
    $webLog = Join-Path $logsDir "web_console.log"
    $webProc = Start-ServiceProcess -Name "Web Console" -Command "npm run dev" -WorkingDir $webDir -LogFile $webLog -Port $WebConsolePort
    if ($webProc) { $processes += @{ Name = "Web Console"; Process = $webProc; Port = $WebConsolePort } }
}

# ============================================================================
# 5. Resumo
# ============================================================================
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ SERVIÇOS INICIADOS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

foreach ($procInfo in $processes) {
    Write-Host "  $($procInfo.Name):" -ForegroundColor Green
    switch ($procInfo.Port) {
        8000 { Write-Host "    http://127.0.0.1:8000" -ForegroundColor Cyan }
        8001 { Write-Host "    http://127.0.0.1:8001" -ForegroundColor Cyan }
        9002 { Write-Host "    http://localhost:9002/dashboard" -ForegroundColor Cyan }
        3000 { Write-Host "    http://localhost:3000" -ForegroundColor Cyan }
        default { 
            if ($procInfo.Port -ge 8000 -and $procInfo.Port -lt 9000) {
                Write-Host "    http://127.0.0.1:$($procInfo.Port)" -ForegroundColor Cyan 
            } else {
                Write-Host "    http://localhost:$($procInfo.Port)" -ForegroundColor Cyan 
            }
        }
    }
    Write-Host "    PID: $($procInfo.Process.Id)" -ForegroundColor Gray
}

if ($SkipPostgres) {
    Write-Host "  PostgreSQL: [PULADO]" -ForegroundColor Yellow
}
if ($SkipAnalytics) {
    Write-Host "  Analytics Dashboard: [PULADO]" -ForegroundColor Yellow
}
if ($SkipWeb) {
    Write-Host "  Web Console: [PULADO]" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Logs disponíveis em:" -ForegroundColor Yellow
Write-Host "  $logsDir" -ForegroundColor Gray
Write-Host ""
Write-Host "Para encerrar, execute:" -ForegroundColor Yellow
Write-Host "  .\stop-services.ps1" -ForegroundColor Gray
Write-Host ""

# Exportar PIDs para arquivo (útil para o stop script)
$pidsFile = Join-Path $FARO_HOME ".faro_pids"
$processes | ForEach-Object { $_.Process.Id } | Out-File -FilePath $pidsFile -Encoding UTF8

Write-Host "Pressione Ctrl+C para encerrar todos os serviços..." -ForegroundColor Yellow
try {
    # Manter script rodando para poder encerrar com Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch [System.Management.Automation.HaltCommandException] {
    Write-Host ""
    Write-Host "Encerrando serviços..." -ForegroundColor Yellow
    foreach ($procInfo in $processes) {
        try {
            Stop-Process -Id $procInfo.Process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  ✅ $($procInfo.Name) encerrado" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  $($procInfo.Name) já estava encerrado" -ForegroundColor Yellow
        }
    }
    # Limpar arquivo de PIDs
    if (Test-Path $pidsFile) {
        Remove-Item $pidsFile -Force
    }
    Write-Host "Todos os serviços encerrados." -ForegroundColor Green
}
