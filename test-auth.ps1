# F.A.R.O. - Teste de Autenticação
# Script para testar login e obter token JWT

Write-Host "🔐 Testando autenticação F.A.R.O. ..." -ForegroundColor Green

# Dados de teste
$loginData = @{
    identifier = "admin@faro.pol"
    password = "password"
} | ConvertTo-Json

Write-Host "📤 Enviando requisição para: http://localhost:8000/api/v1/auth/login" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginData `
        -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Login successful!" -ForegroundColor Green
        
        $tokenData = $response.Content | ConvertFrom-Json
        Write-Host "🎫 Access Token:" -ForegroundColor Yellow
        Write-Host $tokenData.access_token -ForegroundColor White
        Write-Host ""
        Write-Host "🔄 Refresh Token:" -ForegroundColor Yellow
        Write-Host $tokenData.refresh_token -ForegroundColor White
        Write-Host ""
        Write-Host "💡 Para testar endpoints protegidos:" -ForegroundColor Cyan
        Write-Host "curl -H 'Authorization: Bearer $($tokenData.access_token)' http://localhost:8000/api/v1/intelligence/queue" -ForegroundColor Gray
        Write-Host ""
        
        # Salvar token em variável de ambiente
        $env:FARO_TOKEN = $tokenData.access_token
        Write-Host "✅ Token salvo em `$env:FARO_TOKEN`" -ForegroundColor Green
        
    } else {
        Write-Host "❌ Login failed!" -ForegroundColor Red
        Write-Host "Status Code:" $response.StatusCode -ForegroundColor Red
        Write-Host "Response:" $response.Content -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erro ao conectar com o servidor:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "🔍 Verificando status do backend..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ Backend está online!" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend offline!" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erro ao verificar saúde do backend:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
