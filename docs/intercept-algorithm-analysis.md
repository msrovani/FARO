# F.A.R.O. - Análise do Algoritmo INTERCEPT

**Data:** 2026-04-28  
**Status:** 🔍 **EM ANÁLISE** - Algoritmo não encontrado no código

---

## 📋 Resumo da Busca

Realizei busca completa pelo algoritmo **INTERCEPT** em todo o código do FARO, mas **não foi encontrado**. 

---

## 🔍 **O que foi Encontrado**

### ✅ **Algoritmos Existentes no FARO**

No arquivo `server-core/app/db/base.py`, encontrei os seguintes algoritmos implementados:

```python
class AlgorithmType(str, PyEnum):
    WATCHLIST = "watchlist"                    # ✅ Implementado
    IMPOSSIBLE_TRAVEL = "impossible_travel"    # ✅ Implementado
    ROUTE_ANOMALY = "route_anomaly"            # ✅ Implementado
    SENSITIVE_ZONE_RECURRENCE = "sensitive_zone_recurrence"  # ✅ Implementado
    CONVOY = "convoy"                          # ✅ Implementado
    ROAMING = "roaming"                        # ✅ Implementado
    COMPOSITE_SCORE = "composite_score"        # ✅ Implementado
```

### ❌ **Algoritmo INTERCEPT Não Existe**

- **Nenhuma referência** a "INTERCEPT" em nenhum arquivo
- **Não está** no enum `AlgorithmType`
- **Não há** implementação no `analytics_service.py`
- **Não há** endpoints específicos para INTERCEPT

---

## 🎯 **Possíveis Cenários**

### **Cenário 1: Algoritmo INTERCEPT é um Conceito, não Implementação**
- INTERCEPT pode ser um **nome operacional** para combinação de algoritmos
- Pode se referir a **abordagem qualificada** baseada em múltiplos sinais
- Não existe como algoritmo único no código

### **Cenário 2: Algoritmo Pendente de Implementação**
- INTERCEPT pode estar no **roadmap futuro**
- Pode ser um **requisito não implementado**
- Pode precisar ser criado do zero

### **Cenário 3: INTERCEPT = Watchlist + Route Anomaly**
- Conceito de "interceptar" veículos baseado em:
  - Veículos em watchlist
  - Rotas anômalas
  - Combinação de múltiplos fatores

---

## 🔧 **Opções de Implementação**

### **Opção 1: Criar Algoritmo INTERCEPT do Zero** ⭐ **Recomendado**

```python
# Adicionar em server-core/app/db/base.py
class AlgorithmType(str, PyEnum):
    # ... algoritmos existentes ...
    INTERCEPT = "intercept"  # 🆕 NOVO

# Implementar em server-core/app/services/analytics_service.py
async def evaluate_intercept_algorithm(
    db: AsyncSession, 
    observation: VehicleObservation
) -> InterceptEvent | None:
    """
    Algoritmo INTERCEPT - Identificação de veículos para abordagem qualificada.
    
    Combina múltiplos fatores:
    - Watchlist hits
    - Route anomalies
    - Impossible travel
    - Sensitive zone recurrence
    - Composite score elevado
    """
    # Implementar lógica combinada
    pass
```

### **Opção 2: Mapear INTERCEPT para Algoritmos Existentes**

```python
# INTERCEPT = combinação de sinais de múltiplos algoritmos
def calculate_intercept_score(observation):
    watchlist_score = get_watchlist_score(observation)
    route_score = get_route_anomaly_score(observation)
    travel_score = get_impossible_travel_score(observation)
    zone_score = get_sensitive_zone_score(observation)
    
    # Lógica de combinação ponderada
    intercept_score = (
        watchlist_score * 0.4 +
        route_score * 0.25 +
        travel_score * 0.2 +
        zone_score * 0.15
    )
    
    return intercept_score > 0.7  # Threshold para abordagem
```

### **Opção 3: Implementar como View Composta no Web Intelligence**

```typescript
// Criar aba "INTERCEPT" no Web Intelligence
// Combinar dados de múltiplos algoritmos existentes
interface InterceptEvent {
  observationId: string;
  plateNumber: string;
  interceptScore: number;
  triggers: {
    watchlist: boolean;
    routeAnomaly: boolean;
    impossibleTravel: boolean;
    sensitiveZone: boolean;
  };
  recommendation: "APPROACH" | "MONITOR" | "IGNORE";
}
```

---

## 🎯 **Implementação Sugerida**

### **Fase 1: Criar Algoritmo INTERCEPT (45 min)**

1. **Adicionar ao Enum:**
```python
# server-core/app/db/base.py
INTERCEPT = "intercept"
```

2. **Implementar Lógica:**
```python
# server-core/app/services/analytics_service.py
async def evaluate_intercept_algorithm(db, observation):
    # Verificar watchlist
    watchlist_hit = await check_watchlist(db, observation)
    
    # Verificar route anomaly
    route_anomaly = await check_route_anomaly(db, observation)
    
    # Verificar impossible travel
    impossible_travel = await check_impossible_travel(db, observation)
    
    # Verificar sensitive zone
    zone_recurrence = await check_sensitive_zone(db, observation)
    
    # Calcular score combinado
    intercept_score = calculate_combined_score(watchlist_hit, route_anomaly, impossible_travel, zone_recurrence)
    
    # Retornar evento se threshold atingido
    if intercept_score > 0.7:
        return InterceptEvent(...)
```

3. **Criar Tabela/Model:**
```python
# server-core/app/db/base.py
class InterceptEvent(Base):
    observation_id: Mapped[UUID] = mapped_column(ForeignKey("vehicleobservation.id"))
    intercept_score: Mapped[float] = mapped_column(Float)
    triggers: Mapped[dict] = mapped_column(JSON)
    recommendation: Mapped[str] = mapped_column(String)
    # ... outros campos
```

### **Fase 2: Expor no Web Intelligence (30 min)**

1. **Criar Endpoint:**
```python
# server-core/app/api/v1/endpoints/intelligence.py
@router.get("/intercept/events")
async def get_intercept_events(...):
    # Buscar eventos INTERCEPT
    pass
```

2. **Criar Aba no Frontend:**
```typescript
// web-intelligence-console/src/app/screens/intercept-screen.tsx
export function InterceptScreen() {
  // Exibir eventos de interceptação
  // Filtros por score, triggers, recomendações
  // Mapa com localizações
  // Actions: aproach, monitor, ignore
}
```

### **Fase 3: Integrar com Fluxo Existente (15 min)**

1. **Integrar com evaluate_observation_algorithms**
2. **Adicionar métricas ao observability**
3. **Incluir nos dashboards**

---

## 🚨 **Status Atual**

**O algoritmo INTERCEPT não existe no código atual.** 

**Recomendação:** Implementar como algoritmo combinatório que utiliza os sinais dos algoritmos existentes para identificar veículos que devem ser abordados.

**Tempo estimado:** 1.5 horas para implementação completa

---

## 📝 **Próximos Passos**

1. **Confirmar com o usuário** o que exatamente é o algoritmo INTERCEPT
2. **Implementar lógica combinatória** baseada nos algoritmos existentes
3. **Criar aba específica** no Web Intelligence Console
4. **Integrar com fluxo** de avaliação de observações
5. **Testar com dados reais**

O conceito de INTERCEPT parece ser operacional (abordagem qualificada) e pode ser implementado como uma camada de inteligência sobre os algoritmos existentes.
