# F.A.R.O. - OpenMemory Guide

**Project ID:** FARO  
**Last Updated:** 2026-04-28  
**Version:** 1.0.0

---

## Overview

F.A.R.O. (Ferramenta de Análise de Rotas e Observações) é uma plataforma de inteligência policial que transforma registros de campo em decisões de inteligência com retorno ao próprio agente, em um ciclo fechado.

### Objetivo Operacional
1. Campo registra
2. Backend valida e enriquece
3. Inteligência reanalisa e decide
4. Backend devolve feedback
5. Campo recebe e aplica no próximo contato

### Stack Tecnológico Principal
- **Backend:** FastAPI 0.115.0 (Python 3.11) + SQLAlchemy 2.0.36 (async)
- **Database:** PostgreSQL 16 + PostGIS 3.4 + TimescaleDB + Citus
- **Cache/Queue:** Redis 7 (3 bancos separados)
- **Storage:** MinIO (S3-compatible) com fallback local
- **Mobile:** Android (Kotlin/Java)
- **Web:** Next.js 15 + React 18 + TypeScript
- **ML/OCR:** PyTorch 2.5.0 + YOLO 8.3.0 + EasyOCR 1.7.1
- **Observability:** OpenTelemetry + Prometheus + Grafana + Jaeger + Sentry

---

## Architecture

### Arquitetura Geral
**Modular Monolith** com fronteiras claras para extração futura em microserviços. Padrão async/IO-first com otimizações para performance.

### Componentes Principais

#### 1. Server Core (Backend)
- **Localização:** `server-core/`
- **Framework:** FastAPI com Uvicorn
- **Porta:** 8000
- **Responsabilidades:**
  - Auth JWT com refresh tokens
  - API REST versionada (`/api/v1/`)
  - Processamento de observações e suspeições
  - Algoritmos de inteligência (rotas, hotspots, convoy, roaming)
  - Eventos via Redis Streams
  - Auditoria e storage
  - OCR server-side

#### 2. Mobile Agent Field (APK)
- **Localização:** `mobile-agent-field/`
- **Framework:** Android nativo (Kotlin/Java)
- **Responsabilidades:**
  - Captura rápida de placas e contexto
  - OCR assistido
  - Operação offline com sync
  - Multi-perfil para dispositivo compartilhado
  - Upload de assets (imagem/audio)

#### 3. Web Intelligence Console
- **Localização:** `web-intelligence-console/`
- **Framework:** Next.js 15 + React 18 + TypeScript
- **Porta:** 3000
- **Responsabilidades:**
  - Dashboard de inteligência
  - Fila analítica com revisão estruturada
  - Watchlist, casos, rotas suspeitas
  - Hotspots de criminalidade com mapas
  - Previsão de rotas
  - Alertas e eventos (convoy, roaming)
  - Auditoria e feedback

#### 4. Analytics Dashboard
- **Localização:** `analytics-dashboard/` (raiz do projeto)
- **Framework:** FastAPI (standalone)
- **Porta:** 9002
- **Responsabilidades:**
  - Dashboard analítico em tempo real
  - 8 abas: Overview, Alerts, Database, Circuit Breakers, Usabilidade, Analytics, Auditoria, Histórico Alertas
  - Métricas HTTP, DB, Cache, Alerts, PgBouncer, Redis
  - Conectividade de usuários (online/offline, WiFi/4G/3G)
  - OCR analytics (mobile/server), suspeições por severidade
  - WebSocket para updates em tempo real
  - Slider de refresh configurável (2s a 30min)

#### 5. Infraestrutura
- **Docker Compose:** 12 serviços orquestrados
- **PostgreSQL:** Porta 5432
- **Redis:** Porta 6379
- **MinIO:** Portas 9000 (API), 9001 (Console)
- **Prometheus:** Porta 9090
- **Grafana:** Porta 3000
- **Jaeger:** Porta 16686

---

## User Defined Namespaces

- [Leave blank - user populates]

---

## Components

### Backend Modules (server-core/app/)

#### API Layer (`api/v1/endpoints/`)
- `auth.py` - Login, refresh, logout
- `mobile.py` - Observações, suspeições, sync
- `intelligence.py` - Fila analítica, revisão
- `alerts.py` - Alertas automáticos
- `suspicious_routes.py` - Rotas suspeitas
- `hotspots.py` - Hotspots de criminalidade
- `route_prediction.py` - Previsão de rotas
- `assets.py` - Upload de assets
- `audit.py` - Auditoria
- `websocket.py` - WebSocket (configurável)

#### Services Layer (`services/`)
- `observation_service.py` - Processamento de observações
- `alert_service.py` - Geração de alertas
- `route_analysis_service.py` - Análise de rotas
- `hotspot_analysis_service.py` - Clustering espacial
- `route_prediction_service.py` - Previsão baseada em padrões
- `suspicious_route_service.py` - Detecção de rotas suspeitas
- `ocr_service.py` - OCR server-side
- `cache_service.py` - Cache Redis
- `storage_service.py` - Storage S3/local
- `websocket_service.py` - WebSocket
- `analytics_service.py` - Analytics geral
- `agent_movement_analysis_service.py` - Análise de movimento de agentes

#### Database Layer (`db/`)
- `base.py` - Modelos SQLAlchemy com PostGIS
- `session.py` - Session management com pooling
- `materialized_views.py` - Views materializadas

#### Schemas (`schemas/`)
- Pydantic models para I/O
- 21+ schemas definidos

#### Core (`core/`)
- `config.py` - Configuração centralizada (Pydantic Settings)
- `observability.py` - Logging, metrics, tracing
- `circuit_breaker.py` - Circuit breaker pattern
- `rate_limit.py` - Rate limiting
- `security.py` - JWT, password hashing

#### Workers (`workers/`)
- `stream_worker.py` - Consumer Redis Streams

### Analytics Dashboard (`analytics-dashboard/`)
- **Framework:** FastAPI standalone
- **Porta:** 9002
- **Abas (8):**
  - Overview - Métricas HTTP, DB, Cache, Alerts, PgBouncer, Redis
  - Alerts - Lista de alertas ativos em tempo real
  - Database - Pool de conexões, overflow, status de saúde
  - Circuit Breakers - Status de cada circuit breaker
  - Usabilidade - Conectividade (online/offline, WiFi/4G/3G, qualidade de rede)
  - Analytics - OCR (mobile/server), suspeitas por severidade, alertas por algoritmo
  - Auditoria - Logs de auditoria com filtros
  - Histórico Alertas - Histórico com paginação
- **Endpoints:**
  - `/dashboard` - Interface HTML
  - `/api/v1/health` - Status completo JSON
  - `/api/v1/metrics` - Métricas atuais
  - `/api/v1/alerts` - Lista de alertas
  - `/api/v1/audit/logs` - Logs de auditoria
  - `/api/v1/monitoring/history` - Histórico de alertas
  - `/ws` - WebSocket para updates em tempo real
- **Features:**
  - Slider de refresh configurável (2s a 30min)
  - WebSocket para updates em tempo real (com fallback polling)
  - Conexão ao server-core (porta 8000) para métricas reais
  - Responsivo para desktop e mobile
  - Dark mode nativo

### Web Console Modules (web-intelligence-console/src/app/)
- `alerts/` - Alertas
- `routes/` - Rotas suspeitas
- `hotspots/` - Hotspots com mapas
- `route-prediction/` - Previsão de rotas
- `convoys/` - Eventos de convoy
- `roaming/` - Eventos de roaming
- `watchlist/` - Watchlist
- `cases/` - Casos
- `audit/` - Auditoria
- `feedback/` - Feedback
- `queue/` - Fila analítica
- `users/` - Usuários
- `devices/` - Dispositivos

### Database Schema
- **Extensões:** PostGIS, TimescaleDB, Citus
- **Tabelas principais:**
  - `agency` - Hierarquia de agências
  - `user` - Usuários com roles
  - `device` - Dispositivos móveis
  - `vehicleobservation` - Observações de veículos
  - `suspicion` - Suspeições
  - `alert` - Alertas
  - `suspiciousroute` - Rotas suspeitas
  - `hotspot` - Hotspots
  - `convoyevent` - Eventos de convoy
  - `roamingevent` - Eventos de roaming
  - `watchlist` - Watchlist
  - `case` - Casos
  - `agentlocationlog` - Log de localização de agentes

---

## Patterns

### Architecture Patterns
- **Modular Monolith:** Fronteiras claras entre domínios
- **Separation of Concerns:** Routes → Services → Repository
- **Intelligence Cycle:** Campo → Backend → Inteligência → Feedback
- **Zero Trust:** Security não-negociável
- **Performance-first:** Targets P95/P99 para todas as operações

### Code Patterns
- **Async/IO-first:** I/O bound operations com async/await
- **Process Pool Executor:** CPU-bound tasks com hardware detection
- **Circuit Breaker:** Proteção contra falhas em cascata
- **Fallback Patterns:** Redis, storage, integrações externas
- **Dependency Injection:** get_db(), get_current_user()

### Database Patterns
- **PostGIS-native:** Queries geoespaciais (ST_Within, ST_DWithin, ST_Intersects)
- **Connection Pooling:** SQLAlchemy pool (20 + 10 overflow) + PgBouncer (opcional)
- **Indexing:** GIST (espaciais), BRIN (temporais)
- **Multi-tenant:** Sharding por agency_id via Citus

### API Patterns
- **Versioned API:** `/api/v1/`
- **Route Aliases:** Backward compatibility
- **JWT Auth:** Access token (30min) + Refresh token (7 dias)
- **Rate Limiting:** 100 req/60s baseline

### Performance Patterns
- **Redis Multi-banco:** Cache (DB 0), Streams (DB 1), Cache específico (DB 2)
- **Cache TTL:** Short (60s), Medium (300s), Long (3600s)
- **Parallel Execution:** Algoritmos executados em paralelo
- **Materialized Views:** Hotspots pré-calculados
- **TimescaleDB Hypertables:** Time-series otimizadas

### Security Patterns
- **JWT Authentication:** python-jose com HS256
- **Password Hashing:** Bcrypt via passlib
- **RBAC:** Roles (field_agent, intelligence, supervisor, admin)
- **Audit Logging:** Operações sensíveis registradas
- **CORS:** Configurável por origem

### Testing Patterns
- **Pytest:** Framework de testes com async support
- **Factory Boy:** Test data fixtures
- **Faker:** Dados de teste realistas
- **HTTPX:** HTTP client para testes

### Development Patterns
- **Black:** Code formatter
- **isort:** Import sorting
- **flake8:** Linting
- **mypy:** Type checking

---

## Key Features Implemented

### Core Features
- ✅ Auth JWT com refresh tokens
- ✅ Observações com idempotência de cliente
- ✅ Suspeições estruturadas
- ✅ Sync em lote com feedback pendente
- ✅ Confirmação de abordagem
- ✅ Upload de assets para storage S3-compatible
- ✅ Fila de inteligência com revisão versionada
- ✅ Watchlist, casos e analytics overview
- ✅ Auditoria consultável
- ✅ Redis Streams para eventos

### Advanced Features
- ✅ Rotas suspeitas com PostGIS
- ✅ Hotspots de criminalidade com clustering espacial
- ✅ Previsão de rotas baseada em padrões históricos
- ✅ Alertas automáticos para rotas recorrentes
- ✅ Eventos de convoy com padrões temporais
- ✅ Eventos de roaming com padrões de área
- ✅ OCR server-side com PyTorch + YOLO + EasyOCR

### Robustness Features
- ✅ Fallback seguro para Redis indisponível
- ✅ Worker dedicado para consumo assíncrono
- ✅ Rate limiting baseline
- ✅ Migration de índices geoespaciais
- ✅ Route aliases para backward compatibility
- ✅ PgBouncer auto-detection
- ✅ Health checks (DB, PgBouncer, Redis)

---

## Performance Optimizations

### Database Optimizations
- PgBouncer connection pooling (5-10x throughput)
- BRIN index para vehicle_observations (10x mais rápido)
- Parallel query tuning (2-4x mais rápido)
- Materialized views para hotspots (10x mais rápido)
- TimescaleDB hypertable para time-series (50-100x mais rápido)
- Citus escala horizontal por agency_id

### Algorithm Optimizations
- Execução paralela de algoritmos (50-70% redução de latência)
- Cache Redis para dados estáticos (30-50% queries redundantes eliminadas)
- Otimização Convoy com single query (O(N) → O(1))
- Otimização score composto com paralelização (7 queries paralelas)
- Otimização check route match com batch query (N → 1)
- Otimizações OCR server-side (3-5x mais rápido)

### Monitoring
- PerformanceMonitor com auto-tuning
- Targets P95/P99 por task type
- Prometheus metrics customizadas
- OpenTelemetry tracing
- Sentry error tracking

---

## Pending Items

### High Priority
- Conexão real com base estadual (hoje fallback dev)
- Build Android reproduzível no repositório (gradlew + pipeline)
- Testes automatizados de integração HTTP + Postgres/PostGIS + Redis
- Calibração dos algoritmos com dados reais

### Medium Priority
- Hardening de observabilidade (métricas por domínio, traces, alertas)
- Plano formal de depreciação do fluxo legado de feedback
- Políticas de retenção/exportação
- Classificação de sensibilidade

---

## Installation & Deployment

### Automated Installation (Windows)
```powershell
cd C:\Users\[username]\FARO
.\install-faro.ps1
```

### Start Services
```powershell
.\start-services.ps1
```

### Access Points
- **Server Core:** http://localhost:8000
- **Web Console:** http://localhost:3000
- **Analytics Dashboard:** http://localhost:9002/dashboard
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000
- **Jaeger:** http://localhost:16686

### Default Credentials
- **Admin:** admin@faro.pol / password

---

## Root Files / Arquivos da Raiz

### Scripts de Instalação e Gerenciamento

#### `install-faro.ps1`
- **Tipo:** PowerShell
- **Função:** Instalação automatizada completa do FARO
- **Parâmetros:**
  - `-SkipDocker` - Pular Docker
  - `-SkipWebConsole` - Pular Web Console
  - `-SkipAnalytics` - Pular Analytics Dashboard
  - `-PostgresPort`, `-ServerPort`, `-WebConsolePort`, `-AnalyticsPort` - Portas customizadas
- **Passos:** Verifica pré-requisitos → PostgreSQL → Redis → Migrations → Seed data → Inicia serviços → Health check

#### `start-services.ps1`
- **Tipo:** PowerShell
- **Função:** Inicia todos os serviços do FARO
- **Parâmetros:**
  - `-SkipWebConsole` - Pular Web Console
  - `-SkipAnalytics` - Pular Analytics Dashboard
  - Portas configuráveis
- **Funcionalidade:** Verifica portas → Encerra conflitos → Inicia Server Core (8000) → Web Console (3000) → Analytics Dashboard (9002)

#### `stop-services.ps1`
- **Tipo:** PowerShell
- **Função:** Encerra todos os serviços do FARO
- **Ações:** Encerra uvicorn (Python) → Encerra node (Web Console) → Para containers Docker (opcional)

#### `start-infrastructure.ps1`
- **Tipo:** PowerShell
- **Função:** Inicia infraestrutura essencial Docker (PostgreSQL + Redis)
- **Recursos:** Verificação automática do Docker, status de containers, informações de conexão
- **Portas:** PostgreSQL:5432, Redis:6379

#### `verify-installation.ps1`
- **Tipo:** PowerShell
- **Função:** Verifica se todos os serviços estão UP e saudáveis
- **Verificações:** PostgreSQL → Redis → Server Core → Web Console → Analytics Dashboard → Database tables → Health endpoints

#### `run_faro_services.py`
- **Tipo:** Python
- **Função:** Script Python alternativo para iniciar serviços
- **Serviços iniciados:**
  - Server Core (8000) - Uvicorn
  - Web Console (3000) - npm run dev
  - Analytics Dashboard (9002) - analytics_dashboard.app
- **Features:** Inicia em consoles separados, Ctrl+C para encerrar

### Configuração

#### `.env.example`
- Template de variáveis de ambiente
- **Variáveis:**
  - `SECRET_KEY` - Chave secreta JWT
  - `DATABASE_URL` - URL PostgreSQL (padrão: postgresql+asyncpg://faro:CHANGE_ME@localhost:5432/faro_db)
  - `S3_ACCESS_KEY`, `S3_SECRET_KEY` - Credenciais S3/MinIO

#### `.gitignore`
- Regras de exclusão do Git
- **Categorias:** IDE (VSCode, IntelliJ), Python (__pycache__, venv), Node.js (node_modules), Android (build), Logs, Test scripts
- **Nota:** Scripts de teste (check_*.py, test_*.py, simulate_*.py) são ignorados

### PgBouncer (`pgbouncer/`)
- **Configuração:** `pgbouncer-faro.ini` - Configuração do connection pooler
- **Usuários:** `userlist.txt` - Lista de usuários para autenticação
- **Propósito:** Connection pooling para PostgreSQL (opcional, auto-detection pelo server-core)

### IDE Configuration (`.windsurf/`)
- **Regras:** `rules/` - Configurações específicas do Windsurf IDE

### Estrutura de Diretórios - Analytics Dashboard

**Mudança Importante (2026-04-28):**
O Analytics Dashboard foi movido de `server-core/analytics_dashboard/` para `analytics-dashboard/` na **raiz do projeto**.

**Motivação:**
- Separação clara de responsabilidades (dashboard ≠ server-core)
- Facilita deployment independente
- Melhor organização do projeto

**Scripts atualizados:**
- `run_services.py` → usa `analytics-dashboard/app.py`
- `run_faro_services.py` → usa `analytics-dashboard/app.py`
- `start_all.bat` → inicia de `analytics-dashboard/`
- `start_services.ps1` → inicia de `analytics-dashboard/`
- `start-services.ps1` → verifica em `analytics-dashboard/`

### Outros Scripts

#### `run_services.py` (Otimizado)
- **Tipo:** Python 3
- **Framework:** Gerenciador de serviços com classe ServiceManager
- **Features:**
  - ✅ Paths relativos (detecta diretório automaticamente via `Path(__file__).parent`)
  - ✅ Logging colorido com timestamps (emojis + cores ANSI)
  - ✅ Verificação de portas antes de iniciar (com opção para encerrar processos conflitantes)
  - ✅ Graceful shutdown (Ctrl+C encerra todos os processos)
  - ✅ Monitoramento de serviços (reinicia se morrerem)
  - ✅ Logs individuais em `logs/` para cada serviço
  - ✅ Parâmetros: `--skip-web`, `--skip-analytics`
  - ✅ **Analytics Dashboard:** `analytics-dashboard/app.py` (raiz do projeto)

#### `run_faro_services.py` (Otimizado)
- **Tipo:** Python 3
- **Função:** Versão simplificada com consoles visíveis
- **Features:**
  - ✅ Paths relativos (Pathlib)
  - ✅ Logging colorido
  - ✅ Parâmetros: `--skip-web`, `--skip-analytics`
  - ✅ Monitoramento de processos
  - ✅ Ideal para desenvolvimento/debugging

#### `start_all.bat` (Otimizado)
- **Tipo:** Batch Script (Windows)
- **Features:**
  - ✅ Paths dinâmicos (`%~dp0` detecta diretório do script)
  - ✅ Cores ANSI (Windows 10+)
  - ✅ Verificação de portas antes de iniciar
  - ✅ Criação automática de diretório `logs/`
  - ✅ Parâmetros: `skip-web`, `skip-analytics`
  - ✅ Resumo colorido com URLs

#### `start_services.ps1` (Unificado - Script Principal)
- **Tipo:** PowerShell
- **Framework:** Unifica funcionalidades dos dois scripts anteriores
- **Features:**
  - ✅ Paths dinâmicos (detecta automaticamente)
  - ✅ Verificação de PostgreSQL (opcional com `-SkipPostgres`)
  - ✅ Verificação de portas (com opção de encerrar conflitos)
  - ✅ Logs centralizados em `logs/`
  - ✅ Parâmetros: `-SkipWeb`, `-SkipAnalytics`, `-SkipPostgres`, `-Port <porta>`
  - ✅ Graceful shutdown automático (Ctrl+C)
  - ✅ Monitoramento de processo
  - ✅ **Analytics Dashboard:** `analytics-dashboard/app.py` (raiz do projeto)
  - ✅ **Nota:** Substitui ambos `start-services.ps1` e `start_services.ps1` antigos

---

## Documentation References

- **Installation:** `INSTALL.md`
- **Server Tech Stack:** `docs/SERVER_TECH_STACK.md`
- **Architecture Overview:** `docs/architecture/overview.md`
- **Components:** `docs/architecture/components.md`
- **Backend Architecture:** `docs/architecture/backend.md`
- **API Contracts:** `docs/api/contracts.md`
- **Data Model:** `docs/data-model/model.md`
- **Database Schema:** `database/schema_unificado.sql`
- **PostGIS Guide:** `docs/database/postgis-indexes-guide.md`
- **Database Tuning:** `docs/database/db-tuning-actions.md`
