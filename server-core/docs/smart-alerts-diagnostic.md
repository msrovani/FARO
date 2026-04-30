# F.A.R.O. Smart Alerts - Diagnosticador Inteligente
# =============================================================================
# Este documento contém TODOS os alertas com:
# - Gatilho (quando dispara)
# - Insight (diagnóstico)
# - Causas possíveis  
# - Soluções específicas (comandos)
# - Auto-fixa
# - Nível de urgência
# =============================================================================

# ALERTA 1.1: PgBouncer disponível mas não está em uso
# ------------------------------------------------------------------------------
- alert: PgBouncerAvailableNotInUse
  severity: warning
  urgency: medium
  
  triggers_when: |
    PgBouncer foi detectado mas PGBOUNCER_ENABLED=false
    
  insight: |
    Sistema não está usando connection pooling.
    Conexões diretas ao PostgreSQL = overhead alto.
    
  possible_causes: |
    1. Variável PGBOUNCER_ENABLED não definida como true
    2. PgBouncer não iniciado
    3. .env não recarregado após mudança
    
  solutions: |
    # Verificar status atual:
    curl http://localhost:8000/health | jq .pgbouncer
    
    # Habilitar:
    # .env:
    PGBOUNCER_ENABLED=true
    PGBOUNCER_HOST=localhost
    PGBOUNCER_PORT=6432
    
    # Reiniciar app:
    # sudo systemctl restart faro
    
  auto_fix: false
  runbook: docs/pgbouncer-setup.md

# ALERTA 1.2: PgBouncer pool exhausted
# ------------------------------------------------------------------------------
- alert: PgBouncerPoolExhausted
  severity: critical
  urgency: high
  
  triggers_when: |
    Todas as conexões do PgBouncer estão em uso (available=0)
    
  insight: |
    ⚠️ URGENTE: Pool 100% usado. Clientes esperando.
    
  possible_causes: |
    1. Spikes de tráfego
    2. Queries demorando muito
    3. Pool size muito pequeno
    4. Connection leak
    
  solutions: |
    # Verificar status:
    psql -h localhost -p 6432 -d pgbouncer -c "SHOW STATS"
    
    # Aumentar pool temporário:
    # Em .env:
    PGBOUNCER_DEFAULT_POOL_SIZE=50
    
    # Verificar queries lentas:
    psql -h localhost -p 6432 -d pgbouncer -c "SHOW CLIENTS"
    
    # Kill queries problemáticas (CUIDADO):
    # SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction'
    
  auto_fix: false
  annotations:
    slack: "@faro-oncall: PgBouncer pool exhausted! Verificar urgentemente."

# ALERTA 1.3: Clientes esperando conexão
# ------------------------------------------------------------------------------
- alert: PgBouncerClientsWaiting
  severity: warning
  urgency: medium
  
  triggers_when: |
    Clientes aguardando > 0
    
  solutions: |
    # Verificar o que está causando espera:
    psql -h localhost -p 6432 -d pgbouncer -c "SHOW POOLS"
    
  auto_fix: false

# ALERTA 2.1: Database pool exhausted
# ------------------------------------------------------------------------------
- alert: DatabasePoolExhausted
  severity: critical
  urgency: high
  
  triggers_when: |
    Todas as conexões SQLAlchemy em uso
    
  insight: |
    ⚠️ URGENTE: Application-level pool 100%
    
  possible_causes: |
    1. database_pool_size pequeno
    2. Queries demorando
    3. Transaction não commitada (leak)
    
  solutions: |
    # Verificar health:
    curl /health | jq .database_pool
    
    # Verificar queries:
    psql -c "SELECT count(*) FROM pg_stat_activity"
    
    # Aumentar pool em .env:
    DATABASE_POOL_SIZE=50
    DATABASE_MAX_OVERFLOW=20
    
  auto_fix: false

# ALERTA 2.2: Database pool overflow
# ------------------------------------------------------------------------------
- alert: DatabasePoolOverflow
  severity: warning
  urgency: medium
  
  triggers_when: |
    Overflow > 10 conexões
    
  solutions: |
    # quick fix:
    DATABASE_POOL_SIZE=30
    DATABASE_MAX_OVERFLOW=20
    
  auto_fix: false

# ALERTA 2.3: Database unhealthy
# ------------------------------------------------------------------------------
- alert: DatabaseUnhealthy
  severity: critical
  urgency: critical
  
  triggers_when: |
    pool_size = 0 ou ausente
    
  insight: |
    🔴 CRÍTICO: Banco inacessível!
    
  possible_causes: |
    1. PostgreSQL fora do ar
    2. Rede/firewall bloqueando
    3. Credenciais inválidas
    4. tablespace cheio
    5. many conexões max exceeded
    
  solutions: |
    # Verificar PostgreSQL:
    docker ps | grep postgres
    # ou
    sudo systemctl status postgresql
    
    # Testar conexão direta:
    psql -h $DB_HOST -U faro -d faro
    
    # Verificar logs:
    docker logs postgres
    # ou
    sudo tail -f /var/log/postgresql/postgresql.log
    
    # Se tablespace cheio:
    # SELECT pg_size_pretty(pg_database_size('faro'))
    # Verificar: SELECT * FROM pg_tablespace;
    
  auto_fix: false
  critical_actions: |
    1. Verificar se PostgreSQL está rodando
    2. Testar conexão local
    3. Verificar logs
    4. Se não iniciar, verificar disco

# ALERTA 2.4: DB overload + PgBouncer OFF (SMART)
# ------------------------------------------------------------------------------
- alert: DBOverloadPgBouncerOff
  severity: critical
  urgency: critical
  
  triggers_when: |
    DB overload + PgBouncer não está em uso
    
  insight: |
    🔴 URGENTE: conexão direta não aguenta!
    HABILITAR PgBouncer AGORA!
    
  solutions: |
    # URGENTE - COPIAR E EXECUTAR:
    
    # 1. Habilitar PgBouncer:
    set PGBOUNCER_ENABLED=true
    set PGBOUNCER_DEFAULT_POOL_SIZE=50
    
    # 2. Aumentar pool local:
    set DATABASE_POOL_SIZE=30
    set DATABASE_MAX_OVERFLOW=15
    
    # 3. Verificar se PgBouncer está rodando:
    # Windows: .\pgbouncer.exe pgbouncer-faro.ini
    # Linux: sudo systemctl start pgbouncer
    
    # 4. Reiniciar app:
    # sudo systemctl restart faro
    
    # 5. Monitorar:
    curl /health | jq .pgbouncer
    
  auto_fix: false

# ALERTA 3.1: Alta latência P95 (>5s)
# ------------------------------------------------------------------------------
- alert: HighLatencyP95
  severity: warning
  urgency: medium
  
  triggers_when: |
    Latência P95 > 5 segundos
    
  insight: |
    5% das requisições estão lentas
    
  possible_causes: |
    1. Queries não otimizadas
    2. Índices faltando
    3. CPU/memória altos
    4. Rede lenta
    
  solutions: |
    # Verificar queries lentas:
    psql -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"
    
    # Verificar índices:
    psql -c "\\di" faro.*
    
    # Adicionar índice:
    # CREATE INDEX idx ON table(column);
    
    # Verificar CPU:
    top
    
    # Verificar memória:
    free -h
    
  auto_fix: false

# ALERTA 3.2: Latência crítica P95 (>10s)
# ------------------------------------------------------------------------------
- alert: CriticalLatencyP95
  severity: critical
  urgency: high
  
  triggers_when: |
    Latência P95 > 10 segundos
    
  insight: |
    ⚠️ CRÍTICO: Servidor com sérios problemas
    
  solutions: |
    # Verificar processos:
    top
    htop
    
    # Verificar database:
    psql -c "SELECT * FROM pg_stat_activity WHERE state != 'idle'"
    
    # Se necessário, restart:
    # sudo systemctl restart faro
    
  auto_fix: false

# ALERTA 3.3: Alta taxa de erros 5xx (>5%)
# ------------------------------------------------------------------------------
- alert: HighErrorRate5xx
  severity: warning
  urgency: medium
  
  triggers_when: |
    Taxa de erros 5xx > 5%
    
  insight: |
    erros no servidor
    
  solutions: |
    # Verificar logs:
    tail -100 logs/app.log | grep ERROR
    
    # Verificar health:
    curl /health
    
    # Verificar se é erro de DB:
    psql -c "SELECT last_error FROM faro.errors ORDER BY created_at DESC LIMIT 10"
    
  auto_fix: false

# ALERTA 3.4: Taxa crítica de erros 5xx (>20%)
# ------------------------------------------------------------------------------
- alert: CriticalErrorRate5xx
  severity: critical
  urgency: critical
  
  triggers_when: |
    Taxa de erros 5xx > 20%
    
  insight: |
    🔴 CRÍTICO: Servidor com falha grave!
    
  solutions: |
    # Verificar logs imediatamente:
    tail -f logs/app.log | grep ERROR
    
    # Verificar crash:
    dmesg | tail -20
    
    # Se crash, restart:
    # sudo systemctl restart faro
    
    # Verificar memória:
    dmesg | grep -i oom
    
  auto_fix: false

# ALERTA 4.1: Circuit breaker aberto
# ------------------------------------------------------------------------------
- alert: CircuitBreakerOpen
  severity: critical
  urgency: high
  
  triggers_when: |
    Circuit breaker para endpoint = OPEN
    
  insight: |
    ⚠️ PROTECÃO ATIVADA: serviço de backend não está respondendo bem
    
  possible_causes: |
    1. Servicio de destino fora do ar
    2. Serviço muito lento (timeout)
    3. many falhas consecutivas
    4. Banco de dados indisponível
    
  solutions: |
    # Verificar qual circuito:
    curl /health | jq .circuit_breakers
    
    # Testar endpoint diretamente:
    curl http://localhost:8000/api/v1/health
    
    # Verificar logs do serviço:
    # docker logs service-name
    # ou
    # journalctl -u service-name -n 50
    
    # Se serviço OK, esperar (circuit fecha sozinho após timeout)
    # Timeout configured: 60s default
    
  auto_fix: false
  runbook: docs/circuit-breaker.md

# ALERTA 4.2: Circuit breaker metade aberto
# ------------------------------------------------------------------------------
- alert: CircuitBreakerHalfOpen
  severity: warning
  urgency: low
  
  triggers_when: |
    Circuit = HALF_OPEN (testando recuperação)
    
  insight: |
    Sistema está testando se serviço recuperou
    
  solutions: |
    # Monitorar por mais tempo
    # Se circuit fecha após 2 successes, OK
    # Se falha, volta para OPEN
    
  auto_fix: false

# ALERTA 5.1: Redis indisponível
# ------------------------------------------------------------------------------
- alert: RedisUnavailable
  severity: warning
  urgency: medium
  
  triggers_when: |
    Métricas de cache ausente > 2min
    
  insight: |
    Redis pode estar fora do ar
    
  possible_causes: |
    1. Redis parado
    2. Rede bloquada
    3. Credenciais erradas
    4. Memória cheia
    
  solutions: |
    # Testar Redis:
    redis-cli ping
    # Deve retornar: PONG
    
    # Verificar config:
    # Em .env:
    # REDIS_URL=redis://localhost:6379/0
    
    # Verificar se está rodando:
    # docker ps | grep redis
    # ou
    # redis-cli info
    
    # Verificar memória:
    redis-cli info memory
    
  auto_fix: false

# ALERTA 5.2: Cache hit ratio baixo (<50%)
# ------------------------------------------------------------------------------
- alert: CacheLowHitRatio
  severity: warning
  urgency: low
  
  triggers_when: |
    Hit ratio < 50%
    
  insight: |
    Cache não está sendo efetivo
    
  possible_causes: |
    1. TTL muito curto
    2. Dados que mudam muito
    3. Cache muito pequeno (evictions)
    
  solutions: |
    # Verificar hit ratio:
    # curl /metrics | grep cache_hit
    
    # Aumentar TTL em decorators:
    # @cached_query(ttl=3600)  # 1 hora
    # @cached_query(preset="long")  # 1 hora
    
    # Verificar evictions:
    redis-cli info stats | grep evicted
    
  auto_fix: false

# ALERTA 6.1: CPU alta (>80%)
# ------------------------------------------------------------------------------
- alert: HighCPU
  severity: warning
  urgency: medium
  
  triggers_when: |
    CPU usage > 80%
    
  solutions: |
    # Verificar processos:
    top
    htop
    
    # Verificar se há loops infinitos:
    # Ver logs de crash:
    dmesg | tail -20
    
    # Reduzir workers se necessário:
    # Em config: process_pool_max_workers=4
    
  auto_fix: false

# ALERTA 6.2: Memória alta (>2GB)
# ------------------------------------------------------------------------------
- alert: HighMemory
  severity: warning
  urgency: medium
  
  triggers_when: |
    Memory > 2GB
    
  solutions: |
    # Verificar uso:
    /metrics | grep process_resident
    
    # Verificar se memory leak:
    # Observar crescimento ao longo do tempo
    
    # Se necessário, restart:
    # sudo systemctl restart faro
    
  auto_fix: false

# ALERTA 7.1: Mobile Sync alta taxa de falha
# ------------------------------------------------------------------------------
- alert: MobileSyncHighFailureRate
  severity: warning
  urgency: medium
  
  triggers_when: |
    Sync failures > 10%
    
  insight: |
    Agentes de campo podem ter problema para sincronizar
    
  possible_causes: |
    1. Rede instável
    2. API timeout
    3. Dados inválidos
    4. many dispositivos offline
    
  solutions: |
    # Verificar últimos erros:
    # Dashboard de sync
    # ou
    # SELECT * FROM sync_errors ORDER BY created_at DESC LIMIT 20
    
    # Verificar rede dos agentes:
    # Ver logs de rede:
    # docker logs faro-mobile | grep network
    
  auto_fix: false

# ALERTA 7.2: Mobile Sync pendente (>100 items)
# ------------------------------------------------------------------------------
- alert: MobileSyncPending
  severity: warning
  urgency: low
  
  triggers_when: |
    Itens pendentes > 100 por muito tempo
    
  insight: |
    Dados podem estar desatualizados nos dispositivos
    
  solutions: |
    # Verificar queue:
    curl /intelligence/queue | jq length
    
    # Forçar sync manual:
    # POST /mobile/sync/force
    # ou
    # Usar comando no app mobile
    
    # Verificar agentes offline:
    # SELECT agent_id, last_sync FROM agents WHERE last_sync < now() - interval '1 hour'
    
  auto_fix: false

# ALERTA 8.1: Algoritmo falhou
# ------------------------------------------------------------------------------
- alert: AlgorithmExecutionFailed
  severity: warning
  urgency: medium
  
  triggers_when: |
    Algoritmo de predição com erros
    
  insight: |
    Predições de rota não estão sendo geradas
    
  possible_causes: |
    1. Dados insuficientes
    2. Erro no modelo ML
    3. Timeout de processing
    4. Memória GPU insuficiente
    
  solutions: |
    # Verificar logs de algoritmo:
    # docker logs faro | grep algorithm
    # ou
    # journalctl -u faro -n 50 | grep -i algo
    
    # Verificar dados:
    psql -c "SELECT count(*) FROM observations;"
    psql -c "SELECT count(*) FROM routes;"
    
    # Verificar GPU:
    # nvidia-smi (se disponível)
    
  auto_fix: false

# =============================================================================
# RESUMO DE AÇÕES POR SEVERIDADE
# =============================================================================

# 🔴 CRITICAL (responder em 15min):
# - DatabaseUnhealthy
# - CriticalErrorRate5xx  
# - CircuitBreakerOpen (se muitos endpoints)
# - DBOverloadPgBouncerOff
# AÇÃO: Restart, verificar logs, escalar infra

# ⚠️ WARNING (responder em 1h):
# - HighLatencyP95
# - DatabasePoolOverflow
# - PGBoosterAvailableNotInUse
# - MobileSyncHighFailureRate
# AÇÃO: Ajustar configurações, verificar queries

# 🔵 INFO (responder em 24h):
# - CacheLowHitRatio
# - AlgorithmExecutionFailed (ocasional)
# AÇÃO: Monitorar, otimizar

# =============================================================================
# COMANDOS DE DIAGNÓSTICO RÁPIDO
# =============================================================================

# Ver status geral:
curl /health | jq .

# Ver métricas Prometheus:
curl /metrics | grep -E "(faro_.*)"

# Ver logs de erro:
tail -100 logs/app.log | grep ERROR

# Ver DATABASE:
psql -c "SELECT count(*) FROM pg_stat_activity"

# Ver PGBOUNCER:
psql -h localhost -p 6432 -d pgbouncer -c "SHOW STATS"

# Ver REDIS:
redis-cli info | grep -E "used_memory|evicted_keys"

# =============================================================================
# FIM DO GUIA DE ALERTAS
# =============================================================================