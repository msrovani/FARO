# F.A.R.O. - Implementação de Funcionalidades Avançadas

## Documentação de Implementação - Fase 1

**Data:** 14/04/2026
**Status:** Alta Prioridade Concluída

---

## 1. Cadastro de Rotas Suspeitas (Manual Route Registration)

### 1.1 Modelo de Dados

**Arquivo:** `server-core/app/db/base.py`

**Enums Criados:**
- `CrimeType`: drug_trafficking, contraband, escape, weapons_trafficking, kidnapping, car_theft, stolen_vehicle, gang_activity, human_trafficking, money_laundering, other
- `RouteDirection`: inbound, outbound, bidirectional
- `RiskLevel`: low, medium, high, critical

**Modelo `SuspiciousRoute`:**
```python
- agency_id: UUID (FK agency)
- name: String(255)
- crime_type: Enum(CrimeType)
- direction: Enum(RouteDirection)
- risk_level: Enum(RiskLevel)
- route_geometry: Geometry(LINESTRING, SRID=4326)
- buffer_distance_meters: Float (opcional)
- active_from_hour: Integer (0-23, opcional)
- active_to_hour: Integer (0-23, opcional)
- active_days: Array(Integer) (0=Monday, 6=Sunday, opcional)
- justification: Text (opcional)
- created_by: UUID (FK user)
- approved_by: UUID (FK user, opcional)
- approval_status: String (pending/approved/rejected)
- is_active: Boolean
```

**Índices:**
- ix_suspicious_route_agency_id
- ix_suspicious_route_name
- ix_suspicious_route_agency_active (composto)
- ix_suspicious_route_crime_type
- ix_suspiciousroute_route_geometry (GiST para queries espaciais)

### 1.2 Schemas Pydantic

**Arquivo:** `server-core/app/schemas/suspicious_route.py`

- `SuspiciousRouteCreate`: Criação de rota (route_points como array de GeolocationPoint)
- `SuspiciousRouteUpdate`: Atualização de rota
- `SuspiciousRouteResponse`: Resposta com todos os campos
- `SuspiciousRouteMatchRequest`: Verificação de match (observation_id, plate_number, location, observed_at)
- `SuspiciousRouteMatchResponse`: Resultado do match (matches, matched_routes, distance_meters, alert_triggered)
- `SuspiciousRouteListResponse`: Listagem com paginação
- `RouteApprovalRequest`: Aprovação/rejeição (approval_status, justification)

### 1.3 Serviço de Negócio

**Arquivo:** `server-core/app/services/suspicious_route_service.py`

**Funções:**
- `create_suspicious_route`: Cria rota com conversão de pontos para LINESTRING PostGIS
- `get_suspicious_route`: Busca rota por ID
- `list_suspicious_routes`: Lista com filtros (crime_type, risk_level, approval_status, is_active)
- `update_suspicious_route`: Atualiza rota (inclui geometria)
- `delete_suspicious_route`: Soft delete (is_active = False)
- `check_route_match`: Verifica se observação intersecta rota usando PostGIS
  - ST_Intersects para interseção direta
  - ST_Buffer + ST_Distance para proximidade
  - Verifica restrições temporais (horário e dias)
- `approve_route`: Aprova/rejeita rota
- `route_to_response`: Converte modelo para schema

### 1.4 API Endpoints

**Arquivo:** `server-core/app/api/v1/endpoints/suspicious_routes.py`

**Endpoints:**
- `POST /intelligence/suspicious-routes`: Criar rota
- `GET /intelligence/suspicious-routes`: Listar rotas (query params: crime_type, risk_level, approval_status, is_active, page, page_size)
- `GET /intelligence/suspicious-routes/{route_id}`: Detalhes da rota
- `PUT /intelligence/suspicious-routes/{route_id}`: Atualizar rota
- `DELETE /intelligence/suspicious-routes/{route_id}`: Desativar rota
- `POST /intelligence/suspicious-routes/{route_id}/approve`: Aprovar/rejeitar rota
- `POST /intelligence/suspicious-routes/match`: Verificar match de observação

**Registro:** `server-core/app/api/routes.py`

### 1.5 Migration

**Arquivo:** `server-core/alembic/versions/0004_suspicious_routes.py`

**Conteúdo:**
- Cria tipos enum (crimetype, routedirection, risklevel)
- Cria tabela suspiciousroute com todas as colunas
- Cria índices (incluindo GiST em route_geometry)
- Downgrade remove tudo na ordem inversa

---

## 2. Análise de Hotspots de Criminalidade

### 2.1 Serviço de Análise

**Arquivo:** `server-core/app/services/hotspot_analysis_service.py`

**Data Classes:**
- `HotspotPoint`: latitude, longitude, observation_count, suspicion_count, unique_plates, radius_meters, intensity_score
- `HotspotAnalysisResult`: hotspots, total_observations, total_suspicions, analysis_period_days, cluster_radius_meters, min_points_per_cluster

**Funções:**
- `analyze_hotspots`: 
  - Agrupa observações por proximidade espacial (clustering simplificado)
  - Calcula centroides e estatísticas por cluster
  - Calcula intensity_score (0-1) baseado em densidade e suspeitas
  - Retorna top 20 hotspots ordenados por intensidade
  
- `get_hotspot_timeline`:
  - Distribuição temporal de observações em área específica
  - Usa ST_DWithin do PostGIS para busca espacial
  - Retorna dados horários e padrão diário (24 horas)
  - Identifica hora de pico
  
- `get_hotspot_plates`:
  - Placas mais frequentes em área específica
  - Usa ST_DWithin do PostGIS
  - Retorna contagem, primeira e última observação por placa

### 2.2 Schemas Pydantic

**Arquivo:** `server-core/app/schemas/hotspot.py`

- `HotspotPointResponse`: Ponto de hotspot
- `HotspotAnalysisRequest`: Parâmetros de análise (start_date, end_date, cluster_radius_meters, min_points_per_cluster)
- `HotspotAnalysisResponse`: Resultado da análise
- `HotspotTimelineRequest`: Parâmetros de timeline (latitude, longitude, radius_meters, days)
- `HotspotTimelineResponse`: Resultado do timeline (hourly_data, daily_pattern, total_observations, peak_hour)
- `HotspotPlatesRequest`: Parâmetros de placas (latitude, longitude, radius_meters, limit)
- `HotspotPlateEntry`: Entrada de placa
- `HotspotPlatesResponse`: Lista de placas

### 2.3 API Endpoints

**Arquivo:** `server-core/app/api/v1/endpoints/hotspots.py`

**Endpoints:**
- `POST /intelligence/hotspots/analyze`: Analisar hotspots
- `POST /intelligence/hotspots/timeline`: Timeline de área
- `POST /intelligence/hotspots/plates`: Placas em área

**Registro:** `server-core/app/api/routes.py`

---

## 3. Explicabilidade de SuspicionScore

**Status:** Já existente no modelo

**Arquivo:** `server-core/app/db/base.py`

**Modelo `SuspicionScore`:**
- `explanation`: Text (explicação geral)
- `false_positive_risk`: String (low/medium/high)

**Modelo `SuspicionScoreFactor`:**
- `factor_name`: Nome do fator
- `factor_source`: Fonte do fator (watchlist, impossible_travel, etc.)
- `weight`: Peso do fator
- `contribution`: Contribuição ao score final
- `explanation`: Explicação específica do fator
- `direction`: positive/negative

---

## 4. Integração PostGIS

### 4.1 Operações Espaciais Implementadas

**SuspiciousRoute:**
- ST_Intersects: Verifica se observação intersecta rota
- ST_Distance: Calcula distância entre observação e rota
- ST_Buffer: Cria zona de alerta ao redor da rota

**Hotspots:**
- ST_DWithin: Busca observações dentro de raio específico
- ST_SetSRID + ST_MakePoint: Cria ponto geográfico

### 4.2 Índices Espaciais

- GiST index em suspiciousroute.route_geometry
- Habilita queries espaciais eficientes

---

## 5. Governança e Auditabilidade

### 5.1 Audit Logs

**Arquivo:** `server-core/app/services/audit_service.py`

**Função `log_audit_event`:**
- Registra ações em SuspiciousRoute (create, update, delete, approve)
- Inclui: actor, action, resource_type, resource_id, details, justification

**Uso em endpoints:**
- create_suspicious_route
- update_suspicious_route
- delete_suspicious_route
- approve_route
- suspicious_route_alert (quando match aciona alerta)

---

## 6. Multi-Tenancy

### 6.1 Escopo por Agência

**SuspiciousRoute:**
- agency_id obrigatório
- Queries filtram por agency_id do usuário
- Índice composto (agency_id, is_active)

**Hotspots:**
- Queries filtram por agency_id do usuário

---

## 7. Aprovação de Rotas

### 7.1 Workflow

1. Analista cria rota (approval_status = "pending")
2. Supervisor aprova ou rejeita (approval_status = "approved"/"rejected")
3. Apenas rotas aprovadas são usadas em match checking

### 7.2 Campos de Governança

- `created_by`: Quem criou
- `approved_by`: Quem aprovou
- `approval_status`: pending/approved/rejected
- `justification`: Justificativa de criação ou aprovação

---

## 8. Frontend - Visualizações de Mapa para Inteligência Policial

### 8.1 Componentes de Mapa

**Arquivo:** `web-intelligence-console/src/app/components/map/MapBase.tsx`

**Funcionalidades:**
- Componente base usando react-map-gl com OpenStreetMap
- Controles de navegação (zoom, pan)
- Controle de escala
- Controle de geolocalização
- Controle de tela cheia
- Tema escuro configurado
- Configuração inicial de view (latitude, longitude, zoom)

**Arquivo:** `web-intelligence-console/src/app/components/map/HotspotMarker.tsx`

**Funcionalidades:**
- Marcadores circulares para hotspots
- Tamanho dinâmico baseado no número de observações
- Coloração baseada no score de intensidade (verde a vermelho)
- Popup com detalhes: localização, observações, suspeitas, placas únicas, intensidade
- Ícone de MapPin do lucide-react

**Arquivo:** `web-intelligence-console/src/app/components/RouteMarker.tsx`

**Funcionalidades:**
- Renderização de linhas para rotas suspeitas
- Marcadores de início e fim
- Pontos editáveis clicáveis no mapa
- Popup com detalhes: nome, tipo de crime, direção, nível de risco, justificativa
- Suporte para criar novas rotas via cliques
- Ícones de MapPin e Route do lucide-react

**Arquivo:** `web-intelligence-console/src/app/components/AlertMarker.tsx`

**Funcionalidades:**
- Marcadores para alertas com ícones por tipo
- Coloração por severidade (critical, high, medium, low)
- Popup com detalhes: tipo, severidade, descrição, placa, localização
- Ícones de AlertTriangle, Shield, Clock, MapPin do lucide-react

### 8.2 Páginas de Visualização

**Arquivo:** `web-intelligence-console/src/app/hotspots/page.tsx`

**Funcionalidades:**
- Visualização de hotspots de criminalidade no mapa
- Filtros: raio de cluster, pontos mínimos, período de análise
- Estatísticas: total de observações, total de suspeitas, hotspots identificados
- Lista lateral de hotspots com preview
- Painel de detalhes para hotspot selecionado
- Timeline de atividade por hora do dia
- Placas mais frequentes na área
- Mock data pronto para integração com API backend

**Arquivo:** `web-intelligence-console/src/app/suspicious-routes/page.tsx`

**Funcionalidades:**
- Visualização e cadastro de rotas suspeitas
- Criação de rotas via cliques no mapa
- Filtros: tipo de crime, nível de risco, status de aprovação
- Lista lateral de rotas com preview
- Painel de detalhes para rota selecionada
- Ações: aprovar, rejeitar, editar, desativar
- Formulário de criação/edição com todos os campos
- Mock data pronto para integração com API backend

**Arquivo:** `web-intelligence-console/src/app/route-prediction/page.tsx`

**Funcionalidades:**
- Previsão de rotas baseada em padrões históricos
- Input de número de placa e dias à frente
- Visualização de corridor previsto no mapa (polylines)
- Exibição de confiança da predição
- Horas previstas de atividade
- Dias previstas de atividade
- Força do padrão detectado
- Mock data com simulação de API call
- Pronto para integração com endpoint `/intelligence/route-prediction`

**Arquivo:** `web-intelligence-console/src/app/alerts/page.tsx`

**Funcionalidades:**
- Visualização de alertas no mapa
- Filtros: tipo de alerta, severidade, status de revisão
- Estatísticas: total, críticos, altos, pendentes
- Lista lateral de alertas com preview
- Painel de detalhes para alerta selecionado
- Ações: aprovar, dispensar alerta
- Coloração por severidade e tipo
- Mock data pronto para integração com API backend

**Arquivo:** `web-intelligence-console/src/app/convoy-events/page.tsx`

**Funcionalidades:**
- Visualização de eventos de convoy
- Filtros: decisão, severidade, mínimo de coocorrências
- Estatísticas: total, confirmados, pendentes, rejeitados
- Lista lateral de eventos com preview
- Painel de detalhes com: placas primária e relacionada, coocorrências, confiança, severidade
- Ações: aprovar, rejeitar evento
- Marcadores coloridos por decisão (verde=confirmado, amarelo=pendente, vermelho=rejeitado)
- Mock data pronto para integração com API backend

**Arquivo:** `web-intelligence-console/src/app/roaming-events/page.tsx`

**Funcionalidades:**
- Visualização de eventos de roaming
- Filtros: decisão, severidade, mínimo de recorrências
- Estatísticas: total, confirmados, pendentes, rejeitados
- Lista lateral de eventos com preview
- Painel de detalhes com: placa, área, recorrências, confiança, severidade
- Ações: aprovar, rejeitar evento
- Marcadores coloridos por decisão
- Mock data pronto para integração com API backend

### 8.3 Design e UX

**Características Comuns:**
- Layout split-screen (sidebar + mapa)
- Tema escuro consistente (bg-gray-900, bg-gray-800, bg-gray-700)
- Ícones lucide-react para UI e marcadores
- Responsivo e interativo
- Feedback visual para seleção e ações
- Cards com sombras e bordas arredondadas
- Cores semânticas (verde=sucesso, amarelo=pendente, vermelho=erro/crítico)

**Padrão de Componentes:**
- Sidebar esquerda com filtros e lista
- Mapa principal à direita com marcadores
- Painel flutuante inferior direito para detalhes
- Resumo estatístico no topo da sidebar
- Filtros expansíveis

### 8.4 Integração com Backend

**Endpoints Mapeados:**
- Hotspots → `/intelligence/hotspots/analyze`, `/intelligence/hotspots/timeline`, `/intelligence/hotspots/plates`
- Rotas Suspeitas → `/intelligence/suspicious-routes`
- Previsão de Rotas → `/intelligence/route-prediction`
- Alertas → `/intelligence/alerts`
- Convoy Events → Endpoint a ser criado
- Roaming Events → Endpoint a ser criado

**Status de Integração:**
- Mock data implementado em todas as páginas
- Estrutura de dados alinhada com schemas Pydantic
- Pronto para substituir mock por chamadas reais de API
- Timeout de 1 segundo para simular loading

### 8.5 Dependências

**Instaladas:**
- maplibre-gl
- react-map-gl
- lucide-react

**Nota:** Erros de lint TypeScript devido a dependências não instaladas são esperados no ambiente de desenvolvimento. Executar `npm install` no diretório `web-intelligence-console` resolve.

---

## Próximos Passos (Pendente)

### Média Prioridade
- Criar endpoints para ConvoyEvents e RoamingEvents no backend
- Integrar frontend com endpoints reais (substituir mock data)
- Implementar autenticação e autorização no frontend

### Baixa Prioridade
- Criar dashboard consolidado de inteligência
- Criar relatórios de impacto e precisão
- Adicionar exportação de dados (PDF, CSV)
- Implementar notificações em tempo real

---

## Instruções para Deploy

### 1. Executar Migration
```bash
cd server-core
alembic upgrade head
```

### 2. Verificar Índices Espaciais
```sql
-- Verificar índice GiST
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'suspiciousroute';
```

### 3. Testar Endpoints
- Criar rota suspeita
- Aprovar rota
- Verificar match de observação
- Analisar hotspots

---

## Arquivos Criados/Modificados

### Novos Arquivos (Backend)
- `server-core/app/schemas/suspicious_route.py`
- `server-core/app/services/suspicious_route_service.py`
- `server-core/app/api/v1/endpoints/suspicious_routes.py`
- `server-core/app/schemas/hotspot.py`
- `server-core/app/services/hotspot_analysis_service.py`
- `server-core/app/api/v1/endpoints/hotspots.py`
- `server-core/alembic/versions/0004_suspicious_routes.py`
- `server-core/app/services/route_prediction_service.py`
- `server-core/app/services/alert_service.py`
- `server-core/app/schemas/route_prediction.py`
- `server-core/app/schemas/alerts.py`
- `server-core/app/api/v1/endpoints/route_prediction.py`
- `server-core/app/api/v1/endpoints/alerts.py`
- `server-core/alembic/versions/0005_advanced_convoy_roaming.py`
- `docs/implementation/advanced-features-implementation.md`
- `docs/implementation/complete-implementation-report.md`

### Novos Arquivos (Frontend)
- `web-intelligence-console/src/app/components/map/MapBase.tsx`
- `web-intelligence-console/src/app/components/map/HotspotMarker.tsx`
- `web-intelligence-console/src/app/components/RouteMarker.tsx`
- `web-intelligence-console/src/app/components/AlertMarker.tsx`
- `web-intelligence-console/src/app/hotspots/page.tsx`
- `web-intelligence-console/src/app/suspicious-routes/page.tsx`
- `web-intelligence-console/src/app/route-prediction/page.tsx`
- `web-intelligence-console/src/app/alerts/page.tsx`
- `web-intelligence-console/src/app/convoy-events/page.tsx`
- `web-intelligence-console/src/app/roaming-events/page.tsx`

### Arquivos Modificados
- `server-core/app/db/base.py` (enums + modelo SuspiciousRoute + ConvoyEvent expandido + RoamingEvent expandido)
- `server-core/app/api/routes.py` (registro de routers: suspicious_routes, hotspots, route_prediction, alerts)
