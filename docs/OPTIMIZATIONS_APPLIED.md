# F.A.R.O. Server Core - Otimizações Aplicadas

**Data:** 22 de Abril de 2026  
**Versão:** 1.0.0  
**Baseado em:** Melhores práticas de 2025-2026 para FastAPI, PostgreSQL, Redis, PgBouncer

---

## Resumo Executivo

Este documento detalha todas as otimizações aplicadas ao servidor F.A.R.O. baseadas em estudo profundo das melhores práticas da indústria. As otimizações abrangem FastAPI, PostgreSQL/PostGIS, Redis, PgBouncer, SQLAlchemy e arquitetura de cache.

**Principais Benefícios Esperados:**
- Redução de latência em 30-50% através de cache otimizado
- Aumento de throughput em 2-3x através de pooling otimizado
- Prevenção de memory leaks através de worker restarts
- Melhor monitoramento de performance com pg_stat_statements
- Resiliência aprimorada com fallbacks e health checks

---

## 1. FastAPI & Server Configuration

### 1.1 Gunicorn Production Settings

**Arquivo:** `server-core/app/core/config.py`

**Otimizações Aplicadas:**
```python
# Gunicorn Production Settings (recommended for production)
gunicorn_enabled: bool = Field(default=True)
gunicorn_worker_class: str = Field(default="uvicorn.workers.UvicornWorker")
gunicorn_worker_connections: int = Field(default=1000)
gunicorn_max_requests: int = Field(default=1000)  # Restart workers after N requests
gunicorn_max_requests_jitter: int = Field(default=50)  # Random jitter
gunicorn_graceful_timeout: int = Field(default=30)
gunicorn_timeout: int = Field(default=120)
gunicorn_preload: bool = Field(default=True)  # Copy-on-write optimization
```

**Justificativa (Best Practices):**
- **Gunicorn + Uvicorn Workers**: Recomendado pela documentação oficial do FastAPI para produção
- **max_requests + max_requests_jitter**: Previne memory leaks acumulativos e thundering herd
- **worker_connections**: 1000 conexões por worker para alta concorrência
- **preload**: Reduz uso de memória através de copy-on-write
- **graceful_timeout**: Permite completion de requests durante restarts

**Referência:** 
- [FastAPI Production Deployment Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/deployment/server-workers/)

### 1.2 Gunicorn Startup Script

**Arquivo:** `server-core/gunicorn_start.py`

**Funcionalidades:**
- Auto-detection de CPU cores para workers
- Configuração de timeouts otimizados
- Logging com response time para performance monitoring
- Preload app habilitado
- Security headers configurados

**Uso em Produção:**
```bash
gunicorn -c gunicorn_start.py app.main:app
```

---

## 2. SQLAlchemy Async Pool Optimizations

### 2.1 Connection Pool Settings

**Arquivo:** `server-core/app/db/session.py`

**Otimizações Aplicadas:**
```python
engine = create_async_engine(
    get_database_url(),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,  # 20
    max_overflow=settings.database_max_overflow,  # 10
    pool_timeout=settings.database_pool_timeout,  # 30
    pool_pre_ping=settings.database_pool_pre_ping,  # True
    pool_recycle=settings.database_pool_recycle,  # 3600
    future=True,
)
```

**Arquivo:** `server-core/app/core/config.py`
```python
database_pool_pre_ping: bool = Field(default=True)  # Validate connections
database_pool_recycle: int = Field(default=3600)  # Recycle hourly
```

**Justificativa (Best Practices):**
- **pool_pre_ping**: Valida conexões antes do uso, previne erros de stale connections
- **pool_recycle**: Recicla conexões a cada hora, previne problemas de long-running connections
- **pool_size=20 + max_overflow=10**: Total de 30 conexões concorrentes (ajustável por hardware)
- **pool_timeout**: Timeout de 30s para obter conexão do pool

**Referência:**
- [SQLAlchemy Connection Pooling Documentation](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [FastAPI Production Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)

---

## 3. PgBouncer Optimizations

### 3.1 Advanced Pool Configuration

**Arquivo:** `pgbouncer/pgbouncer-faro.ini`

**Otimizações Aplicadas:**
```ini
# Pool configuration
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3

# Connection reset and health (best practices)
server_reset_query = DISCARD ALL
server_check_delay = 30
server_reset_query_always = 0  # Enable prepared statements

# Timeouts (optimized for production)
server_lifetime = 3600
server_idle_timeout = 600
server_connect_timeout = 15

# TCP keepalive (maintain connections over unreliable networks)
tcp_keepalive = 1
tcp_keepidle = 30
tcp_keepintvl = 10
tcp_keepcnt = 3
```

**Justificativa (Best Practices):**
- **server_reset_query = DISCARD ALL**: Limpa estado de transação entre conexões
- **server_check_delay = 30**: Verifica saúde de conexões a cada 30s
- **server_reset_query_always = 0**: Habilita prepared statements para melhor performance
- **tcp_keepalive**: Mantém conexões ativas em redes não confiáveis
- **reserve_pool**: Pool de reserva para spikes de carga

**Referência:**
- [PgBouncer Configuration Guide](https://dev.to/rajasekhar_beemireddy_cb8/boosting-postgresql-performance-with-pgbouncer-a-configuration-guide-gkj)
- [PgBouncer Official Documentation](https://www.pgbouncer.org/usage.html)

---

## 4. PostgreSQL / PostGIS Optimizations

### 4.1 Performance Tuning Configuration

**Arquivo:** `database/postgresql-tuning.conf`

**Otimizações Aplicadas:**
```ini
# CONNECTION SETTINGS
max_connections = 200

# MEMORY SETTINGS (adjust based on available RAM)
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 16MB
maintenance_work_mem = 512MB

# WAL SETTINGS
wal_buffers = 64MB
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min

# QUERY PLANNER
random_page_cost = 1.1  # SSD optimization
effective_io_concurrency = 200  # SSD optimization

# POSTGIS-SPECIFIC TUNING
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# AUTOVACUUM SETTINGS
autovacuum_max_workers = 4
autovacuum_naptime = 10s
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.02

# STATISTICS
track_io_timing = on
track_functions = all

# LOGGING
log_min_duration_statement = 1000  # Log queries > 1s
```

**Justificativa (Best Practices):**
- **shared_buffers = 25% RAM**: Configuração padrão recomendada
- **effective_cache_size = 75% RAM**: Cache do sistema operacional
- **random_page_cost = 1.1**: Otimizado para SSDs (default é 4.0)
- **parallel workers**: Habilita processamento paralelo para queries PostGIS
- **aggressive autovacuum**: Previne bloat em workloads de alta escrita
- **track_io_timing**: Habilita tracking de I/O para pg_stat_statements

**Referência:**
- [PostGIS Performance Tuning](https://www.crunchydata.com/blog/postgis-performance-postgres-tuning)
- [PostGIS Performance Tips](https://postgis.net/docs/performance_tips.html)
- [PostgreSQL Tuning Guide](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)

### 4.2 pg_stat_statements Extension

**Arquivo:** `server-core/alembic/versions/0020_pg_stat_statements.py`

**Otimização Aplicada:**
```python
# Enable pg_stat_statements extension
op.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
```

**Configuração Adicional (postgresql.conf):**
```ini
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.max = 10000
pg_stat_statements.track = all
pg_stat_statements.track_utility = off
pg_stat_statements.track_planning = off
```

**Queries Úteis:**
```sql
-- Encontrar queries mais lentas
SELECT total_exec_time, mean_exec_time, calls, rows, query 
FROM pg_stat_statements 
WHERE calls > 0 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Encontrar queries mais frequentes
SELECT total_exec_time, calls, query 
FROM pg_stat_statements 
WHERE calls > 0 
ORDER BY calls DESC 
LIMIT 10;
```

**Justificativa (Best Practices):**
- **pg_stat_statements**: Essencial para identificar slow queries
- **track = all**: Monitora todas as queries
- **track_utility = off**: Exclui commands como SET, BEGIN para reduzir ruído
- **track_planning = off**: Exclui tempo de planning para focar em execução

**Referência:**
- [PostgreSQL pg_stat_statements Documentation](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Crunchy Data PostGIS Performance](https://www.crunchydata.com/blog/postgis-performance-postgres-tuning)

---

## 5. Redis Cache Optimizations

### 5.1 Cache Manager with Cache-Aside Pattern

**Arquivo:** `server-core/app/utils/cache_manager.py`

**Otimizações Aplicadas:**
```python
class CacheManager:
    """
    Production-ready cache manager with cache-aside pattern.
    
    Best practices implemented:
    - Cache-aside (lazy loading) for read-heavy workloads
    - Configurable TTLs per data type
    - Automatic serialization/deserialization
    - Graceful degradation on Redis failures
    - Connection pooling
    """
```

**Funcionalidades:**
- **Cache-Aside Pattern**: Lazy loading para workloads read-heavy
- **TTL Configurável**: short (60s), medium (300s), long (3600s)
- **Connection Pooling**: 50 conexões max
- **Graceful Degradation**: Continua funcionando se Redis falhar
- **SCAN ao invés de KEYS**: Previne blocking em produção
- **Decorator @cached**: Para fácil uso em funções

**Exemplo de Uso:**
```python
from app.utils.cache_manager import cache_manager, cached

# Usando cache manager diretamente
result = await cache_manager.get_or_set(
    prefix="user",
    identifier=user_id,
    fetch_func=lambda: db.get_user(user_id),
    ttl_type="medium"
)

# Usando decorator
@cached(prefix="observation", ttl_type="short")
async def get_observation(obs_id: str):
    return await db.get_observation(obs_id)
```

**Justificativa (Best Practices):**
- **Cache-Aside**: Padrão mais comum e eficiente para read-heavy workloads
- **Lazy Loading**: Primeiro request é lento, subsequentes são rápidos
- **TTLs Estratégicos**: Dados mutáveis = curto, dados estáticos = longo
- **SCAN vs KEYS**: KEYS bloqueia o server, SCAN é non-blocking
- **Graceful Degradation**: Cache não deve quebrar a aplicação

**Referência:**
- [Redis Cache Optimization Guide](https://redis.io/blog/guide-to-cache-optimization-strategies)
- [Redis Best Practices](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/)

---

## 6. Arquitetura de Cache

### 6.1 TTL Strategy

**Arquivo:** `server-core/app/core/config.py`

**Configuração:**
```python
cache_ttl_short: int = Field(default=60)      # 1 minute (dados mutáveis)
cache_ttl_medium: int = Field(default=300)    # 5 minutes (dados normais)
cache_ttl_long: int = Field(default=3600)   # 1 hour (dados estáticos)
```

**Recomendação de Uso:**
- **short (60s)**: Dados que mudam frequentemente (status, contadores)
- **medium (300s)**: Dados normais com mudanças ocasionais (perfis, configurações)
- **long (3600s)**: Dados estáticos (lookup tables, referências)

### 6.2 Cache Patterns

**Cache-Aside (Lazy Loading):**
```python
# Aplicação verifica cache primeiro
# Se miss, busca do banco e popula cache
# Próximos hits são rápidos
```

**Write-Through (Opcional para consistência):**
```python
# Escreve no banco E no cache simultaneamente
# Garante consistência mas aumenta latência de escrita
# Recomendado para dados críticos (financeiro, inventory)
```

**Write-Behind (Opcional para performance):**
```python
# Escreve no cache primeiro, banco depois (async)
# Baixa latência de escrita, mas risco de perda de dados
# Recomendado para analíticos/não-críticos
```

---

## 7. Monitoramento & Observabilidade

### 7.1 Health Checks

**Arquivo:** `server-core/app/db/session.py`

**Health Checks Implementados:**
```python
async def check_db_health() -> dict:
    """Check database connection pool health."""
    # Retorna: pool_size, available, overflow, checked_in, checked_out

async def check_pgbouncer_health() -> dict:
    """Check PgBouncer connection and get pool statistics."""
    # Retorna: status, pool_mode, total_requests, total_errors
```

### 7.2 Prometheus Metrics

**Métricas Disponíveis:**
- DB pool metrics (size, available, overflow)
- PgBouncer stats (requests, errors)
- Performance metrics (P95, P99 targets)
- Custom task metrics (OCR, route analysis, etc.)

---

## 8. Próximos Passos Recomendados

### 8.1 Aplicação Imediata
1. **Aplicar migration**: `alembic upgrade head` (para pg_stat_statements)
2. **Aplicar PostgreSQL tuning**: Copiar `database/postgresql-tuning.conf` para `postgresql.conf` e restart PostgreSQL
3. **Configurar PgBouncer**: Usar configuração otimizada em `pgbouncer-faro.ini`
4. **Usar Gunicorn em produção**: `gunicorn -c gunicorn_start.py app.main:app`

### 8.2 Integração de Cache
1. **Importar cache_manager**: `from app.utils.cache_manager import cache_manager, cached`
2. **Aplicar decorator**: Em funções que beneficiam de cache
3. **Configurar TTL**: Escolher TTL apropriado por tipo de dado
4. **Monitorar cache hits**: Verificar eficácia do caching

### 8.3 Monitoramento Contínuo
1. **pg_stat_statements**: Revisar queries lentas semanalmente
2. **Prometheus/Grafana**: Monitorar métricas de performance
3. **Pool utilization**: Ajustar pool sizes baseado em load real
4. **Cache hit ratio**: Otimizar TTLs baseado em padrões de acesso

---

## 9. Referências de Melhores Práticas

### Fontes Consultadas
1. **FastAPI Best Practices**: https://github.com/zhanymkanov/fastapi-best-practices
2. **FastAPI Production Deployment**: https://render.com/articles/fastapi-production-deployment-best-practices
3. **PostGIS Performance Tuning**: https://www.crunchydata.com/blog/postgis-performance-postgres-tuning
4. **PostGIS Performance Tips**: https://postgis.net/docs/performance_tips.html
5. **Redis Cache Optimization**: https://redis.io/blog/guide-to-cache-optimization-strategies
6. **PgBouncer Configuration**: https://dev.to/rajasekhar_beemireddy_cb8/boosting-postgresql-performance-with-pgbouncer-a-configuration-guide-gkj
7. **SQLAlchemy Connection Pooling**: https://docs.sqlalchemy.org/en/20/core/pooling.html

---

## 10. Checklist de Implementação

- [x] Documentação completa do stack tecnológico
- [x] Configuração Gunicorn para produção
- [x] Otimizações de pool SQLAlchemy (pool_pre_ping, pool_recycle)
- [x] Configuração avançada do PgBouncer
- [x] Tuning de PostgreSQL/PostGIS
- [x] Migration para pg_stat_statements
- [x] Script de startup Gunicorn
- [x] Cache Manager com cache-aside pattern
- [x] Documentação de otimizações aplicadas
- [ ] Aplicar migration no banco de dados
- [ ] Aplicar tuning no postgresql.conf
- [ ] Testar Gunicorn em ambiente de staging
- [ ] Integrar cache_manager em services existentes
- [ ] Configurar monitoramento Prometheus/Grafana
- [ ] Calibrar TTLs baseado em workload real

---

**Documento gerado em 22 de Abril de 2026**  
**Otimizações baseadas em melhores práticas de 2025-2026**
