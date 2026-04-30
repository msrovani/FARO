# F.A.R.O. Analytics Dashboard - Análise Profunda

**Data:** 2026-04-28  
**Status:** 🔍 **EM ANÁLISE** - Identificando problemas de integração

---

## 📋 Resumo da Análise

O Analytics Dashboard está **parcialmente integrado** com o server-core, mas existem problemas críticos que impedem o funcionamento completo de todas as abas.

---

## 🔍 Status Atual da Integração

### ✅ **O que JÁ Funciona:**

1. **Conexão Básica com Server-Core**
   - Dashboard detecta server na porta 8000
   - Endpoint `/api/v1/metrics` está implementado
   - Dados básicos são coletados

2. **Métricas do Server-Core Implementadas**
   ```python
   # Em server-core/app/core/observability.py (linhas 307-668)
   @app.get("/api/v1/metrics")
   async def metrics_json() -> dict:
       # ✅ Database pool metrics
       # ✅ PgBouncer status
       # ✅ Redis health
       # ✅ Cache hit ratio
       # ✅ Circuit breakers
       # ✅ Observações hoje
       # ✅ Suspeitas por nível
       # ✅ Alerts hoje
       # ✅ Intelligence reviews
       # ✅ Watchlist ativa
       # ✅ User connectivity
       # ✅ OCR metrics
       # ✅ Algorithm runs
   ```

3. **WebSocket para Updates em Tempo Real**
   - Implementado no dashboard
   - Broadcast automático a cada 5 segundos

---

### ❌ **Problemas Críticos Identificados:**

#### 1. **Endpoints Faltantes no Server-Core**

O dashboard espera estes endpoints que **NÃO EXISTEM**:

| Endpoint Esperado | Status | Impacto |
|------------------|---------|---------|
| `/api/v1/audit/logs` | ❌ **NÃO EXISTE** | Aba 7 - Auditoria não funciona |
| `/api/v1/monitoring/history` | ❌ **NÃO EXISTE** | Aba 8 - Histórico Alertas não funciona |
| `/api/v1/monitoring/history/stats` | ❌ **NÃO EXISTE** | Estatísticas não funcionam |

#### 2. **Dados Incompletos no `/api/v1/metrics`**

O server-core retorna dados, mas o dashboard não está consumindo tudo:

```python
# Métricas disponíveis no server-core:
✅ db_pool_size, db_pool_available, db_pool_overflow
✅ pgbouncer_in_use, pgbouncer_available, pgbouncer_used
✅ redis_healthy, cache_hit_ratio
✅ circuit_breakers
✅ observations_today, alerts_today
✅ suspicion_high/medium/low/confirmed/rejected
✅ algo_watchlist, algo_convoy, algo_roaming
✅ user_online/offline/wifi/4g/3g
✅ ocr_mobile_success_rate, ocr_server_success_rate
```

#### 3. **Frontend Não Conectado**

O HTML do dashboard está embutido no Python, mas:
- O JavaScript não está buscando os dados corretamente
- As abas não estão atualizando com dados reais
- Interface está mostrando valores zerados

---

## 🎯 **Análise por Aba**

### Aba 1: Overview
- **Status:** ⚠️ **PARCIAL**
- **Funciona:** Conexão com server, métricas básicas
- **Problema:** Alguns campos não são preenchidos

### Aba 2: Alerts
- **Status:** ⚠️ **PARCIAL**
- **Funciona:** Alertas gerados localmente
- **Problema:** Não busca alertas reais do banco

### Aba 3: Database
- **Status:** ✅ **FUNCIONA**
- **Dados:** Pool metrics do server-core

### Aba 4: Circuit Breakers
- **Status:** ✅ **FUNCIONA**
- **Dados:** Status dos circuit breakers

### Aba 5: Usabilidade
- **Status:** ⚠️ **PARCIAL**
- **Dados:** User connectivity disponível mas não exibido

### Aba 6: Analytics
- **Status:** ⚠️ **PARCIAL**
- **Dados:** OCR e algoritmos disponíveis mas não exibidos

### Aba 7: Auditoria
- **Status:** ❌ **NÃO FUNCIONA**
- **Problema:** Endpoint `/api/v1/audit/logs` não existe

### Aba 8: Histórico Alertas
- **Status:** ❌ **NÃO FUNCIONA**
- **Problema:** Endpoints `/api/v1/monitoring/history` não existem

---

## 🔧 **Soluções Necessárias**

### 1. **Criar Endpoints Faltantes no Server-Core**

```python
# Adicionar em server-core/app/api/v1/endpoints/monitoring.py

@app.get("/api/v1/audit/logs")
async def get_audit_logs(
    resource_type: str = None,
    start_date: str = None,
    end_date: str = None,
    ttl_days: str = "30",
    page: str = "1",
    page_size: str = "50",
    db: AsyncSession = Depends(get_db)
):
    # Implementar busca real de audit logs
    pass

@app.get("/api/v1/monitoring/history")
async def get_alert_history(
    alert_group: str = None,
    severity: str = None,
    start_date: str = None,
    end_date: str = None,
    acknowledged: bool = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    # Implementar busca real de histórico de alertas
    pass
```

### 2. **Corrigir Frontend do Dashboard**

O HTML está embutido no Python, mas precisa:
- Conectar JavaScript com os endpoints reais
- Implementar atualização das abas com dados do server
- Remover dados de demonstração

### 3. **Melhorar Integração WebSocket**

O WebSocket só envia "ping/pong". Precisa:
- Enviar métricas reais
- Atualizar interface em tempo real
- Implementar reconexão automática

---

## 📊 **Métricas Disponíveis vs. Utilizadas**

| Categoria | Disponível no Server | Utilizada no Dashboard | Gap |
|-----------|----------------------|------------------------|-----|
| Database | ✅ | ✅ | ✅ OK |
| PgBouncer | ✅ | ✅ | ✅ OK |
| Redis | ✅ | ✅ | ✅ OK |
| Circuit Breakers | ✅ | ✅ | ✅ OK |
| Observations | ✅ | ⚠️ | Parcial |
| Alerts | ✅ | ⚠️ | Parcial |
| User Connectivity | ✅ | ❌ | Não exibido |
| OCR Metrics | ✅ | ❌ | Não exibido |
| Algorithms | ✅ | ❌ | Não exibido |
| Audit Logs | ❌ | ❌ | Endpoint não existe |
| Alert History | ❌ | ❌ | Endpoint não existe |

---

## 🎯 **Plano de Ação**

### Fase 1: Criar Endpoints Faltantes (30 min)
1. Implementar `/api/v1/audit/logs`
2. Implementar `/api/v1/monitoring/history`
3. Implementar `/api/v1/monitoring/history/stats`

### Fase 2: Corrigir Frontend (45 min)
1. Separar HTML do Python
2. Implementar JavaScript para buscar dados
3. Conectar todas as abas com endpoints reais

### Fase 3: Melhorar WebSocket (15 min)
1. Enviar métricas reais via WebSocket
2. Implementar atualização automática das abas

**Tempo estimado total:** 1.5 horas

---

## 🚨 **Status Crítico**

O Analytics Dashboard **não está funcional** para produção porque:
- 2 das 8 abas não funcionam (25% inoperante)
- Dados reais não são exibidos corretamente
- Interface mostra valores zerados

**Recomendação:** Implementar as correções antes de usar em produção.
