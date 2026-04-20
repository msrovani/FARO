# Contratos de Backend - Módulos Estratégicos FARO

## Visão Geral

Este documento descreve os contratos de backend para os três módulos estratégicos do FARO:
1. Cadastro independente de veículo suspeito (Watchlist)
2. Watchlist operacional
3. Casos e dossiês

---

## 1. Cadastro Independente de Veículo Suspeito (WatchlistEntry)

### Model: `WatchlistEntry`

**Localização:** `server-core/app/db/base.py`

**Campos principais:**
- `id`: UUID - Identificador único
- `agency_id`: UUID - Agência proprietária
- `created_by`: UUID - Usuário que criou
- `status`: WatchlistStatus - ACTIVE, INACTIVE, ARCHIVED
- `category`: WatchlistCategory - STOLEN, SUSPICIOUS, WANTED, MONITORING
- `plate_number`: String(20) - Placa completa
- `plate_partial`: String(20) - Placa parcial
- `vehicle_make`: String(100) - Marca do veículo
- `vehicle_model`: String(100) - Modelo do veículo
- `vehicle_color`: String(50) - Cor do veículo
- `visual_traits`: Text - Características visuais
- `interest_reason`: Text - Motivo do interesse (obrigatório)
- `information_source`: String(255) - Fonte da informação
- `sensitivity_level`: String(50) - Nível de sigilo (padrão: "reserved")
- `confidence_level`: String(50) - Nível de confiança
- `geographic_scope`: String(255) - Escopo geográfico
- `active_time_window`: String(255) - Janela temporal ativa
- `priority`: Integer - Prioridade (1-100, padrão: 50)
- `recommended_action`: String(255) - Ação recomendada
- `silent_mode`: Boolean - Modo silencioso (padrão: false)
- `notes`: Text - Notas adicionais
- `valid_from`: DateTime - Início da validade
- `valid_until`: DateTime - Fim da validade
- `review_due_at`: DateTime - Data de revisão
- `metadata_json`: JSON - Metadados adicionais

### Schemas

**Localização:** `server-core/app/schemas/watchlist.py`

#### `WatchlistEntryCreate`
```python
{
    "status": WatchlistStatus.ACTIVE,
    "category": WatchlistCategory,
    "plate_number": Optional[str],
    "plate_partial": Optional[str],
    "vehicle_make": Optional[str],
    "vehicle_model": Optional[str],
    "vehicle_color": Optional[str],
    "visual_traits": Optional[str],
    "interest_reason": str,  # obrigatório, 5-4000 caracteres
    "information_source": Optional[str],
    "sensitivity_level": str = "reserved",
    "confidence_level": Optional[str],
    "geographic_scope": Optional[str],
    "active_time_window": Optional[str],
    "priority": int = 50,  # 1-100
    "recommended_action": Optional[str],
    "silent_mode": bool = False,
    "notes": Optional[str],
    "valid_from": Optional[datetime],
    "valid_until": Optional[datetime],
    "review_due_at": Optional[datetime],
    "metadata_json": Optional[Dict[str, Any]]
}
```

#### `WatchlistEntryUpdate`
Todos os campos são opcionais, mesmo esquema do Create.

#### `WatchlistEntryResponse`
```python
{
    "id": UUID,
    "created_by": UUID,
    "created_by_name": Optional[str],
    "status": WatchlistStatus,
    "category": WatchlistCategory,
    # ... todos os campos do Create ...
    "created_at": datetime,
    "updated_at": datetime
}
```

### Endpoints

**Localização:** `server-core/app/api/v1/endpoints/intelligence.py`

#### `GET /api/v1/watchlist` ou `/api/v1/watchlists`
- **Descrição:** Lista entradas de watchlist
- **Query params:**
  - `status`: WatchlistStatus (opcional)
- **Response:** `list[WatchlistEntryResponse]`
- **RBAC:** `require_intelligence_role`

#### `POST /api/v1/watchlist` ou `/api/v1/watchlists`
- **Descrição:** Cria nova entrada de watchlist
- **Body:** `WatchlistEntryCreate`
- **Response:** `WatchlistEntryResponse`
- **RBAC:** `require_intelligence_role`

#### `PATCH /api/v1/watchlist/{entry_id}` ou `/api/v1/watchlists/{entry_id}`
- **Descrição:** Atualiza entrada de watchlist
- **Body:** `WatchlistEntryUpdate`
- **Response:** `WatchlistEntryResponse`
- **RBAC:** `require_intelligence_role`

#### `DELETE /api/v1/watchlist/{entry_id}` ou `/api/v1/watchlists/{entry_id}`
- **Descrição:** Remove entrada de watchlist
- **Response:** `{"message": "Cadastro de watchlist excluído com sucesso"}`
- **RBAC:** `require_intelligence_role`

---

## 2. Watchlist Operacional

### Funcionalidades

O módulo de watchlist operacional utiliza o mesmo `WatchlistEntry` model, com foco em:

- **Regras editáveis:** Campos `geographic_scope`, `active_time_window`, `priority`
- **Janela temporal:** `valid_from`, `valid_until`, `active_time_window`
- **Área geográfica:** `geographic_scope`
- **Orientação de abordagem:** `recommended_action`, `silent_mode`

### Fluxo Operacional

1. **Criação:** Inteligência cria entrada com regras específicas
2. **Monitoramento:** Sistema verifica observações contra watchlist em tempo real
3. **Alerta:** Quando há match, gera `WatchlistHit` com decisão e severidade
4. **Abordagem:** Campo `silent_mode` controla se alerta é silencioso
5. **Revisão:** Analista pode atualizar prioridade, validade, ações recomendadas

### Tipos de Categoria

- `STOLEN`: Veículo roubado
- `SUSPICIOUS`: Veículo suspeito
- `WANTED`: Veículo procurado
- `MONITORING`: Monitoramento contínuo

---

## 3. Casos e Dossiês

### Model: `IntelligenceCase`

**Localização:** `server-core/app/db/base.py`

**Campos principais:**
- `id`: UUID - Identificador único
- `agency_id`: UUID - Agência proprietária
- `created_by`: UUID - Usuário que criou
- `title`: String(255) - Título do caso (obrigatório)
- `hypothesis`: Text - Hipótese analítica
- `summary`: Text - Resumo do caso
- `status`: CaseStatus - OPEN, MONITORING, ESCALATED, CLOSED
- `sensitivity_level`: String(50) - Nível de sigilo (padrão: "reserved")
- `priority`: Integer - Prioridade (1-100, padrão: 50)
- `review_due_at`: DateTime - Data de revisão

### Model: `CaseLink`

**Localização:** `server-core/app/db/base.py`

**Campos principais:**
- `id`: UUID - Identificador único
- `case_id`: UUID - ID do caso (FK para IntelligenceCase)
- `link_type`: CaseLinkType - Tipo de vínculo
- `linked_entity_id`: UUID - ID da entidade vinculada
- `linked_label`: String(255) - Rótulo descritivo
- `created_by`: UUID - Usuário que criou

### Tipos de Vínculo (CaseLinkType)

- `OBSERVATION`: Vincula observação de veículo
- `WATCHLIST`: Vincula entrada de watchlist
- `SCORE`: Vincula score de suspeição
- `OCCURRENCE`: Vincula ocorrência registrada
- `VEHICLE`: Vincula veículo

### Schemas

**Localização:** `server-core/app/schemas/analytics.py`

#### `IntelligenceCaseCreate`
```python
{
    "title": str,  # obrigatório, 5-255 caracteres
    "hypothesis": Optional[str],
    "summary": Optional[str],
    "status": CaseStatus = CaseStatus.OPEN,
    "sensitivity_level": str = "reserved",
    "priority": int = 50,  # 1-100
    "review_due_at": Optional[datetime]
}
```

#### `IntelligenceCaseUpdate`
Todos os campos são opcionais, mesmo esquema do Create.

#### `IntelligenceCaseResponse`
```python
{
    "id": UUID,
    "title": str,
    "hypothesis": Optional[str],
    "summary": Optional[str],
    "status": CaseStatus,
    "sensitivity_level": str,
    "priority": int,
    "review_due_at": Optional[datetime],
    "created_by": UUID,
    "created_by_name": Optional[str],
    "created_at": datetime,
    "updated_at": datetime
}
```

#### `CaseLinkCreate`
```python
{
    "link_type": CaseLinkType,
    "linked_entity_id": UUID,
    "linked_label": Optional[str]
}
```

#### `CaseLinkResponse`
```python
{
    "id": UUID,
    "case_id": UUID,
    "link_type": CaseLinkType,
    "linked_entity_id": UUID,
    "linked_label": Optional[str],
    "created_by": UUID,
    "created_by_name": Optional[str],
    "created_at": datetime
}
```

### Endpoints

**Localização:** `server-core/app/api/v1/endpoints/intelligence.py`

#### `GET /api/v1/cases`
- **Descrição:** Lista casos analíticos
- **Query params:**
  - `status`: CaseStatus (opcional)
  - `search`: str (opcional) - busca em título, hipótese, resumo
  - `offset`: int (padrão: 0)
  - `limit`: int (padrão: 50)
- **Response:** `list[IntelligenceCaseResponse]`
- **RBAC:** `require_intelligence_role`

#### `POST /api/v1/cases`
- **Descrição:** Cria novo caso analítico
- **Body:** `IntelligenceCaseCreate`
- **Response:** `IntelligenceCaseResponse`
- **RBAC:** `require_intelligence_role`

#### `GET /api/v1/cases/{case_id}`
- **Descrição:** Obtém detalhes de um caso
- **Response:** `IntelligenceCaseResponse`
- **RBAC:** `require_intelligence_role`

#### `PATCH /api/v1/cases/{case_id}`
- **Descrição:** Atualiza caso analítico
- **Body:** `IntelligenceCaseUpdate`
- **Response:** `IntelligenceCaseResponse`
- **RBAC:** `require_intelligence_role`

#### `DELETE /api/v1/cases/{case_id}`
- **Descrição:** Remove caso analítico
- **Response:** `{"message": "Caso analitico excluído com sucesso"}`
- **RBAC:** `require_intelligence_role`

#### `GET /api/v1/cases/{case_id}/links`
- **Descrição:** Lista vínculos do caso
- **Query params:**
  - `link_type`: CaseLinkType (opcional)
- **Response:** `list[CaseLinkResponse]`
- **RBAC:** `require_intelligence_role`

#### `POST /api/v1/cases/{case_id}/links`
- **Descrição:** Adiciona vínculo ao caso
- **Body:** `CaseLinkCreate`
- **Response:** `CaseLinkResponse`
- **RBAC:** `require_intelligence_role`

#### `DELETE /api/v1/cases/{case_id}/links/{link_id}`
- **Descrição:** Remove vínculo do caso
- **Response:** `{"message": "Vinculo de caso removido com sucesso"}`
- **RBAC:** `require_intelligence_role`

---

## Integração com Frontend

### Web Intelligence Console

O frontend deve implementar:

1. **Watchlist Management:**
   - Tabela de entradas com filtros por status e categoria
   - Formulário de criação/edição com todos os campos
   - Visualização de prioridade com indicadores visuais
   - Indicadores de validade temporal (valid_from/valid_until)
   - Modo silencioso com destaque visual

2. **Case Management:**
   - Lista de casos com busca e filtros
   - Detalhes do caso com todos os campos
   - Gerenciamento de vínculos (add/remove)
   - Visualização de entidades vinculadas por tipo
   - Timeline de evolução do caso

3. **Case Linking:**
   - Interface para vincular observações, watchlists, scores, ocorrências, veículos
   - Visualização de vínculos por tipo
   - Busca de entidades para vincular
   - Rótulos descritivos para vínculos

### RBAC e Escopo

Todos os endpoints utilizam:
- `require_intelligence_role` - Requer papel de inteligência
- `scoped_query` - Filtra por agência com suporte a hierarquia

### Auditoria

Todas as operações são auditadas via `log_audit_event`:
- Ações: `watchlist_created`, `watchlist_updated`, `watchlist_deleted`
- Ações: `intelligence_case_created`, `intelligence_case_updated`, `intelligence_case_deleted`
- Ações: `case_link_created`, `case_link_deleted`

### Event Bus

- `intelligence_case_created` publicado quando caso é criado
- Payload inclui: case_id, created_by, status

---

## Exemplos de Uso

### Criar entrada de watchlist

```bash
POST /api/v1/watchlist
{
    "category": "STOLEN",
    "plate_number": "ABC1234",
    "vehicle_make": "Toyota",
    "vehicle_model": "Corolla",
    "vehicle_color": "Preto",
    "interest_reason": "Veículo reportado como roubado",
    "sensitivity_level": "confidential",
    "priority": 90,
    "geographic_scope": "Zona Centro",
    "valid_until": "2026-12-31T23:59:59Z",
    "recommended_action": "Abordagem imediata com cautela"
}
```

### Criar caso analítico

```bash
POST /api/v1/cases
{
    "title": "Investigação Roubo Veículos Zona Centro",
    "hypothesis": "Padrão de roubos em veículos da marca Toyota",
    "status": "OPEN",
    "priority": 80,
    "review_due_at": "2026-05-01T10:00:00Z"
}
```

### Vincular observação ao caso

```bash
POST /api/v1/cases/{case_id}/links
{
    "link_type": "OBSERVATION",
    "linked_entity_id": "uuid-da-observacao",
    "linked_label": "Observação principal - ABC1234"
}
```

---

## Próximos Passos

1. Implementar UI no Web Intelligence Console para os três módulos
2. Adicionar validações de negócio (ex: valid_until > valid_from)
3. Implementar notificações para revisões pendentes
4. Adicionar relatórios e exportação de dados
5. Implementar busca avançada com filtros compostos
6. Adicionar permissões granulares por nível de sigilo
