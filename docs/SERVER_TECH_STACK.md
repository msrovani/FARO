# F.A.R.O. Server Core - Stack Tecnológico Completo

**Data:** Abril 2026  
**Versão:** 1.0.0  
**Framework:** FastAPI (Python 3.11)

---

## Visão Geral

**Framework Principal:** FastAPI 0.115.0  
**Arquitetura:** Modular Monolith com fronteiras claras para extração futura  
**Padrão:** Async/IO-first com otimizações para performance  
**Filosofia:** Performance-first, Zero Trust, Intelligence Cycle

---

## 1. Core Framework & Language

### FastAPI 0.115.0
- **Framework ASGI** moderno com validação automática via Pydantic
- **Uvicorn 0.32.0** como ASGI server (workers configuráveis)
- Suporte nativo a async/await
- OpenAPI/Swagger automático (desativado em produção)
- **Mandatory:** Todo endpoint deve considerar P95/P99 targets

### Python 3.11
- Versão recente com melhorias de performance
- Type hints obrigatórios (Pydantic 2.10.0)
- Pydantic Settings para configuração centralizada

### Middleware Stack
```python
# Ordem de execução (top to bottom em main.py)
1. CORSMiddleware - Cross-origin configurável
2. GZipMiddleware - Compressão de resposta (min 1KB)
3. InMemoryRateLimitMiddleware - Rate limiting baseline (100 req/60s)
4. Circuit Breaker - Proteção contra falhas em cascata
5. Metrics/Tracing - OpenTelemetry instrumentation
```

---

## 2. Database & Data Layer

### PostgreSQL + PostGIS 16-3.4
- **Banco relacional** com extensão espacial (GeoAlchemy2 0.16.0)
- Suporte a queries geoespaciais (ST_Within, ST_DWithin, ST_Intersects)
- Índices GIST para dados espaciais
- Índices BRIN para dados temporais
- **Design:** Tabelas preparadas para Citus sharding (distributed by agency_id/tenant_id)

### SQLAlchemy 2.0.36 (Async)
- **ORM async** com session management
- Pool de conexões configurável (20 pool + 10 overflow)
- AsyncPG como driver (psycopg2-binary para sync)
- **Regra:** Usar async para I/O bound operations
- **Regra:** Prefer PgBouncer compatible session management

### Alembic 1.14.0
- Migrations versionadas com nomes descritivos
- Índices geoespaciais e operacionais (migration 0002)

### PgBouncer (Opcional com Auto-Detection)
- **Connection pooling** dedicado
- Hot-swap automático: detecta PgBouncer e usa se disponível
- Pool mode: transaction (configurável para session)
- Configurações:
  - pgbouncer_max_client_conn: 1000
  - pgbouncer_default_pool_size: 25
  - pgbouncer_min_pool_size: 5
- **Monitoramento:** Prometheus alerta se disponível mas não usado
- **Health check:** `check_pgbouncer_health()` com SHOW STATS

### Health Checks
```python
# Database pool health
check_db_health() -> {
    "status": "healthy",
    "pool_size": int,
    "available": int,
    "overflow": int,
    "checked_in": int,
    "checked_out": int,
    "invalid": int
}

# PgBouncer health
check_pgbouncer_health() -> {
    "status": "healthy",
    "pool_mode": "transaction",
    "total_requests": int,
    "total_errors": int,
    "query_duration_ms": float
}
```

---

## 3. Caching & Message Queuing

### Redis 7-alpine (3 bancos separados)
```bash
DB 0: Cache geral
DB 1: Redis Streams (eventos)
DB 2: Cache específico
```

- **Hiredis 3.1.0:** Parser C para performance
- Socket timeout: 5s
- Socket connect timeout: 5s

### Redis Streams
- **Publicação de eventos** com fallback seguro se indisponível
- Consumer group: `faro-analytics`
- Stream key: `faro.events`
- Configurações:
  - Batch size: 20
  - Block: 5s
  - Error backoff: 3s
- **Worker dedicado:** `app/workers/stream_worker.py`

### Cache TTL Configurável
```python
cache_ttl_short: 60s    # Dados mutáveis
cache_ttl_medium: 300s  # Dados normais
cache_ttl_long: 3600s   # Dados estáticos
```

---

## 4. Storage

### S3-Compatible (MinIO 7.2.10)
- **Endpoint:** http://localhost:9000
- **Presigned URLs:** 1h expiry
- **Bucket:** faro-assets
- **Opcional:** Fallback para local storage se indisponível
- **Porta reservada:** 9000 (S3 API), 9001 (Console UI)

### Local Storage Fallback
- **Path:** `./local_assets/`
- **Max size:** 10GB
- **AIOFiles 24.1.0** para async I/O

### Boto3 1.35.0
- Cliente AWS S3 para integrações externas

---

## 5. Authentication & Security

### JWT (python-jose 3.3.0)
- **Access token:** 30min
- **Refresh token:** 7 dias
- **Algoritmo:** HS256
- **Secret key:** Mínimo 32 caracteres (validado no startup)

### Password Hashing (passlib 1.7.4)
- **Bcrypt** para hashing
- Password mínimo 8 caracteres

### Rate Limiting
- **In-memory:** 100 req/60s
- **Exempt paths:** `/health`, `/`
- Configurável via env vars

### CORS
- Configurável por origem
- Credentials enabled por padrão
- Methods/headers configuráveis

### Security Principles
- **Zero Trust:** Security é não-negociável
- **RBAC:** Verificar sempre antes de permitir
- **Audit logging:** Registrar operações sensíveis

---

## 6. Async Processing

### Celery 5.4.0 + Celery-RedBeat 2.2.0
- **Task queue** distribuída
- Scheduler via Redis Beat
- Process pools para CPU-bound tasks

### Process Pool Executor
- **Auto-detection** de hardware via `hardware_detector.py`
- Configurações separadas:
  - General: 4-32 workers (auto)
  - CPU-bound: 4-8 workers (auto)
  - IO-bound: auto
- **PerformanceMonitor** com targets P95/P99

### Performance Targets (registrados no startup)
```python
# OCR processing
task_type="ocr_processing"
target_p95_ms=1000
target_p99_ms=2000

# OCR batch
task_type="ocr_batch"
target_p95_ms=5000
target_p99_ms=10000

# Route recurrence
task_type="route_recurrence"
target_p95_ms=500
target_p99_ms=1000

# Route direction
task_type="route_direction"
target_p95_ms=200
target_p99_ms=500

# Hotspot clustering
task_type="hotspot_clustering"
target_p95_ms=2000
target_p99_ms=5000
```

---

## 7. ML / Computer Vision

### PyTorch 2.5.0 + Torchvision 0.20.0
- **Framework ML** principal
- Suporte a CUDA/MPS configurável
- Device: "auto", "cpu", "cuda", "mps"

### Ultralytics 8.3.0
- **YOLO** para detecção de objetos
- OCR e reconhecimento de placas

### EasyOCR 1.7.1
- **OCR multilíngue**
- Confidence threshold: 0.7
- Auto-accept: 0.85 (opcional)
- Auto-accept enabled: false (default)

### OpenCV 4.10.0
- Processamento de imagens
- Headless version para server

### Pillow 11.0.0
- Manipulação de imagens

---

## 8. Observability & Monitoring

### OpenTelemetry 1.28.0
- **Tracing distribuído**
- Exporter OTLP
- Instrumentação FastAPI (opentelemetry-instrumentation-fastapi)
- Endpoint: http://localhost:4318/v1/traces

### Sentry 2.19.0
- **Error tracking**
- Integração FastAPI
- DSN configurável via env

### Prometheus 0.21.0
- **Métricas customizadas**
- Exportador nativo
- Porta: 9090
- Health checks de DB/PgBouncer

### Grafana
- **Dashboards** para visualização
- Datasources: Prometheus
- Porta: 3000

### Jaeger
- **UI** para análise de traces
- Collector OTLP
- Portas: 16686 (UI), 4319 (collector)

### Logging (structlog 24.4.0)
- **Structured logging**
- Configurável por nível (INFO default)
- JSON em produção
- pytz 2024.2 para timezone handling

---

## 9. Infrastructure & Deployment

### Docker
- **Base:** python:3.11-slim
- Multi-stage build
- Non-root user (faro:1000)
- Healthcheck: `/health` (30s interval, 30s timeout)
- Expose: 8000

### Docker Compose
- **12 serviços** orquestrados
- Networks: bridge (faro-network)
- Volumes persistentes

### Serviços Orquestrados
```yaml
1. postgres: PostgreSQL + PostGIS (5432)
2. redis: Redis (6379)
3. minio: MinIO S3 (9000, 9001)
4. server: FastAPI server (8000)
5. worker: Redis Streams consumer
6. nginx: Reverse proxy (80, 443)
7. prometheus: Metrics (9090)
8. alertmanager: Alerts (9093)
9. grafana: Dashboards (3000)
10. otel-collector: Traces (4317, 4318)
11. jaeger: Trace UI (16686)
12. minio-init: Bucket creation
```

### Nginx
- **Reverse proxy**
- TLS termination
- Static serving
- Config: `infra/nginx/nginx.conf`

---

## 10. Architecture Patterns

### Modular Monolith
- **Fronteiras claras** entre domínios
- Extraível para microserviços no futuro
- Sem premature optimization
- **Directory Structure:**
  ```
  app/
  ├── api/v1/          # Routes only
  ├── services/        # Business logic
  ├── db/repository/   # Data access logic
  ├── schemas/         # Pydantic models for I/O
  ├── core/            # Configuration, middleware
  ├── utils/           # Utilities
  └── workers/         # Background workers
  ```

### Módulos de Domínio (30+)
```
auth, users, devices
observations, plate_reads/ocr
suspicions, alerts
intelligence_reviews
route_analysis, route_prediction
suspicious_routes, hotspot_analysis
alert_service, cache
observability, materialized_views
feedback, audit, storage
workers/sync, integrations
analytics
```

### Separation of Concerns
- **app/api/v1/endpoints/**: Routes only
- **app/services/**: Business logic
- **app/db/repository/**: Data access
- **app/schemas/**: Pydantic models

### Intelligence Cycle
**Campo → Backend → Inteligência → Feedback**
- Campo: Mobile agents coletam dados
- Backend: Processa e armazena
- Inteligência: Analisa padrões
- Feedback: Retorna insights para campo

---

## 11. API Structure

### Router Hierarchy
```
/api/v1/
├── /auth (Authentication)
│   ├── /login
│   ├── /refresh
│   └── /logout
├── /mobile (Mobile App)
│   ├── /observations
│   ├── /suspicious-vehicles
│   └── /sync
├── /intelligence (Intelligence Console)
│   ├── /devices
│   ├── /suspicious_routes
│   ├── /hotspots
│   ├── /route_prediction
│   ├── /alerts
│   └── /boletim_atendimento
├── /audit (Audit)
├── /monitoring (Alert History)
├── /ws (WebSocket)
├── /documentation
└── /v1/assets (Storage)
```

### Dependency Injection
- **get_db()**: Database session
- **get_current_user()**: Auth
- Custom dependencies por endpoint

### Route Aliases
- Aliases de rota para evitar quebra de clientes
- Backward compatibility garantido

---

## 12. Performance Optimization

### Database
- **PgBouncer pooling** (auto-detection)
- Índices GIST (espaciais) + BRIN (temporais)
- Connection pooling SQLAlchemy (20 + 10 overflow)
- Pool timeout: 30s

### Caching
- **Redis multi-banco** (cache, streams, cache específico)
- TTL configurável por tipo (short/medium/long)
- Cache service layer

### Async
- **I/O bound:** async/await nativo
- **CPU bound:** Process Pool Executor
- Hardware detection para workers

### Compression
- **GZip middleware** (min 1KB)

### Monitoring
- **PerformanceMonitor** com auto-tuning
- Targets P95/P99 por task type
- Prometheus metrics customizadas

### Rate Limiting
- **In-memory** baseline protection
- Configurável por endpoint

---

## 13. Reporting & Documents

### Pandas 2.2.0
- Análise de dados
- Exportação de relatórios

### OpenPyXL 3.1.2
- Excel files

### ReportLab 4.1.0
- PDF generation

### python-docx 1.1.0
- Word documents

---

## 14. Testing Stack

### Pytest 8.3.0
- Framework de testes
- Async support (pytest-asyncio 0.24.0)
- Config: `pytest.ini`

### Factory Boy 3.3.0
- Test data fixtures

### Faker 30.10.0
- Dados de teste realistas

### HTTPX 0.27.0
- HTTP client para testes

---

## 15. Development Tools

### Black 24.10.0
- Code formatter

### isort 5.13.0
- Import sorting

### flake8 7.1.0
- Linting

### mypy 1.13.0
- Type checking

---

## 16. Configuration Management

### Pydantic Settings 2.6.0
- Configuração centralizada em `app/core/config.py`
- Environment variables via `.env`
- Validation no startup
- **Secret key validation:** Mínimo 32 caracteres

### Environment Variables
```bash
# Application
DEBUG=false
ENVIRONMENT=development

# Security
SECRET_KEY=32+ chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://...
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# PgBouncer
PGBOUNCER_ENABLED=false
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=6432
PGBOUNCER_POOL_MODE=transaction

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_STREAMS_URL=redis://localhost:6379/1
REDIS_CACHE_URL=redis://localhost:6379/2

# Storage
S3_ENABLED=false
S3_ENDPOINT=http://localhost:9000
S3_BUCKET_NAME=faro-assets

# Observability
SENTRY_DSN=
OTLP_ENDPOINT=http://localhost:4318/v1/traces
LOG_LEVEL=INFO
```

---

## 17. Capabilities Implementadas

### Core
- ✅ Auth JWT com refresh
- ✅ Observação com idempotência de cliente
- ✅ Suspeição estruturada
- ✅ Sync em lote com retorno de feedback pendente
- ✅ Confirmação de abordagem
- ✅ Upload de assets para storage S3-compatible
- ✅ Fila de inteligência e revisão versionada
- ✅ Watchlist, casos e analytics overview
- ✅ Auditoria consultável
- ✅ Publicação e consumo de eventos Redis Streams

### Advanced
- ✅ Cadastro de rotas suspeitas (SuspiciousRoute) com PostGIS
- ✅ Análise de hotspots de criminalidade com clustering espacial
- ✅ Previsão de rotas baseada em padrões históricos
- ✅ Serviço de alertas automáticos para rotas recorrentes
- ✅ Expansão de ConvoyEvent com padrões temporais
- ✅ Expansão de RoamingEvent com padrões de área

### Robustness
- ✅ Fallback seguro para indisponibilidade temporária de Redis
- ✅ Worker dedicado para consumo assíncrono
- ✅ Rate limiting baseline por middleware
- ✅ Migration de índices geoespaciais e operacionais
- ✅ Aliases de rota para evitar quebra de clientes

---

## 18. Capacidades de Robustez

### Resilience Patterns
- **Circuit Breaker:** Proteção contra falhas em cascata
- **Fallback Redis:** Publicação segura mesmo se Redis indisponível
- **Health Checks:** DB, PgBouncer, Redis
- **Auto-detection:** PgBouncer hot-swap
- **Rate Limiting:** Proteção baseline contra abuso

### Monitoring
- **PerformanceMonitor:** Auto-tuning baseado em P95/P99
- **Prometheus Metrics:** DB pool, PgBouncer stats, custom metrics
- **Sentry:** Error tracking
- **OpenTelemetry:** Distributed tracing
- **Structured Logging:** JSON logs em produção

---

## 19. Integrações Externas

### Base Estadual
- **Adapter separado** pronto para conexão real
- No ambiente dev retorna fallback `sem conexão`
- **Regra:** Não espalhar chamadas externas pelos endpoints
- **Regra:** Manter integração centralizada em módulo/adapters

### Integrações Planejadas
```bash
# SOEWEB (Sistema Operacional Estadual)
SOEWEB_BASE_URL=
SOEWEB_API_KEY=

# GovBR (Governo Federal)
GOVBR_CLIENT_ID=
GOVBR_CLIENT_SECRET=
```

---

## 20. Pendências Estruturais

### Testes
- ⚠️ Testes automatizados de integração em ambiente com Postgres/PostGIS/Redis
- ⚠️ Calibração dos algoritmos com dado real

### Deprecação
- ⚠️ Plano formal de depreciação do fluxo legado de feedback

### Compliance
- ⚠️ Políticas de retenção/exportação
- ⚠️ Classificação de sensibilidade

---

## 21. Pontos Fortes

1. **Performance-first:** Targets P95/P99, monitoring ativo
2. **Resilience:** Circuit breaker, fallbacks, health checks
3. **Observability:** Stack completo (traces, metrics, logs, errors)
4. **Spatial-native:** PostGIS integrado desde o início
5. **Async-native:** I/O bound operations otimizadas
6. **Modular:** Monolith com fronteiras claras
7. **Auto-scaling:** Hardware detection para workers
8. **Security:** JWT, rate limiting, RBAC preparado
9. **ML-integrated:** PyTorch + YOLO + OCR nativos
10. **Production-ready:** Docker, monitoring, alerting
11. **Zero Trust:** Security não-negociável
12. **Intelligence Cycle:** Campo → Backend → Inteligência → Feedback

---

## 22. Áreas de Atenção

1. **MinIO opcional:** Fallback local funciona, mas S3 recomendado para produção
2. **PgBouncer:** Auto-detection inteligente, mas requer configuração manual para ativar
3. **Testes:** Stack de testes presente, mas coverage não especificado
4. **Integrações externas:** Adapter pronto para SOEWEB/GovBR, mas não conectado
5. **WebSocket:** Habilitado via config, mas não ativo por padrão
6. **Calibração ML:** Algoritmos precisam de dados reais para calibração

---

## 23. Resumo Técnico

Stack moderno e bem-arquitetado, com foco em performance, observabilidade e resiliência. Uso inteligente de async/await, pooling, caching e monitoring. Arquitetura modular monolith permite evolução controlada sem complexidade prematura de microserviços. Integração nativa de ML/Computer Vision para OCR e detecção. Stack completo de observabilidade (traces, metrics, logs, errors). Princípios de Zero Trust e Performance-first aplicados consistentemente.

---

## 24. Referências

- **Backend Architecture:** `docs/architecture/backend.md`
- **Database Schema:** `database/schema_unificado.sql`
- **API Documentation:** `docs/api/openapi-v1-detailed.yaml`
- **PostGIS Guide:** `docs/database/postgis-indexes-guide.md`
- **PgBouncer Setup:** `server-core/docs/pgbouncer-setup.md`
- **Performance Tuning:** `docs/database/db-tuning-actions.md`

---

**Documento gerado automaticamente em 22/04/2026**
**Versão do Stack: 1.0.0**
