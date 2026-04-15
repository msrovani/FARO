# F.A.R.O. - Memoria tecnica consolidada

## 1. Identidade do produto

- Nome: `F.A.R.O.`
- Expansao: `Ferramenta de Analise de Rotas e Observacoes`
- Escopo: plataforma integrada de abordagem veicular, inteligencia operacional e protecao do ativo
- Arquitetura obrigatoria: 3 componentes separados
  - `mobile-agent-field`
  - `web-intelligence-console`
  - `server-core`

## 2. Principios de engenharia

- offline-first no mobile
- OCR assistido (humano confirma)
- backend ativo e explicavel
- inteligencia humana no loop
- auditoria e governanca desde o desenho
- nada de mock como entrega final

## 3. Estado real por componente

### 3.1 Mobile (agente de campo)

Implementado:

- autenticacao real (`login/refresh/logout`) conectada ao backend
- sessao persistida em DataStore com perfis compartimentados por usuario no mesmo dispositivo
- interceptor HTTP com token dinamico (sem token fixo em build)
- sync em lote com consumo de `pending_feedback`
- inbox local de feedback e marcacao local como lido
- upload de assets (imagem/audio) no fluxo de sync apos observacao confirmada
- viewmodels para auth, home e historico
- telas conectadas ao fluxo real de sessao/feedback
- alternancia de perfil salvo no login para celular compartilhado em patrulha
- ARQUITETURA ZERO-TRUST: dados criptografados em repouso (AES-256 + Android Keystore)
- compressao de imagens para resolucao auditavel (800x600 max, qualidade 85%)
- eliminacao segura pos-sync (DoD 5220.22-M wipe standard)
- TTL automatico (7 dias) com auto-destruicao de dados nao sincronizados

Pendente prioritario:

- build Android reproduzivel no repositorio (`gradlew` + pipeline)
- validacao automatizada de cenarios offline instaveis em device farm/lab

### 3.2 Web (inteligencia)

Implementado:

- dashboard analitico
- fila analitica com revisao estruturada
- feedback ao campo com templates
- watchlist com monitoramento
- casos/dossies
- rotas
- comboio/coocorrencia
- roaming/loitering
- ativo sensivel
- auditoria
- **visualizacoes de mapa para inteligencia policial**:
  - componente base de mapa OpenStreetMap (react-map-gl)
  - marcadores para hotspots, rotas suspeitas e alertas
  - pagina de visualizacao de hotspots com filtros e timeline
  - pagina de cadastro/visualizacao de rotas suspeitas
  - pagina de previsao de rotas baseada em padroes historicos
  - pagina de alertas com filtros e acoes de aprovacao
  - pagina de eventos de convoy
  - pagina de eventos de roaming
  - tema escuro consistente com layout split-screen
  - mock data pronto para integracao com backend

Pendente prioritario:

- refinamento de UX para alta densidade
- dashboards de BI institucional (produtividade util por unidade/turno)
- integracao frontend com endpoints reais (substituir mock data)

### 3.3 Backend + banco

Implementado:

- auth JWT com refresh
- observacao mobile com idempotencia por `client_id`
- suspeicao estruturada
- historico mobile
- sync em lote com retorno de feedback pendente consolidado
- endpoint de confirmacao de abordagem
- endpoint de upload de assets para storage S3-compatible
- pipeline de eventos com Redis Streams (publish + worker consume)
- aliases de rota para compatibilidade de clientes
- rate limiting baseline
- migration `0002_operational_indexes` (GiST + indices analiticos)
- base multiagencia com isolamento por `agency_id` em usuario/unidade/dispositivo/observacao/watchlist/casos/feedback/rotas
- escopo de consultas da inteligencia por agencia (admin global preservado)
- **funcionalidades avancadas de analise**:
  - cadastro de rotas suspeitas (SuspiciousRoute) com PostGIS
  - analise de hotspots de criminalidade com clustering espacial
  - previsao de rotas baseada em padroes historicos
  - servico de alertas automaticos para rotas recorrentes
  - expansao de ConvoyEvent com padroes temporais e analise de rotas
  - expansao de RoamingEvent com padroes de area e tracking de recorrencia
- **migrations adicionais**:
  - `0004_suspicious_routes` - tabela SuspiciousRoute com enums e indices espaciais
  - `0005_advanced_convoy_roaming` - expansao de ConvoyEvent e RoamingEvent

Pendente prioritario:

- integracao real com base estadual (hoje fallback dev)
- suites de teste automatizadas de integracao (HTTP + Postgres/PostGIS + Redis)
- criacao de endpoints para ConvoyEvents e RoamingEvents no backend

## 4. Regras de Escopo e Visibilidade por Agencia

### 4.1 Visibilidade de Campo (Agente)
- Agente de campo ve suspeitas de **TODAS** as agencias (visao ampla)
- Consulta de placa (`/mobile/plates/{plate}/check-suspicion`) retorna suspeitas de qualquer origem
- Watchlist acessivel independente de `agency_id`
- Contagem de observacoes previas inclui todas as agencias

### 4.2 Gestao de Inteligencia (Console Web)
- Inteligencia ve apenas dados da sua agencia (`agency_id` isolado)
- Gestao de agentes: apenas agentes da propria agencia (filhos)
- Watchlist: cadastro e gestao por agencia
- Fila analitica: apenas observacoes da propria agencia

### 4.3 Retorno de Abordagem (n+1)
- Abordagem de veiculo ja suspeito: retorna para **agencia de origem** + **cadastrador original**
- Feedback criado com `agency_id` da agencia que cadastrou a suspeita
- Notificacao enviada ao agente original (independente de estar online)

## 5. Fluxo operacional consolidado

1. agente registra observacao no mobile
2. backend persiste e enriquece retorno com contexto operacional
3. agente recebe indicacao imediata e pode confirmar abordagem
4. inteligencia recebe na fila, revisa e classifica
5. inteligencia envia feedback para agente/equipe
6. feedback retorna ao campo no ciclo de sync e historico

## 6. Integracao estadual (status oficial)

Situacao atual:

- adapter desacoplado pronto para integracao real
- fallback de desenvolvimento ativo:
  - `connected: false`
  - `status: "no_connection"`
  - `message: "sem conexao com base estadual"`

Decisao:

- manter fallback explicito ate o conector oficial estar homologado
- nao simular dado falso de veiculo estadual

## 7. Endpoints que suportam o fluxo atual

Auth:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

Mobile:

- `POST /api/v1/mobile/observations`
- `POST /api/v1/mobile/observations/{id}/suspicion`
- `POST /api/v1/mobile/observations/{id}/approach-confirmation`
- `POST /api/v1/mobile/observations/{id}/assets`
- `POST /api/v1/mobile/sync/batch`
- `GET /api/v1/mobile/history`
- `GET /api/v1/mobile/observations/{id}/feedback`
- `GET /api/v1/mobile/plates/{plate}/check-suspicion`

Inteligencia:

- `GET /api/v1/intelligence/queue`
- `GET /api/v1/intelligence/observations/{id}`
- `POST /api/v1/intelligence/reviews`
- `PATCH /api/v1/intelligence/reviews/{id}`
- `POST /api/v1/intelligence/feedback`
- `POST /api/v1/intelligence/feedback/{id}/read`
- `GET/POST /api/v1/intelligence/feedback/templates`
- `GET /api/v1/intelligence/feedback/recipients`
- `GET/POST/PATCH /api/v1/intelligence/watchlists`
- `GET/POST/PATCH /api/v1/intelligence/cases`
- `GET /api/v1/intelligence/routes`
- `POST /api/v1/intelligence/route-analysis`
- `POST /api/v1/intelligence/routes/analyze` (alias)
- `GET /api/v1/intelligence/route-timeline/{plate}`
- `GET /api/v1/intelligence/routes/{plate}/timeline` (alias)
- `GET /api/v1/intelligence/routes/{plate}`
- `GET /api/v1/intelligence/convoys`
- `GET /api/v1/intelligence/roaming`
- `GET /api/v1/intelligence/sensitive-assets`
- `GET /api/v1/intelligence/analytics/overview`

Auditoria:

- `GET /api/v1/audit/logs`

## 8. Banco e modelagem

Blocos principais:

- operacao: observacoes, leitura OCR, suspeicao, sync, assets
- inteligencia: reviews, feedback estruturado, watchlist, casos
- algoritmos: eventos de rota/convoy/roaming/ativo sensivel, score composto
- governanca: usuarios, dispositivos, auditoria
- tenancy: agencias e escopo segregado por `agency_id`

Ponto importante:

- coexistem `feedbackevent` (legado) e `analystfeedbackevent` (estruturado)
- backend consolida leitura para manter compatibilidade
- deprecacao do legado ainda precisa de plano formal

## 9. Eventos internos

Ja publicados/consumidos no ciclo atual:

- `observation_created`
- `suspicion_submitted`
- `sync_completed`
- `field_approach_confirmed`
- eventos de review/feedback no modulo de inteligencia

Worker assincorno:

- consumo em grupo Redis Streams
- ack de mensagem processada
- tolerancia a indisponibilidade temporaria de Redis

## 10. Validacoes executadas no ambiente desta sessao

- `npm run lint` em `web-intelligence-console` (OK)
- `npm run build` em `web-intelligence-console` (OK)

Limitacoes registradas:

- runtime Python indisponivel no PATH para validacao local completa
- repositorio mobile ainda sem `gradlew` e ambiente sem Gradle global (build Android nao executado nesta sessao)

## 11. Riscos tecnicos remanescentes

- sem integracao estadual real, parte do valor imediato segue em fallback
- sem wrapper gradle versionado, build Android nao fica plenamente reproduzivel
- sem suite automatizada de integracao, risco de regressao em contratos
- heuristicas analiticas v1 precisam calibracao com dado real para reduzir ruido

## 12. Documentacao Tecnica Completa

### 12.1 Arquitetura Zero-Trust (Mobile-Server Sync)
**Documentacao:** `docs/architecture/zero-trust-implementation.md`

**Implementado:**
- Criptografia AES-256 (Android Keystore)
- Compressao de imagens 800x600 auditavel
- Sync seguro com eliminacao DoD 5220.22-M
- TTL 7 dias com auto-destruicao
- Endpoints server: `/mobile/sync/batch`, `/mobile/observations/{id}/assets`

**Fluxo:**
Mobile (captura criptografada) → HTTPS sync → Server (PostgreSQL+MinIO) → Confirmação → Eliminação segura local

## 13. Integracoes Futuras (para outros devs)

**Documentacao completa:** `docs/integrations/future-roadmap.md`

### 13.1 Consulta de Placa em Bases Oficiais
**Status:** 🟡 Estrutura pronta, aguardando implementacao

**TODOs marcados no codigo:**
- `server-core/app/api/v1/endpoints/mobile.py:235-286` - TODO[FUTURO] consulta base oficial
- `server-core/app/integrations/state_registry_adapter.py` - Adapter stub (retorna "sem conexao")

**Bases a integrar:**
1. DETRAN-MS (roubo/furto, debitos, dados cadastrais)
2. Policia Federal (alertas nacionais)
3. RENAVAM (dados cadastrais completos)

**Implementacao:** Descomentar chamada em `check_plate_suspicion()` e implementar adapters.

### 13.2 Autenticacao em Bases Oficiais
**Status:** 🟡 Estrutura pronta, autenticacao local funcionando

**TODOs marcados no codigo:**
- `server-core/app/api/v1/endpoints/auth.py:37-132` - TODO[FUTURO] autenticacao externa
- Funcao `verify_with_intelligence_db()` comentada com documentacao extensa

**Sistemas a integrar:**
1. GOV.BR (SSO Federal) - OAuth2/OIDC
2. Sistema RH/PESSOAL PMMS (validar matricula, unidade, status)
3. SIGMIL (Sistema de Identidade Militar)

**Implementacao:** Descomentar funcao e implementar adapters conforme checklist no codigo.

**Credenciais:** Solicitar via SELOG/PMMS (processo administrativo)

## 14. Quick Wins Implementados (Fase 1 - 2026-04-15)

### 14.1 Push Notification em Tempo Real (WebSocket)
**Backend:**
- `app/services/websocket_service.py` - WebSocketConnectionManager para gerenciar conexões
- `app/api/v1/endpoints/websocket.py` - Endpoints WebSocket para usuário e broadcast
- Configurações em `config.py`: `websocket_enabled`, `websocket_ping_interval`, `websocket_max_connections`
- Integração com feedback: notificação enviada via WebSocket quando feedback é criado
- Router adicionado em `app/api/routes.py`

**Mobile:**
- `app/src/main/java/com/faro/mobile/data/websocket/WebSocketManager.kt` - Cliente WebSocket
- Conexão por usuário para notificações personalizadas
- Reconexão automática com exponential backoff
- Gerenciamento de estado de conexão e notificações

**Rollback:** Desabilitar via `websocket_enabled=false` no config. Fallback para sync em lote.

### 14.2 Auto-OCR com Threshold
**Backend:**
- Configurações em `config.py`: `ocr_auto_accept_enabled`, `ocr_auto_accept_threshold` (default 0.85)
- `ocr_confidence_threshold` já existente (default 0.7)

**Mobile:**
- `PlateCaptureScreen.kt` atualizado com lógica de auto-aceitação
- Variáveis `autoOcrEnabled` e `autoOcrThreshold` configuráveis
- Auto-aceita OCR quando `confidence >= threshold` (default 0.85)
- Fallback manual sempre disponível

**Rollback:** Desabilitar via `ocr_auto_accept_enabled=false`. Fallback para OCR assistido.

### 14.3 Priorização Automática da Fila
**Backend:**
- Configurações em `config.py`: `queue_auto_prioritization_enabled`, `queue_score_weight` (0.6), `queue_urgency_weight` (0.4), `queue_score_threshold` (0.7)
- `intelligence.py` - Enhanced queue ordering com composite score
- Quando habilitado: ordena por urgency + SuspicionScore * score_weight
- Fallback para FIFO manual (urgency + time) quando desabilitado

**Rollback:** Desabilitar via `queue_auto_prioritization_enabled=false`. Fallback para fila FIFO manual.

### 14.4 Upload Progressivo de Assets
**Backend:**
- Configurações em `config.py`: `progressive_upload_enabled`, `progressive_upload_chunk_size_mb` (5), `progressive_upload_max_retries` (3)
- `storage_service.py` - `upload_observation_asset_progressive()` e `complete_progressive_upload()`
- Suporte a multipart upload com chunking
- Retry automático com abort on error
- Endpoint `/mobile/observations/{id}/assets/progressive` em `mobile.py`

**Rollback:** Desabilitar via `progressive_upload_enabled=false`. Fallback para upload após sync.

## 15. Proximos passos recomendados

1. implementar conector oficial da base estadual no adapter existente
2. adicionar `gradlew` ao mobile e pipeline de build Android
3. criar testes de integracao backend com Postgres/PostGIS/Redis
4. calibrar thresholds dos 7 algoritmos em dataset operacional
5. reforcar observabilidade por dominio (fila, sync, feedback, rotas)
6. habilitar WebSocket, auto-OCR, priorização e upload progressivo via config após testing

## 16. BI Institucional Implementado (Fase 2 - 2026-04-15)

### 16.1 Hierarquia de Agências
**Backend:**
- `app/db/base.py`: Adicionado `AgencyType` enum (LOCAL, REGIONAL, CENTRAL)
- `app/db/base.py`: Adicionados campos `type` e `parent_agency_id` ao modelo Agency
- `alembic/versions/0006_agency_hierarchy.py`: Migration para hierarquia de agências

**RBAC:**
- `app/api/v1/endpoints/intelligence.py`: `get_agency_scope_filter()` para filtros por nível
- `app/api/v1/endpoints/intelligence.py`: Extended `scoped_query()` com suporte a hierarquia
- `app/api/v1/endpoints/intelligence.py`: `/analytics/overview` com parâmetro `agency_id`

**Web Intelligence Console:**
- `src/app/types/index.ts`: Adicionado `AgencyType` e interface `Agency`
- `src/app/services/api.ts`: `dashboardApi.getStats()` aceita `agencyId` opcional
- `src/app/page.tsx`: Selector de agência com filtros (local/regional/central)

### 16.2 Visão por Nível de Agência
**Agências Locais:**
- Responsáveis por validação de insights/suspeição dos agentes de campo
- Escopo: Batalhões, regimentos, companhias independentes
- Visão: Mapas, rotas, hotspots ao nível local

**Agências Regionais:**
- Responsáveis por visão analítica regional
- Escopo: Região do estado com agências locais
- Visão: Mapas, rotas, hotspots ao nível regional (agregado)

**Agência Central:**
- Responsável por visão analítica estadual
- Escopo: Todo o estado com agências regionais
- Visão: Mapas, rotas, hotspots ao nível estadual (agregado)

### 16.3 Próximos Passos
- ✅ Implementar hierarchy-based filtering completo (child agencies) - Helper functions adicionadas
- ✅ Criar dashboards específicos por nível de agência - Selector dinâmico implementado
- ✅ Adicionar endpoints para listar agências por tipo - `/intelligence/agencies` endpoint criado
- ⏳ Testing com usuários de cada nível - Pendente
- ⏳ Deployment incremental (local → regional → central) - Pendente

### 16.4 Implementação Complementar (Fase 2.1 - 2026-04-15)
**Backend:**
- `app/schemas/agency.py`: Schemas para Agency (Create, Response, Update, List)
- `app/schemas/__init__.py`: Adicionados Agency schemas
- `app/api/v1/endpoints/intelligence.py`: Endpoint `/intelligence/agencies` com filtro por tipo
- `get_user_agency_with_hierarchy()`: Função auxiliar para carregar agência com hierarquia
- `get_child_agency_ids()`: Função auxiliar para buscar agências filhas

**Web Intelligence Console:**
- `src/app/services/api.ts`: `dashboardApi.getAgencies()` para listar agências
- `src/app/page.tsx`: Selector dinâmico de agência com filtro por tipo
- Reload automático ao mudar agência ou tipo

### 16.5 Gestão de Usuários Hierarquizada (Fase 2.2 - 2026-04-15)
**Backend:**
- `app/api/v1/endpoints/auth.py`: Endpoints CRUD de usuários
  - `GET /auth/users`: Listar usuários com filtros por role e agency
  - `POST /auth/users`: Criar novo usuário
  - `PUT /auth/users/{user_id}`: Atualizar usuário
  - `DELETE /auth/users/{user_id}`: Soft delete de usuário

**RBAC Implementado:**
- **ADMIN**: Pode ver, criar, atualizar e deletar usuários em qualquer agência
- **SUPERVISOR**: Pode gerenciar usuários apenas na sua agência
- **INTELLIGENCE (Central)**: Pode ver todos analistas de inteligência de todas as agências
- **INTELLIGENCE (Regional)**: Pode ver analistas da sua região
- **FIELD_AGENT**: Não tem acesso à gestão de usuários

**Web Intelligence Console:**
- `src/app/services/api.ts`: `userApi` com métodos listUsers, createUser, updateUser, deleteUser
- `src/app/users/page.tsx`: Tela de gestão de usuários
  - Filtro por perfil (analista/agente/supervisor/admin)
  - Filtro por agência
  - Busca por nome ou email
  - Tabela com listagem de usuários
  - Ações de editar e deletar
  - Paginação
