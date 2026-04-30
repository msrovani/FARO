# F.A.R.O. - Script de Parada de Serviços
# Este script encerra todos os serviços do FARO
# Uso: .\stop-services.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  F.A.R.O. - Encerrando Serviços" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Função para matar processo por nome
function Stop-ProcessByName {
    param([string]$ProcessName, [string]$DisplayName)
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "  ⏳ Encerrando $DisplayName..." -ForegroundColor Yellow
        foreach ($process in $processes) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "    ✅ Processo encerrado (PID: $($process.Id))" -ForegroundColor Green
        }
    } else {
        Write-Host "  ℹ️  $DisplayName não está rodando" -ForegroundColor Cyan
    }
}

# ============================================================================
# Encerrar Serviços Python (Server Core, Analytics Dashboard)
# ============================================================================
Write-Host "1. Encerrando serviços Python..." -ForegroundColor Yellow
Stop-ProcessByName -ProcessName "uvicorn" -DisplayName "Server Core/Analytics Dashboard"
Stop-ProcessByName -ProcessName "python" -DisplayName "Python processes"

# ============================================================================
# Encerrar Serviços Node.js (Web Console)
# ============================================================================
Write-Host ""
Write-Host "2. Encerrando serviços Node.js..." -ForegroundColor Yellow
Stop-ProcessByName -ProcessName "node" -DisplayName "Web Intelligence Console"

# ============================================================================
# Encerrar Docker (opcional)
# ============================================================================
Write-Host ""
Write-Host "3. Verificando Docker containers..." -ForegroundColor Yellow

if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        $containers = docker ps --filter "name=faro" --format "{{.Names}}" 2>$null
        if ($containers) {
            Write-Host "  ⏳ Encerrando containers Docker FARO..." -ForegroundColor Yellow
            cd "$PSScriptRoot\infra\docker"
            docker compose -f docker-compose.dev.yml down
            Write-Host "  ✅ Docker containers encerrados" -ForegroundColor Green
        } else {
            Write-Host "  ℹ️  Nenhum container FARO rodando" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "  ⚠️  Erro ao encerrar Docker: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ℹ️  Docker não encontrado" -ForegroundColor Cyan
}

# ============================================================================
# Relatório Final
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Serviços Encerrados!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Todos os serviços do FARO foram encerrados." -ForegroundColor Green
Write-Host ""
Write-Host "Para reiniciar:" -ForegroundColor Yellow
Write-Host "  Execute: .\start-services.ps1" -ForegroundColor White
Write-Host ""
