@echo off
REM ============================================================================
REM F.A.R.O. - Start All Services (Batch Script)
REM ============================================================================
REM Inicia todos os serviços do F.A.R.O. de forma coordenada.
REM Detecta automaticamente o diretório base.
REM
REM Uso: start_all.bat [skip-web] [skip-analytics]
REM   start_all.bat              - Inicia todos
REM   start_all.bat skip-web     - Inicia server + dashboard
REM   start_all.bat skip-analytics - Inicia server + web
REM ============================================================================

setlocal EnableDelayedExpansion

REM Detectar diretório base (onde este script está)
set "FARO_HOME=%~dp0"
set "FARO_HOME=%FARO_HOME:~0,-1%"

REM Cores (ANSI escape codes - funciona no Windows 10+)
set "CYAN=[96m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "RESET=[0m"

REM Parse arguments
set "SKIP_WEB=0"
set "SKIP_ANALYTICS=0"

:parse_args
if "%~1"=="" goto :done_args
if /I "%~1"=="skip-web" set "SKIP_WEB=1"
if /I "%~1"=="skip-analytics" set "SKIP_ANALYTICS=1"
shift
goto :parse_args
:done_args

echo.
echo %CYAN%========================================%RESET%
echo %CYAN%  F.A.R.O. - Iniciando Servicos%RESET%
echo %CYAN%========================================%RESET%
echo.

REM ============================================================================
REM Funcoes de Utilidade
REM ============================================================================

REM Verificar se porta esta disponivel
:check_port
set "PORT=%~1"
set "NAME=%~2"

netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo %YELLOW%  ⚠️  Porta %PORT% (%NAME%) esta em uso%RESET%
    set "PORT_BUSY=1"
) else (
    echo %GREEN%  ✅ Porta %PORT% (%NAME%) disponivel%RESET%
    set "PORT_BUSY=0"
)
goto :eof

REM ============================================================================
REM Verificar Portas
REM ============================================================================

echo %CYAN%1. Verificando portas disponiveis...%RESET%
set "CONFLICTS=0"

call :check_port 8000 "Server Core"
if !PORT_BUSY! equ 1 set /a CONFLICTS+=1

if %SKIP_ANALYTICS% equ 0 (
    call :check_port 9002 "Analytics Dashboard"
    if !PORT_BUSY! equ 1 set /a CONFLICTS+=1
)

if %SKIP_WEB% equ 0 (
    call :check_port 3000 "Web Console"
    if !PORT_BUSY! equ 1 set /a CONFLICTS+=1
)

if %CONFLICTS% gtr 0 (
    echo.
    echo %RED%  ❌ Portas em conflito detectadas: %CONFLICTS%%RESET%
    echo %YELLOW%     Verifique e encerre os processos manualmente%RESET%
    echo %YELLOW%     ou execute: .\stop-services.ps1%RESET%
    echo.
    pause
    exit /b 1
)

echo.
echo %GREEN%✅ Todas as portas disponiveis%RESET%
echo.

REM ============================================================================
REM Iniciar Servicos
REM ============================================================================

echo %CYAN%2. Iniciando servicos...%RESET%

REM Criar diretorio de logs se nao existir
if not exist "%FARO_HOME%\logs" mkdir "%FARO_HOME%\logs"

REM Server Core (sempre inicia)
echo %CYAN%   → Server Core (porta 8000)...%RESET%
start "FARO Server Core" cmd /c "cd /d "%FARO_HOME%\server-core" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 2^>"%FARO_HOME%\logs\server_core.log""
timeout /t 2 /nobreak >nul

REM Analytics Dashboard
if %SKIP_ANALYTICS% equ 0 (
    echo %CYAN%   → Analytics Dashboard (porta 9002)...%RESET%
    start "FARO Dashboard" cmd /c "cd /d "%FARO_HOME%\analytics-dashboard" && python -m app" 2^>"%FARO_HOME%\logs\dashboard.log""
    timeout /t 2 /nobreak >nul
)

REM Web Console
if %SKIP_WEB% equ 0 (
    echo %CYAN%   → Web Console (porta 3000)...%RESET%
    start "FARO Web Console" cmd /c "cd /d "%FARO_HOME%\web-intelligence-console" && npm run dev 2^>"%FARO_HOME%\logs\web_console.log""
    timeout /t 2 /nobreak >nul
)

REM ============================================================================
REM Resumo
REM ============================================================================

timeout /t 2 /nobreak >nul

echo.
echo %GREEN%========================================%RESET%
echo %GREEN%  ✅ SERVICOS INICIADOS%RESET%
echo %GREEN%========================================%RESET%
echo.
echo   Server Core:       %CYAN%http://127.0.0.1:8000%RESET%

if %SKIP_ANALYTICS% equ 0 (
    echo   Analytics Dashboard: %CYAN%http://localhost:9002/dashboard%RESET%
) else (
    echo   Analytics Dashboard: %YELLOW%[PULADO]%RESET%
)

if %SKIP_WEB% equ 0 (
    echo   Web Console:       %CYAN%http://localhost:3000%RESET%
) else (
    echo   Web Console:       %YELLOW%[PULADO]%RESET%
)

echo.
echo %YELLOW%Logs disponiveis em:%RESET%
echo   %FARO_HOME%\logs\
echo.
echo %YELLOW%Para encerrar, execute:%RESET%
echo   .\stop-services.ps1
echo   ou feche as janelas individuais
echo.

endlocal