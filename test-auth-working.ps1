# F.A.R.O. - Teste de Autenticação

Write-Host "Testando autenticação F.A.R.O." -ForegroundColor Green

# Criar body JSON
$body = @{
    identifier = "admin@faro.pol"
    password = "password"
}

Write-Host "Enviando requisição de login..." -ForegroundColor Cyan

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body ($body | ConvertTo-Json) -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "Login successful!" -ForegroundColor Green
        
        $tokenData = $response.Content | ConvertFrom-Json
        Write-Host "Access Token:" -ForegroundColor Yellow
        Write-Host $tokenData.access_token -ForegroundColor White
        Write-Host "Refresh Token:" -ForegroundColor Yellow
        Write-Host $tokenData.refresh_token -ForegroundColor White
        Write-Host ""
        Write-Host "Para testar endpoints protegidos:" -ForegroundColor Cyan
        Write-Host "curl -H 'Authorization: Bearer $($tokenData.access_token)' http://localhost:8000/api/v1/intelligence/queue" -ForegroundColor Gray
        
        $env:FARO_TOKEN = $tokenData.access_token
        Write-Host "Token salvo em variável de ambiente" -ForegroundColor Green
        
    } else {
        Write-Host "Login failed!" -ForegroundColor Red
        Write-Host "Status Code:" $response.StatusCode -ForegroundColor Red
        Write-Host "Response:" $response.Content -ForegroundColor Red
    }
} catch {
    Write-Host "Erro ao conectar com o servidor:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Verificando status do backend..." -ForegroundColor Cyan

try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "Backend está online!" -ForegroundColor Green
    } else {
        Write-Host "Backend offline!" -ForegroundColor Red
    }
} catch {
    Write-Host "Erro ao verificar saúde do backend:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
