# F.A.R.O. Web Intelligence Console - Análise Profunda

**Data:** 2026-04-28  
**Status:** 🔍 **EM ANÁLISE** - Identificando problemas de integração

---

## 📋 Resumo da Análise

O Web Intelligence Console está **bem estruturado** mas possui problemas de integração com endpoints específicos do server-core que impedem o funcionamento completo de algumas funcionalidades.

---

## 🔍 Status Atual da Integração

### ✅ **O que JÁ Funciona:**

1. **Estrutura API Completa**
   - Todos os serviços API definidos em `src/app/services/api.ts`
   - Circuit breaker, cache, retry automático
   - Logger estruturado implementado
   - Tratamento de erros robusto

2. **Endpoints Principais Implementados**
   - Autenticação (`/auth/*`)
   - Intelligence Queue (`/intelligence/queue`)
   - Feedback (`/intelligence/feedback/*`)
   - Watchlist (`/intelligence/watchlists`)
   - Casos (`/intelligence/cases`)
   - Auditoria (`/audit/*`)
   - Dispositivos (`/intelligence/devices`)

3. **Frontend Bem Estruturado**
   - Next.js 15 com TypeScript
   - Componentes reutilizáveis
   - Navegação por abas funcionando
   - Estado global com React Query

### ❌ **Problemas Críticos Identificados:**

#### 1. **Endpoints de Analytics Faltando**

O frontend espera estes endpoints que **NÃO EXISTEM** ou **RETORNAM ERRO**:

| Endpoint Esperado | Status no Server | Problema |
|------------------|------------------|---------|
| `/intelligence/analytics/overview` | ✅ **EXISTE** | Mas dados incompletos |
| `/intelligence/analytics/observations-by-day` | ❌ **NÃO EXISTE** | Gráfico de observações não funciona |
| `/intelligence/analytics/top-plates` | ❌ **NÃO EXISTE** | Top placas não funciona |
| `/intelligence/analytics/unit-performance` | ❌ **NÃO EXISTE** | Performance por unidade não funciona |
| `/intelligence/agencies` | ❌ **NÃO EXISTE** | Filtro por agência não funciona |

#### 2. **Dados Incompletos no `/analytics/overview`**

O endpoint existe mas não retorna todos os campos esperados:

```typescript
// Esperado pelo frontend (DashboardStats):
interface DashboardStats {
  total_observations: number;
  today_observations: number;
  pending_reviews: number;
  active_alerts: number;
  confirmed_suspicions: number;
  discarded_suspicions: number;
  avg_response_time_hours: number;
  corrected_rate: number;
  critical_scores: number;
  // Campos faltando:
  high_scores: number;
  moderate_scores: number;
  low_scores: number;
  watchlist_hits: number;
  algorithm_runs: number;
  ocr_success_rate: number;
}
```

#### 3. **Integração com Algoritmos Parcial**

Os endpoints de algoritmos existem mas o frontend não está consumindo corretamente:

- ✅ `/intelligence/convoys` - Existe
- ✅ `/intelligence/roaming` - Existe  
- ✅ `/intelligence/routes` - Existe
- ❌ Frontend não exibe dados corretamente
- ❌ Mapas não funcionam (dependem de Mapbox GL)

---

## 🎯 **Análise por Aba/Funcionalidade**

### Dashboard Principal (page.tsx)
- **Status:** ⚠️ **PARCIAL**
- **Funciona:** Login, layout básico, navegação
- **Problema:** Cards de estatísticas sem dados completos

### Aba: Intelligence Queue
- **Status:** ✅ **FUNCIONA**
- **Dados:** Busca da fila de inteligência funciona

### Aba: Watchlist
- **Status:** ✅ **FUNCIONA**
- **Dados:** CRUD de watchlist funciona

### Aba: Casos
- **Status:** ✅ **FUNCIONA**
- **Dados:** Gestão de casos funciona

### Aba: Convoy Events
- **Status:** ⚠️ **PARCIAL**
- **Problema:** Dados existem mas exibição incorreta

### Aba: Roaming Events
- **Status:** ⚠️ **PARCIAL**
- **Problema:** Dados existem mas exibição incorreta

### Aba: Route Prediction
- **Status:** ⚠️ **PARCIAL**
- **Problema:** Algoritmos funcionam mas interface não exibe

### Aba: Hotspots
- **Status:** ✅ **FUNCIONA**
- **Dados:** Análise de hotspots funciona

### Aba: Alerts
- **Status:** ✅ **FUNCIONA**
- **Dados:** Alertas agregados funcionam

### Aba: Audit
- **Status:** ✅ **FUNCIONA**
- **Dados:** Logs de auditoria funcionam

### Aba: Devices
- **Status:** ✅ **FUNCIONA**
- **Dados:** Gestão de dispositivos funciona

---

## 🔧 **Soluções Necessárias**

### 1. **Criar Endpoints de Analytics Faltantes**

```python
# Adicionar em server-core/app/api/v1/endpoints/intelligence.py

@router.get("/analytics/observations-by-day")
async def get_observations_by_day(
    days: int = 7,
    agency_id: Optional[str] = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db)
):
    # Implementar busca de observações por dia
    pass

@router.get("/analytics/top-plates")
async def get_top_plates(
    limit: int = 10,
    agency_id: Optional[str] = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db)
):
    # Implementar busca de top placas
    pass

@router.get("/analytics/unit-performance")
async def get_unit_performance(
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db)
):
    # Implementar performance por unidade
    pass

@router.get("/agencies")
async def get_agencies(
    agency_type: Optional[str] = None,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db)
):
    # Implementar busca de agências
    pass
```

### 2. **Completar Dados do `/analytics/overview`**

Adicionar campos faltantes ao endpoint existente:

```python
# Campos faltantes no analytics/overview:
high_scores = await db.scalar(...)
moderate_scores = await db.scalar(...)
low_scores = await db.scalar(...)
watchlist_hits = await db.scalar(...)
algorithm_runs = await db.scalar(...)
ocr_success_rate = await db.scalar(...)
```

### 3. **Corrigir Frontend para Exibir Dados**

- Verificar se os componentes estão mapeando corretamente os campos
- Corrigir tipos TypeScript se necessário
- Implementar tratamento de loading e erro

### 4. **Configurar Mapas (Opcional)**

- Configurar Mapbox GL JS
- Adicionar tokens de API
- Implementar visualização de rotas e hotspots

---

## 📊 **Métricas da Integração**

| Categoria | Server-Core | Frontend | Status |
|-----------|-------------|----------|---------|
| Autenticação | ✅ | ✅ | **OK** |
| Intelligence Queue | ✅ | ✅ | **OK** |
| Watchlist | ✅ | ✅ | **OK** |
| Casos | ✅ | ✅ | **OK** |
| Feedback | ✅ | ✅ | **OK** |
| Auditoria | ✅ | ✅ | **OK** |
| Dispositivos | ✅ | ✅ | **OK** |
| Analytics Overview | ⚠️ Parcial | ⚠️ Parcial | **70%** |
| Analytics Detalhados | ❌ | ❌ | **0%** |
| Algoritmos | ✅ | ⚠️ Parcial | **60%** |
| Mapas | ⚠️ Parcial | ❌ | **30%** |

---

## 🎯 **Plano de Ação**

### Fase 1: Endpoints Analytics (45 min)
1. Implementar `/analytics/observations-by-day`
2. Implementar `/analytics/top-plates`
3. Implementar `/analytics/unit-performance`
4. Implementar `/agencies`

### Fase 2: Completar Overview (15 min)
1. Adicionar campos faltantes ao `/analytics/overview`
2. Validar estrutura de dados

### Fase 3: Corrigir Frontend (30 min)
1. Verificar mapeamento de dados nos componentes
2. Corrigir tipos TypeScript
3. Implementar loading states

### Fase 4: Algoritmos e Mapas (30 min)
1. Corrigir exibição de dados de algoritmos
2. Implementar visualização básica de mapas

**Tempo estimado total:** 2 horas

---

## 🚨 **Status Crítico**

O Web Intelligence Console **não está 100% funcional** para produção porque:
- 25% das funcionalidades de analytics não funcionam
- Dados incompletos no dashboard principal
- Algoritmos não exibem resultados corretamente

**Recomendação:** Implementar as correções antes de usar em produção. A infraestrutura está sólida, apenas precisa dos endpoints faltantes.
