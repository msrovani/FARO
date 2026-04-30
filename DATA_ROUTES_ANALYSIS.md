# F.A.R.O. - Análise de Rotas de Dados Internas

## 📊 Visão Geral da Arquitetura de Dados

### Backend (FastAPI - Porta 8000)
**Módulos de Endpoints:**
1. **intelligence.py** (42 endpoints) - Triagem, análise estruturada, watchlist, casos
2. **mobile.py** (13 endpoints) - Fluxo do agente de campo, observações, sync
3. **alerts.py** (11 endpoints) - Alertas automáticos, regras de alerta
4. **suspicion.py** (12 endpoints) - Gestão de suspeitas
5. **auth.py** (9 endpoints) - Autenticação, usuários, JWT
6. **audit.py** (7 endpoints) - Auditoria, logs, geolocalização
7. **agents.py** (4 endpoints) - Gestão de agentes
8. **hotspots.py** (3 endpoints) - Análise de hotspots
9. **monitoring.py** (3 endpoints) - Monitoramento
10. **devices.py** (2 endpoints) - Gestão de dispositivos
11. **assets.py** (1 endpoint) - Assets (imagens, áudio)

### Frontend (Next.js - Porta 3000)
**Serviços API Mapeados:**
1. **intelligenceApi** - 25 métodos
2. **alertsApi** - 7 métodos
3. **mobileApi** - 3 métodos
4. **authApi** - 9 métodos
5. **userApi** - 6 métodos
6. **hotspotsApi** - 1 método
7. **suspiciousRoutesApi** - 3 métodos

---

## 🔍 Fluxos de Dados End-to-End

### 1. FLUXO: Captura em Campo → Análise Inteligência

```
[AGENTE DE CAMPO] → [mobile.py] → [DATABASE] → [intelligence.py] → [WEB CONSOLE]
     │                    │               │              │                │
     │ POST /mobile/      │               │              │ GET /intelligence/queue
     │ observations       │               │              │                    │
     │                    │               │              │                    ▼
     │                    │               │              │         [queue/page.tsx]
     │                    │               │              │         Mesa Analítica
     │                    │               │              │
     │                    │               │              │ GET /intelligence/observations/{id}
     │                    │               │              │                    │
     │                    │               │              │                    ▼
     │                    │               │              │         [ObservationDetail]
     │                    │               │              │         Ficha Analítica
     │                    │               │              │
     │                    │               │              │ POST /intelligence/reviews
     │                    │               │              │                    │
     │                    │               │              │                    ▼
     │                    │               │              │         [Análise Estruturada]
     │                    │               │              │         Salva no DB
```

**Dados Enviados (Agente):**
- Placa, estado, país
- Localização (lat/long/accuracy/heading)
- Velocidade, tipo de veículo
- Cor, modelo, ano
- Agent info (id, nome, unidade)
- Device info (id, sync_status)
- Metadata (app_version, etc)
- Imagens (OCR com confiança)

**Dados Apresentados (Inteligência):**
- Placa confirmada com OCR
- Localização formatada (3 casas decimais)
- Rumo (3 casas decimais)
- Velocidade (1 casa decimal)
- Score composto
- Algoritmos ativos
- Histórico de suspeitas
- Botão de análise estruturada

### 2. FLUXO: Watchlist (Cadastro → Match)

```
[WEB CONSOLE] → [intelligence.py] → [DATABASE] → [mobile.py] → [AGENTE]
      │                  │               │              │           │
      │ POST /intelligence/watchlists    │              │           │
      │                    │             │              │           │
      │                    ▼             │              │           │
      │         [Cadastro no DB]         │              │           │
      │                                  │              │           │
      │                                  │              │ GET /mobile/observations
      │                                  │              │ (check watchlist match)
      │                                  │              │           │
      │                                  │              │           ▼
      │                                  │              │    [Alerta no App]
```

**Watchlist Status (Backend):**
- `active` - Ativo
- `suspended` - Suspenso
- `expired` - Expirado
- `closed` - Fechado

### 3. FLUXO: Alertas Automáticos

```
[DATABASE - Observations] → [alerts.py] → [alertsApi] → [alerts/page.tsx]
            │                    │              │               │
            │                    │ GET /alerts/aggregated       │
            │                    │                    │         │
            │                    │                    ▼         │
            │                    │         [Lista de Alertas]   │
            │                    │                            │
            │ POST /alerts/check-observation                  │
            │ (quando nova observação é criada)                │
```

**Tipos de Alertas:**
- `watchlist_match` - Match em watchlist
- `suspicious_route` - Rota suspeita
- `convoy_detected` - Comboio detectado
- `impossible_travel` - Viagem impossível
- `route_anomaly` - Anomalia de rota

### 4. FLUXO: Análise de Dados (Agentes)

```
[audit/geolocation/page.tsx] → [intelligenceApi] → [audit.py] → [DATABASE]
            │                         │                  │            │
            │ GET /audit/geolocation  │                  │            │
            │ analyzeAgentMovement    │                  │            │
            │ getAgentCoverageMap     │                  │            │
            │ correlation             │                  │            │
            │ tacticalPositioning     │                  │            │
```

### 5. FLUXO: Dashboard Estatístico

```
[page.tsx - Dashboard] → [dashboardApi] → [???] → [???]
         │                    │            │        │
         │                    │ GET /dashboard/stats
         │                    │ GET /dashboard/agencies
```

⚠️ **PROBLEMA IDENTIFICADO:** O `dashboardApi` é usado mas não está definido em `api.ts`!

---

## ⚠️ Inconsistências e Problemas Encontrados

### 1. **API Inexistente - Dashboard**
**Local:** `web-intelligence-console/src/app/page.tsx:9, 49`
**Problema:** `dashboardApi` é importado e usado mas não existe em `api.ts`
**Impacto:** Dashboard não carrega estatísticas
**Solução:** Criar o `dashboardApi` em `api.ts` ou implementar endpoints no backend

### 2. **Mismatch de Tipos - WatchlistStatus**
**Status:** ✅ CORRIGIDO na sessão anterior
**Backend:** `active | suspended | expired | closed`
**Frontend (antes):** `active | inactive | archived`
**Solução aplicada:** Atualizado para valores do backend

### 3. **Formatação Numérica Inconsistente**
**Status:** ✅ CORRIGIDO na sessão anterior
**Problema:** Lat/long com 6 casas decimais, rumo sem formatação
**Solução aplicada:** Padronizado para 3 casas decimais (lat/long/rumo) e 1 casa (velocidade)

### 4. **Cache HTTP sem Invalidação**
**Local:** `api.ts:48-82`
**Problema:** Cache de 5 minutos pode mostrar dados desatualizados
**Impacto:** Usuário vê dados antigos após modificações
**Sugestão:** Implementar invalidação seletiva ou reduzir TTL para operações críticas

### 5. **Circuit Breaker - Configuração Rígida**
**Local:** `api.ts:96-144`
**Problema:** Timeout de 60 segundos pode ser muito longo para UX
**Sugestão:** Reduzir para 30 segundos com retry automático

### 6. **Tratamento de Erros 422**
**Status:** ✅ CORRIGIDO na sessão anterior
**Problema:** Watchlist retornava 422 por tipo incorreto

### 7. **Polling vs WebSocket**
**Local:** `queue/page.tsx:199-206`
**Status:** Implementado polling a cada 10 segundos
**Sugestão:** Considerar WebSocket para atualizações em tempo real

---

## 📋 Endpoints Backend x Frontend - Mapeamento Completo

### ✅ MAPEADOS CORRETAMENTE

| Backend | Frontend | Status |
|---------|----------|--------|
| GET /intelligence/queue | intelligenceApi.getQueue | ✅ |
| POST /intelligence/reviews | intelligenceApi.createReview | ✅ |
| GET /intelligence/observations/{id} | intelligenceApi.getObservationDetail | ✅ |
| GET /intelligence/watchlists | intelligenceApi.listWatchlist | ✅ |
| POST /intelligence/watchlists | intelligenceApi.createWatchlistEntry | ✅ |
| PATCH /intelligence/watchlists/{id} | intelligenceApi.updateWatchlistEntry | ✅ |
| DELETE /intelligence/watchlists/{id} | intelligenceApi.deleteWatchlistEntry | ✅ |
| GET /intelligence/cases | intelligenceApi.listCases | ✅ |
| POST /intelligence/cases | intelligenceApi.createCase | ✅ |
| GET /mobile/history | mobileApi.getHistory | ✅ |
| POST /auth/login | authApi.login | ✅ |
| GET /auth/me | authApi.getCurrentUser | ✅ |
| POST /alerts/aggregated | alertsApi.getAggregatedAlerts | ✅ |
| GET /alerts/rules | alertsApi.getAlertRules | ✅ |

### ⚠️ ENDPOINTS NÃO MAPEADOS (Backend existe, Frontend não usa)

| Backend | Descrição | Prioridade |
|---------|-----------|------------|
| POST /alerts/check-observation | Verifica alertas para observação | Média |
| GET /mobile/observations/{id}/feedback | Feedback específico | Baixa |
| GET /intelligence/alerts | Lista alertas (não agregados) | Média |
| GET /audit/agent-movement/analyze | Análise de movimentação | Alta |
| GET /audit/agent-movement/coverage-map | Mapa de cobertura | Alta |
| GET /audit/agent-movement/correlation | Correlação agente-observação | Alta |
| GET /audit/agent-movement/tactical-positioning | Posicionamento tático | Alta |

### ❌ ENDPOINTS FRONTEND SEM BACKEND

| Frontend | Backend | Status |
|----------|---------|--------|
| dashboardApi.getStats | ❌ NÃO EXISTE | 🔴 CRÍTICO |
| dashboardApi.getAgencies | ❌ NÃO EXISTE | 🔴 CRÍTICO |

---

## 🎯 Recomendações de Melhoria

### 1. **Implementar Endpoints Dashboard** (🔴 Alta Prioridade)
```python
# intelligence.py ou novo dashboard.py
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    agency_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return {
        "total_observations": await count_observations(db, agency_id),
        "total_suspicions": await count_suspicions(db, agency_id),
        "queue_size": await count_queue(db, agency_id),
        "alerts_today": await count_alerts_today(db, agency_id),
        "feedback_pending": await count_feedback_pending(db, agency_id),
    }
```

### 2. **Adicionar Cache Busting**
```typescript
// api.ts - Adicionar header para cache busting
api.interceptors.request.use((config) => {
  if (config.method === 'get' && config.url?.includes('/intelligence/queue')) {
    config.params = { ...config.params, _t: Date.now() };
  }
  return config;
});
```

### 3. **Implementar Retry com Exponential Backoff**
```typescript
// Melhorar o retry existente
const RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff
```

### 4. **Adicionar Tipos Estritos para Respostas**
- Criar interfaces para todas as respostas de API
- Usar Zod para validação runtime

### 5. **Implementar WebSocket para Tempo Real**
```typescript
// Novo arquivo: websocket.ts
export const websocket = new WebSocket(`ws://localhost:8000/ws`);
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'new_observation') {
    // Atualizar queue automaticamente
  }
};
```

---

## 📊 Métricas de Fluxo

### Latência Esperada por Fluxo
| Fluxo | Tempo Esperado | Otimização |
|-------|----------------|------------|
| Captura → DB | < 500ms | Async processing |
| DB → Queue | < 2s | Polling 10s |
| Análise → Salvar | < 1s | Transaction |
| Alerta → Notificação | < 5s | WebSocket |

### Volume de Dados Estimado
| Endpoint | Requisições/Min | Payload Médio |
|----------|-----------------|---------------|
| GET /queue | 6 (polling) | ~50 KB |
| POST /observations | Variável | ~200 KB (com imagem) |
| POST /reviews | Baixo | ~5 KB |
| GET /alerts | 1 | ~20 KB |

---

## ✅ Checklist de Correções Aplicadas

- [x] Corrigir WatchlistStatus (backend/frontend)
- [x] Formatação numérica padronizada
- [x] Saída da lista após análise
- [x] Cards de contagem com debug
- [ ] Criar dashboardApi
- [ ] Implementar endpoints dashboard no backend
- [ ] Adicionar cache busting para queue
- [ ] Implementar WebSocket
- [ ] Otimizar retry logic

---

## 📝 Notas Técnicas

### Formato de Dados Padronizado
```typescript
// Coordenadas
interface GeoPoint {
  latitude: number;  // 3 casas decimais: -30.035
  longitude: number; // 3 casas decimais: -51.218
  accuracy?: number; // metros, inteiro
}

// Heading/Rumo
interface Direction {
  heading: number;   // 3 casas decimais: 45.500°
}

// Velocidade
interface Speed {
  speed: number;     // 1 casa decimal: 78.5 km/h
}
```

### Padrão de Nomenclatura
- Backend: `snake_case` (Python)
- Frontend: `camelCase` (TypeScript/JavaScript)
- Conversão: Automática via Axios interceptors

---

**Data da Análise:** 2026-04-30
**Versão:** 1.0
**Próxima Revisão:** Após implementação das correções
