# F.A.R.O. - Script para iniciar infraestrutura essencial
# Uso: .\start-infrastructure.ps1

Write-Host "Iniciando infraestrutura essencial F.A.R.O..." -ForegroundColor Green

# Verificar se Docker está instalado
try {
    docker --version >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker não encontrado. Instale Docker Desktop primeiro." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Docker encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Erro ao verificar Docker: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Ir para o diretório do Docker Compose
Set-Location $PSScriptRoot\infra\docker

# Iniciar PostgreSQL e Redis
Write-Host "🚀 Iniciando PostgreSQL e Redis..." -ForegroundColor Yellow

try {
    # Iniciar os containers
    docker compose up -d postgres redis
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL e Redis iniciados com sucesso!" -ForegroundColor Green
        
        # Verificar status dos containers
        Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
        docker compose ps postgres redis
        
        # Informações de conexão
        Write-Host ""
        Write-Host "🔗 Informações de conexão:" -ForegroundColor Cyan
        Write-Host "   PostgreSQL: localhost:5432" -ForegroundColor White
        Write-Host "   Redis: localhost:6379" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 Para conectar ao PostgreSQL:" -ForegroundColor Yellow
        Write-Host "   psql -h localhost -p 5432 -U faro -d faro_db" -ForegroundColor Gray
        Write-Host ""
        Write-Host "💡 Para conectar ao Redis:" -ForegroundColor Yellow
        Write-Host "   redis-cli -h localhost -p 6379" -ForegroundColor Gray
        Write-Host ""
        
    } else {
        Write-Host "❌ Falha ao iniciar containers" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erro ao iniciar containers: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Infraestrutura essencial pronta!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Iniciar o backend F.A.R.O. (porta 8000)" -ForegroundColor White
Write-Host "2. Iniciar o frontend (porta 3000)" -ForegroundColor White
Write-Host "3. Acessar http://localhost:3000" -ForegroundColor White
