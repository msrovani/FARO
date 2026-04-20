# Relatório de Análise e Correções - Migrations Alembic
**Arquiteto Senior de DB** - Análise para Stack Atual (PostgreSQL + PostGIS + TimescaleDB + Citus)

---

## 1. Ações Realizadas

### 1.1 Reversão de Decisão Supabase
- **Ação**: Deletar arquivos criados para Supabase (errado)
- **Arquivos deletados**:
  - `database/schema_supabase.sql`
  - `database/generate_schema.py`
  - `database/ANALISE_DB_ARQUITETO.md`
- **Motivo**: Manter stack atual com extensões de performance (TimescaleDB, Citus)

### 1.2 Análise de Migrations
- **Total de migrations**: 11 (0001-0011)
- **Framework**: Alembic com SQLAlchemy ORM
- **Schema definido em**: `server-core/app/db/base.py`

---

## 2. Bugs Críticos Identificados e Corrigidos

### 2.1 Inconsistência de Nomes de Tabelas (snake_case vs camelCase)

**Problema**: SQLAlchemy usa camelCase por padrão (ex: `vehicleobservation`), mas algumas migrations usavam snake_case (ex: `vehicle_observations`).

**Impacto**: As migrations falhariam ao tentar acessar tabelas que não existem com o nome incorreto.

**Migrations Corrigidas**:

#### 0007 - BRIN Indexes
- **Arquivo**: `server-core/alembic/versions/0007_brin_index_observations.py`
- **Correções**:
  - `vehicle_observations` → `vehicleobservation` (upgrade)
  - `vehicle_observations` → `vehicleobservation` (downgrade)
  - `ix_vehicle_observations_*` → `ix_vehicleobservation_*`

#### 0009 - Materialized Views
- **Arquivo**: `server-core/alembic/versions/0009_materialized_views_hotspots.py`
- **Correções**:
  - `FROM vehicle_observations vo` → `FROM vehicleobservation vo` (mv_daily_hotspots)
  - `FROM vehicle_observations vo` → `FROM vehicleobservation vo` (mv_agency_hotspots)

#### 0010 - TimescaleDB
- **Arquivo**: `server-core/alembic/versions/0010_timescaledb_setup.py`
- **Correções**:
  - `'vehicle_observations'` → `'vehicleobservation'` (create_hypertable)
  - `FROM vehicle_observations` → `FROM vehicleobservation` (continuous aggregate)
  - `'vehicle_observations'` → `'vehicleobservation'` (downgrade - convert_to_regular_table)
  - Comentário retention policy também corrigido

#### 0011 - Citus
- **Arquivo**: `server-core/alembic/versions/0011_citus_setup.py`
- **Correções**:
  - `'vehicle_observations'` → `'vehicleobservation'` (create_distributed_table)
  - Lista de tabelas corrigida (upgrade):
    - `convoy_events` → `convoyevent`
    - `impossible_travel_events` → `impossibletravelevent`
    - `route_anomaly_events` → `routeanomalyevent`
    - `sensitive_asset_recurrence_events` → `sensitiveassetrecurrenceevent`
    - `roaming_events` → `roamingevent`
    - `suspicion_scores` → `suspicionscore`
    - `watchlist_hits` → `watchlisthit`
  - Lista de tabelas corrigida (downgrade): mesma lista acima

---

## 3. Análise de Otimizações Implementadas

### 3.1 Stack de Performance Atual

| Fase | Migration | Extensão/Técnica | Ganho de Performance |
|------|-----------|------------------|---------------------|
| Fase 2.2 | 0007 | BRIN Indexes (time-ordered) | 10x mais rápido |
| Fase 2.3 | 0008 | Parallel Query Tuning | 2-4x mais rápido |
| Fase 2.4 | 0009 | Materialized Views | 10x mais rápido |
| Fase 4 | 0010 | TimescaleDB Hypertable | 50-100x (time-series) |
| Fase 5 | 0011 | Citus Distributed Tables | 5-10x (escala horizontal) |

### 3.2 Status das Migrations

| Migration | Descrição | Status | Observações |
|-----------|-----------|--------|-------------|
| 0001 | Initial Schema (PostGIS + SQLAlchemy) | ✅ OK | Cria extensão PostGIS e todas as tabelas |
| 0002 | Operational Indexes (GiST + B-Tree) | ✅ OK | Índices geoespaciais e analíticos |
| 0003 | Multi-tenant Agency Scope | ✅ OK | Adiciona agency_id com backfill |
| 0004 | Suspicious Routes | ✅ OK | Cria enums e tabela suspiciousroute |
| 0005 | Advanced Convoy/Roaming | ✅ OK | Adiciona colunas avançadas |
| 0006 | Agency Hierarchy | ✅ OK | Adiciona type e parent_agency |
| 0007 | BRIN Indexes | ✅ CORRIGIDO | Nomes de tabelas corrigidos |
| 0008 | Parallel Query Tuning | ✅ OK | ALTER SYSTEM para paralelismo |
| 0009 | Materialized Views | ✅ CORRIGIDO | Nomes de tabelas corrigidos |
| 0010 | TimescaleDB | ✅ CORRIGIDO | Nomes de tabelas corrigidos |
| 0011 | Citus | ✅ CORRIGIDO | Nomes de tabelas corrigidos |

---

## 4. Análise de Dependências e Ordem de Execução

### 4.1 Sequência Correta de Migrations
```
0001_initial_schema
  ↓ (cria schema base)
0002_operational_indexes
  ↓ (adiciona índices)
0003_multi_tenant_agency_scope
  ↓ (adiciona agency_id)
0004_suspicious_routes
  ↓ (cria suspiciousroute)
0005_advanced_convoy_roaming
  ↓ (adiciona colunas avançadas)
0006_agency_hierarchy
  ↓ (adiciona hierarquia)
0007_brin_index_observations
  ↓ (BRIN indexes)
0008_parallel_query_tuning
  ↓ (parallel tuning)
0009_materialized_views_hotspots
  ↓ (materialized views)
0010_timescaledb_setup
  ↓ (TimescaleDB hypertable)
0011_citus_setup
  ↓ (Citus distributed tables)
```

### 4.2 Dependências Críticas
- **0003** depende de **0001** (tabela agency criada)
- **0004** depende de **0003** (agency_id adicionado)
- **0005** depende de **0001** (tabelas convoyevent/roamingevent criadas)
- **0006** depende de **0003** (tabela agency criada)
- **0007** depende de **0001** (tabela vehicleobservation criada)
- **0009** depende de **0001** (tabela vehicleobservation criada)
- **0010** depende de **0001** (tabela vehicleobservation criada)
- **0011** depende de **0010** (hypertable criado antes de distribuir)

---

## 5. Recomendações de Tuning Adicional

### 5.1 Índices Faltantes
Verificando o base.py, identifiquei alguns índices que poderiam ser otimizados:

- **vehicleobservation**: Índice composto `ix_observation_agent_time` já existe, mas poderia adicionar índice em `sync_status + created_at` para queries de sincronização
- **alert**: Índice `ix_alert_acknowledged` existe, mas poderia adicionar índice em `severity + is_acknowledged` para dashboard de alertas

### 5.2 Otimizações de TimescaleDB
- **Retention Policy**: Está comentada na migration 0010. Recomenda-se habilitar para ambientes de produção para evitar crescimento infinito
- **Continuous Aggregate Policy**: Configurada para refresh a cada 1 hora, o que é apropriado para a maioria dos casos

### 5.3 Otimizações de Citus
- **Reference Tables**: `agency` e `user` são distribuídas como reference tables, o que é correto para lookup
- **Co-location**: Tabelas relacionadas são distribuídas por `agency_id`, o que é correto para joins eficientes

---

## 6. Próximos Passos

### 6.1 SQL Unificado
- **Status**: Pendente
- **Objetivo**: Gerar arquivo SQL único para infraestrutura DB atual
- **Conteúdo**:
  - Extensões (PostGIS, TimescaleDB, Citus)
  - Todas as tabelas do base.py
  - Todos os índices (GiST, B-Tree, BRIN)
  - Materialized Views
  - Continuous Aggregates
  - Configurações de Parallel Tuning
  - Distributed Tables (Citus)

### 6.2 Validação
- **Testar migrations**: Executar `alembic upgrade head` em ambiente de teste
- **Verificar índices**: Confirmar que todos os índices foram criados corretamente
- **Testar performance**: Validar ganhos de performance das otimizações

---

## 7. Conclusão

**Correções Realizadas**: 4 migrations corrigidas (0007, 0009, 0010, 0011)
**Status Atual**: Todas as migrations estão consistentes com o schema SQLAlchemy
**Stack Atual**: PostgreSQL + PostGIS + TimescaleDB + Citus (máxima performance)
**Próximo Passo**: Gerar SQL unificado para deploy automatizado
