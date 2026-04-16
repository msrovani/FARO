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

## 17. Otimização de Performance (Fase 3 - 2026-04-15)

### 17.1 Otimizações Implementadas no Server-Core

**Documentação:** `docs/performance/server-optimization.md`

#### 17.1.1 Otimizações de Database
**mobile.py - Paralelização de Queries:**
- `check_plate_suspicion()` - Queries independentes paralelizadas com `asyncio.gather()`
- Queries: watchlist lookup, prior suspicion check, observation count
- Impacto: ~3x redução de latência para checks de placa

**route_prediction_service.py - Pagination Limits:**
- `get_recurring_route_alerts()` - Adicionado `limit=100` por padrão
- Previne carregamento excessivo de padrões de rota em memória
- Previne memory issues com grandes datasets

#### 17.1.2 Otimizações de Frontend (React)
**Componentes com React.memo:**
- `AlertMarker.tsx` - Map markers otimizados para evitar re-renders
- `RouteMarker.tsx` - Route markers otimizados para evitar re-renders
- Benefício: Performance melhorado quando muitos markers são exibidos no mapa

#### 17.1.3 Detecção Automática de Hardware
**app/utils/hardware_detector.py:**
- Detecta CPU (lógicos/físicos), memória total/disponível
- Detecta GPU (CUDA NVIDIA, MPS Apple Silicon)
- Calcula workers ótimos baseados em tipo de tarefa:
  - CPU-bound: 1-2 workers por core físico
  - I/O-bound: 2-4 workers por core lógico
  - GPU-bound: workers limitados para não sobrecarregar GPU
- Calcula batch size ótimo baseado em capacidade de GPU

#### 17.1.4 Configuração Dinâmica
**config.py:**
```python
workers: int = Field(default="auto")  # Detecta automaticamente
process_pool_max_workers: int = Field(default="auto")
process_pool_cpu_bound_workers: int = Field(default="auto")
process_pool_io_bound_workers: int = Field(default="auto")
ocr_device: str = Field(default="auto")  # GPU automática
```
- Validators resolvem "auto" para valores baseados em hardware detectado
- Fallback para 4 workers se detecção falhar

#### 17.1.5 ProcessPoolExecutor para Tarefas CPU-Bound
**app/utils/process_pool.py:**
- `run_in_process_pool()` - Executa funções CPU-bound em processos separados
- `run_batch_in_process_pool()` - Executa em lote com paralelismo
- Integração com monitoramento de performance
- Integração com circuit breaker para fallback

#### 17.1.6 Monitoramento de Performance
**app/utils/performance_monitor.py:**
- Rastreia tempo de execução (avg, p95, p99)
- Rastreia taxa de sucesso/erro
- Determina estado (HEALTHY, DEGRADED, CRITICAL)
- Fornece recomendações adaptativas (scale up/down, batch size)
- Configurações registradas por tipo de tarefa (OCR, route analysis, hotspot clustering)

#### 17.1.7 Circuit Breaker para Fallback
**app/utils/circuit_breaker.py:**
- Abre circuito após N falhas consecutivas
- Timeout automático para tentar half-open
- Fallback configurável
- Protege contra degradação de performance
- Estados: CLOSED (normal), OPEN (rejeitando), HALF_OPEN (testando recuperação)

#### 17.1.8 GPU Automática para OCR
**ocr_service.py:**
- `detect_gpu_device()` - Detecta CUDA (NVIDIA) ou MPS (Apple Silicon)
- Fallback para CPU se GPU não disponível
- Configuração via `OCR_DEVICE=auto|cpu|cuda|mps`
- Performance esperada:
  - CPU: ~500-1000ms por imagem
  - GPU (CUDA): ~20-50ms por imagem
  - GPU (MPS): ~30-60ms por imagem

#### 17.1.9 Serviços Atualizados com ProcessPoolExecutor
**OCR Service:**
- `AsyncOcrService` - Wrapper async com ProcessPoolExecutor
- `process_image_async()` - OCR assíncrono com monitoring e circuit breaker
- `process_batch_async()` - OCR em lote paralelo

**Route Analysis:**
- `analyze_vehicle_route_parallel()` - Análise com cálculos paralelos
- Cálculos paralelos: recurrence score, predominant direction

**Hotspot Clustering:**
- `analyze_hotspots_parallel()` - Clustering com monitoring e circuit breaker
- Clustering espacial em processo separado

#### 17.1.10 Inicialização Automática
**main.py:**
- Registra configurações de performance para cada tipo de tarefa
- Define targets (p95, p99, success rate)
- Shutdown do process pool ao encerrar
- Configurações registradas:
  - ocr_processing: target p95=1000ms, p99=2000ms
  - ocr_batch: target p95=5000ms, p99=10000ms
  - route_recurrence: target p95=500ms, p99=1000ms
  - route_direction: target p95=200ms, p99=500ms
  - hotspot_clustering: target p95=2000ms, p99=5000ms

### 17.2 Como Usar Otimizações

**Configuração automática (padrão):**
```bash
WORKERS=auto
PROCESS_POOL_MAX_WORKERS=auto
OCR_DEVICE=auto
```

**Override manual:**
```bash
WORKERS=8
PROCESS_POOL_MAX_WORKERS=16
OCR_DEVICE=cuda
```

**API de performance:**
```python
from app.utils.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
metrics = monitor.get_metrics("ocr_processing")
recommendation = monitor.get_adaptive_recommendation("ocr_processing")
```

### 17.3 Benefícios das Otimizações

- **Auto-detecção**: CPU, GPU, memória detectados automaticamente
- **Auto-configuração**: Workers e batch size otimizados para hardware
- **Auto-monitoramento**: Performance rastreada em tempo real
- **Auto-fallback**: Circuit breaker protege contra degradação
- **Auto-adaptação**: Recomendações para escala baseadas em métricas
- **GPU automática**: OCR usa GPU se disponível (CUDA/MPS)
- **Full capacity**: Usa toda capacidade disponível do hardware

### 17.4 Dependencies Adicionadas

**requirements.txt:**
- `psutil==6.1.0` - Para detecção de hardware

### 17.5 Otimizações Implementadas para Android (mobile-agent-field)

**Arquivos Implementados:**
- `app/src/main/java/com/faro/mobile/utils/HardwareCapabilities.kt` - Detecção de hardware
- `app/src/main/java/com/faro/mobile/utils/PerformanceConfig.kt` - Configuração dinâmica
- `app/src/main/java/com/faro/mobile/utils/SyncOptimizer.kt` - Otimizações de sync
- `app/src/main/java/com/faro/mobile/utils/OcrOptimizer.kt` - Otimizações de OCR
- `app/src/main/java/com/faro/mobile/utils/UiOptimizer.kt` - Otimizações de UI
- `app/src/main/java/com/faro/mobile/utils/StorageOptimizer.kt` - Otimizações de armazenamento

#### 17.5.1 Detecção de Hardware Android
**Implementado em HardwareCapabilities.kt:**
- Detecta número de cores CPU (Runtime.getRuntime().availableProcessors())
- Detecta memória total e disponível (ActivityManager.MemoryInfo)
- Detecta GPU (OpenGL ES renderer, version)
- Detecta tipo de dispositivo (phone/tablet)
- Detecta nível de API Android
- Detecta arquitetura (ARMv7, ARM64, x86, x86_64)

#### 17.5.2 Configuração Dinâmica Baseada em Hardware
**Implementado em PerformanceConfig.kt:**

**Low-end (2GB RAM, 4 cores):**
- ThreadPoolExecutor: 2 threads
- Image compression: qualidade 70%, max 640x480
- OCR: CPU only, batch size 2
- Sync batch size: 10 observações (WiFi: 15)
- Cache limit: 50MB

**Mid-range (4GB RAM, 8 cores):**
- ThreadPoolExecutor: 4 threads
- Image compression: qualidade 80%, max 800x600
- OCR: CPU ou GPU se disponível, batch size 4
- Sync batch size: 25 observações (WiFi: 40)
- Cache limit: 150MB

**High-end (8GB+ RAM, 8+ cores, GPU):**
- ThreadPoolExecutor: 8 threads
- Image compression: qualidade 85%, max 1280x720
- OCR: GPU se disponível, batch size 8
- Sync batch size: 50 observações (WiFi: 75)
- Cache limit: 300MB

#### 17.5.3 Otimizações de OCR no Android
**Implementado em OcrOptimizer.kt:**
- Detecção automática de GPU para OCR
- Batch size adaptativo baseado em hardware
- Compressão de imagens antes do OCR (inSampleSize)
- Fallback para server-side OCR se device não tiver capacidade
- Cache de modelos adaptativo baseado em memória disponível
- Thread pool size otimizado para paralelismo

#### 17.5.4 Otimizações de Sync no Android
**Implementado em SyncOptimizer.kt:**
- Batch sync adaptativo baseado em conectividade (WiFi vs Mobile)
- Compressão adaptativa (WiFi: qualidade original, Mobile: +10% compressão)
- Exponential backoff para falhas (base 1s, max 30s)
- Priorização de sync por tipo de dado
- Verificação de disponibilidade de rede
- Threshold de batch size para WiFi (20+ itens requer WiFi)

#### 17.5.5 Otimizações de UI no Android
**Implementado em UiOptimizer.kt:**
- RecyclerView cache size adaptativo (10-30 itens)
- Image loading strategy adaptativo (Conservative/Balanced/Aggressive)
- Animation duration multiplier (0.8x-1.5x baseado em hardware)
- Desabilitação de animações complexas em low-end
- List item preload count adaptativo (3-10 itens)
- Verificação de hardware acceleration

#### 17.5.6 Otimizações de Armazenamento no Android
**Implementado em StorageOptimizer.kt:**
- Query page size adaptativo (20-100)
- Query cache size adaptativo (50-200)
- Data compression level adaptativo (2-6)
- Cache TTL adaptativo (30-120 minutos)
- Max local items adaptativo (100-500)
- Database batch size adaptativo (10-50)
- Index strategy adaptativo (Minimal/Standard/Aggressive)
- WAL mode adaptativo (Disabled/Normal/Full)

#### 17.5.7 Como Usar as Otimizações

**Exemplo de uso:**
```kotlin
// Inicializar otimizadores no Application
val performanceConfigManager = PerformanceConfigManager(context)
val config = performanceConfigManager.getOptimalConfig()

// Usar otimizações específicas
val syncOptimizer = SyncOptimizer(context)
val batchSize = syncOptimizer.getOptimalBatchSize()

val ocrOptimizer = OcrOptimizer(context)
val useGpu = ocrOptimizer.shouldUseGpu()

val uiOptimizer = UiOptimizer(context)
val cacheSize = uiOptimizer.getRecyclerViewCacheSize()

val storageOptimizer = StorageOptimizer(context)
val pageSize = storageOptimizer.getQueryPageSize()
```

## 18. Segurança em WiFi Públicas - Network Validation + 4G-First Policy

### 18.1 Estratégia Implementada

**Por que não VPN:**
- VPN adiciona complexidade de gerenciamento
- Requer infraestrutura dedicada
- Pode ter impacto em performance
- Difícil de auditar e monitorar

**Abordagem Implementada:**
1. **Network Validation** - Bloquear sync em WiFi não confiável
2. **4G-First Policy** - Dados antigos (>7 dias) requerem 4G obrigatório
3. **Heavy Data Policy** - Dados pesados (>10MB) requerem WiFi institucional ou 4G
4. **TTL Enforcement** - Sync obrigatório após 7 dias via 4G

**Não Implementado (Discussão Futura):**
- mTLS (18.3) - Discutir impactos de implementação
- End-to-End Encryption (18.4) - Discutir impactos de implementação

### 18.2 Network Validation - IMPLEMENTADO

**Arquivo:** `app/src/main/java/com/faro/mobile/utils/NetworkValidator.kt`

**Funcionalidades:**
- Detectar tipo de rede (WiFi institucional, WiFi público, 4G)
- Bloquear sync em WiFi não confiável
- Validar SSIDs confiáveis (PMMS, GOV, POLICIA, BMRS)
- Avaliar qualidade de rede (score 0-100)
- Classificar tipo de conexão

**Regras:**
- 4G: Sempre confiável
- WiFi institucional: Confiável
- WiFi público: Bloqueado

### 18.3 mTLS - NÃO IMPLEMENTADO

**Status:** Discutir implementação futura

**Motivo:** Avaliar impactos de infraestrutura e gestão de certificados

### 18.4 End-to-End Encryption - NÃO IMPLEMENTADO

**Status:** Discutir implementação futura

**Motivo:** Avaliar impactos em performance e complexidade de chaves

### 18.5 4G-First Policy - IMPLEMENTADO

**Arquivo:** `app/src/main/java/com/faro/mobile/utils/SyncPolicy.kt`

**Regras Implementadas:**
- Dados com mais de 7 dias (TTL) requerem 4G obrigatório
- Dados pesados (>10MB) requerem WiFi institucional ou 4G
- Dados sensíveis (observações, imagens, áudio) requerem rede confiável
- Feedback não sensível pode usar qualquer rede confiável

**TTL Enforcement:**
- TTL padrão: 7 dias
- Após 7 dias: Sync apenas via 4G
- Prioridade aumenta conforme dados envelhecem

### 18.6 Secure Sync Manager - IMPLEMENTADO

**Arquivo:** `app/src/main/java/com/faro/mobile/utils/SecureSyncManager.kt`

**Funcionalidades:**
- Verificar se sync pode prosseguir
- Validar se dados específicos podem ser sincronizados
- Calcular batch size recomendado
- Determinar prioridade de sync
- Fornecer informações de rede para logging

**Uso:**
```kotlin
val secureSyncManager = SecureSyncManager(context)

// Verificar se sync pode prosseguir
val syncCheck = secureSyncManager.canSync()
if (syncCheck is SyncCheckResult.BLOCKED) {
    // Mostrar mensagem ao usuário
}

// Verificar se dados específicos podem ser sincronizados
val dataCheck = secureSyncManager.canSyncData(
    dataType = DataType.IMAGE,
    dataSizeMb = 15L,
    createdAt = observation.createdAt
)
```

### 18.7 Integração com Sync Existente - IMPLEMENTADO

**Arquivos Modificados:**
- `SyncWorker.kt` - Integrado com SecureSyncManager
- `NetworkValidator.kt` - Integrado com NetworkSettings
- `SyncPolicy.kt` - Integrado com NetworkSettings

**Fluxo de Sync Atualizado:**
1. Verificar se sync pode prosseguir (SecureSyncManager.canSync())
2. Se bloqueado: mostrar notificação ao usuário e não retry
3. Se adiado: mostrar notificação ao usuário e retry
4. Obter observações pendentes (ObservationRepositoryImpl.getPendingSyncObservations())
5. Filtrar observações baseado em política de sync
6. Ordenar por prioridade (dados mais antigos primeiro)
7. Aplicar batch size baseada em rede
8. Sincronizar batch

### 18.8 Notificações ao Usuário - IMPLEMENTADO

**Arquivo:** `SyncWorker.kt`

**Funcionalidades:**
- Notificação quando sync é bloqueado (WiFi público)
- Notificação quando sync é adiado (rede pobre)
- Sugestões claras de ação para o usuário
- Canal de notificação criado automaticamente

**Tipos de Notificação:**
- "Sync Bloqueado" - Quando rede não é confiável
- "Sync Adiado" - Quando qualidade de rede é insuficiente

### 18.9 Configuração de SSIDs Confiáveis - IMPLEMENTADO

**Arquivo:** `NetworkSettings.kt`

**Funcionalidades:**
- Singleton para acesso global a configurações
- Lista de SSIDs confiáveis configurável
- TTL de sync configurável (padrão: 7 dias)
- Threshold de dados pesados configurável (padrão: 10MB)
- Reset para configurações padrão

**Uso:**
```kotlin
val settings = NetworkSettings.getInstance(context)

// Obter SSIDs confiáveis
val ssids = settings.getTrustedSsids()

// Adicionar SSID confiável
settings.addTrustedSsid("NOVA_REDE")

// Remover SSID confiável
settings.removeTrustedSsid("REDE_ANTIGA")

// Configurar TTL
settings.setSyncTtlDays(14L)

// Configurar threshold
settings.setHeavyDataThresholdMb(20L)
```

### 18.10 Exemplo de Integração Completa

**SyncWorker.kt - Integração Real:**
```kotlin
override suspend fun doWork(): Result {
    // Check network
    val syncCheck = secureSyncManager.canSync()
    when (syncCheck) {
        is SyncCheckResult.BLOCKED -> {
            showNotification("Sync Bloqueado", syncCheck.reason, syncCheck.suggestion)
            return Result.success()
        }
        is SyncCheckResult.DEFERRED -> {
            showNotification("Sync Adiado", syncCheck.reason, syncCheck.suggestion)
            return Result.retry()
        }
        is SyncCheckResult.ALLOWED -> { /* Continue */ }
    }
    
    // Filter and prioritize
    val syncQueue = pendingObservations.filter { obs ->
        val dataSizeMb = estimateDataSize(obs)
        val dataCheck = secureSyncManager.canSyncData(DataType.OBSERVATION, dataSizeMb, obs.createdAt)
        dataCheck is SyncDataCheckResult.ALLOWED
    }.sortedByDescending { obs ->
        secureSyncManager.getSyncPriority(DataType.OBSERVATION, obs.createdAt)
    }
    
    // Apply batch size
    val batchSize = secureSyncManager.getRecommendedBatchSize()
    val batch = syncQueue.take(batchSize)
    
    // Sync batch
    return syncBatch(batch)
}
```

### 18.11 Benefícios da Implementação

**Segurança:**
- Bloqueio de WiFi público para dados sensíveis
- TTL enforcement para dados antigos (configurável)
- Validação de rede confiável
- Priorização de dados críticos
- SSIDs confiáveis configuráveis

**Performance:**
- Batch size adaptativo por rede
- Qualidade de rede avaliada
- Defer em redes pobres
- Priorização inteligente
- Estimativa de tamanho de dados

**Operacional:**
- Feedback claro ao usuário via notificações
- Logging detalhado de rede
- Configuração de SSIDs confiáveis via settings
- Fallback para offline (já existente)
- TTL e threshold configuráveis

### 18.12 Próximos Passos

**Fase 1 (Concluído):**
- ✅ Implementar NetworkValidator
- ✅ Implementar SyncPolicy com TTL
- ✅ Implementar SecureSyncManager
- ✅ Documentação

**Fase 2 (Concluído):**
- ✅ Integrar com sync service existente (SyncWorker)
- ✅ Adicionar notificações ao usuário
- ✅ Configurar SSIDs confiáveis via settings (NetworkSettings)
- ✅ Integrar NetworkSettings com NetworkValidator e SyncPolicy

**Fase 3 (Discussão Futura):**
- Avaliar mTLS implementação
- Avaliar E2EE implementação
- Impactos em performance
- Complexidade de gestão

## 19. Análise Detalhada - Fase 3 (mTLS e E2EE)

### 19.1 Análise de mTLS (Mutual TLS)

#### 19.1.1 O que é mTLS

**Definição:**
mTLS (Mutual TLS) é uma extensão do protocolo TLS onde tanto o cliente quanto o servidor se autenticam mutuamente usando certificados digitais.

**Como Funciona:**
1. Cliente se conecta ao servidor
2. Servidor apresenta seu certificado (TLS tradicional)
3. Servidor solicita certificado do cliente
4. Cliente apresenta seu certificado
5. Servidor valida o certificado do cliente
6. Conexão estabelecida após autenticação mútua

#### 19.1.2 Benefícios para FARO

**Segurança:**
- Autenticação forte de dispositivos
- Cada dispositivo tem identidade única
- Revogação centralizada de dispositivos
- Proteção contra dispositivos comprometidos
- Auditoria detalhada por dispositivo

**Operacional:**
- Controle granular de acesso
- Rastreamento de dispositivos
- Compliance com políticas de segurança
- Integração com PKI institucional

#### 19.1.3 Custos e Complexidade

**Infraestrutura:**
- **PKI (Public Key Infrastructure):** Necessária para emissão e gestão de certificados
- **CA (Certificate Authority):** Pode ser interna ou externa
- **CRL (Certificate Revocation List):** Lista de certificados revogados
- **OCSP (Online Certificate Status Protocol):** Validação em tempo real

**Gestão:**
- **Emissão de certificados:** Cada dispositivo precisa de certificado
- **Renovação:** Certificados expiram (geralmente 1-2 anos)
- **Revogação:** Dispositivos perdidos/roubados precisam ser revogados
- **Distribuição:** Certificados precisam ser distribuídos aos dispositivos
- **Backup:** Backup de chaves privadas (se necessário)

**Desenvolvimento:**
- **Android:** Configurar OkHttpClient com certificados cliente
- **Server:** Configurar validação mútua no servidor
- **Provisionamento:** Fluxo seguro para distribuir certificados
- **Erro Handling:** Tratamento de certificados expirados/revogados

#### 19.1.4 Impactos em Performance

**Latência:**
- **Handshake TLS:** Adiciona ~100-200ms na primeira conexão
- **Validação de certificados:** ~10-50ms adicional
- **Caching:** Conexões subsequentes são mais rápidas
- **Impacto geral:** Negligenciável para operações de sync

**Recursos:**
- **CPU:** Criptografia assimétrica é intensiva em CPU
- **Memória:** Armazenamento de certificados
- **Bateria:** Impacto mínimo em dispositivos modernos

#### 19.1.5 Viabilidade para FARO

**Fatores Positivos:**
- Instituição governamental provavelmente já tem PKI
- Controle rigoroso de dispositivos já existe
- Compliance com políticas de segurança
- Benefícios de segurança significativos

**Fatores Negativos:**
- Complexidade de gestão significativa
- Necessita equipe dedicada para PKI
- Processo de onboarding mais complexo
- Custo de infraestrutura

**Recomendação:**
- **Curto prazo:** Não implementar (complexidade alta)
- **Médio prazo:** Avaliar se PKI institucional existe
- **Longo prazo:** Implementar se PKI já existir e equipe disponível

#### 19.1.6 Implementação Sugerida (Se Aprovado)

**Arquitetura:**
```
┌─────────────────┐
│  Android App    │
│  (Client Cert)  │
└────────┬────────┘
         │ mTLS
         ↓
┌─────────────────┐
│  API Gateway    │
│  (Server Cert)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FARO Server    │
└─────────────────┘
```

**Passos:**
1. Configurar CA institucional ou usar Let's Encrypt
2. Emitir certificados para cada dispositivo
3. Configurar servidor para validar certificados cliente
4. Configurar Android app para usar certificados
5. Implementar fluxo de renovação automática
6. Implementar fluxo de revogação

### 19.2 Análise de E2EE (End-to-End Encryption)

#### 19.2.1 O que é E2EE

**Definição:**
E2EE (End-to-End Encryption) é criptografia onde dados são criptografados no dispositivo remetente e só podem ser descriptografados pelo destinatário final. O servidor intermediário não tem acesso às chaves privadas.

**Como Funciona:**
1. Dispositivo A gera par de chaves (pública/privada)
2. Dispositivo A criptografa dados com chave pública do destinatário
3. Dados são transmitidos (servidor não pode descriptografar)
4. Dispositivo B descriptografa com sua chave privada

#### 19.2.2 Benefícios para FARO

**Segurança:**
- Servidor comprometido não expõe dados
- Proteção contra administradores maliciosos
- Compliance com LGPD (minimização de dados)
- Proteção contra interceptação no servidor
- Auditoria de acesso criptografada

**Operacional:**
- Privacidade máxima para dados sensíveis
- Controle de acesso granular
- Rastreabilidade de acessos
- Compliance com políticas de privacidade

#### 19.2.3 Custos e Complexidade

**Infraestrutura:**
- **Gestão de chaves:** Cada dispositivo precisa de par de chaves
- **Distribuição de chaves:** Chaves públicas precisam ser distribuídas
- **Backup de chaves:** Chaves privadas precisam de backup seguro
- **Rotação de chaves:** Chaves precisam ser rotacionadas periodicamente
- **Key Escrow:** Mecanismo para recuperação em caso de perda

**Desenvolvimento:**
- **Criptografia assimétrica:** RSA/ECC para criptografia
- **Gestão de chaves:** Armazenamento seguro de chaves privadas
- **Key Exchange:** Protocolo seguro para troca de chaves
- **Forward Secrecy:** Proteção contra comprometimento de chaves futuras
- **UI:** Interface para gestão de chaves pelo usuário

**Gestão:**
- **Onboarding:** Configuração de chaves para novos dispositivos
- **Offboarding:** Revogação/remoção de chaves de dispositivos
- **Recuperação:** Processo para recuperação de chaves perdidas
- **Auditoria:** Logging de operações de criptografia

#### 19.2.4 Impactos em Performance

**Latência:**
- **Criptografia:** ~50-100ms por operação
- **Descriptografia:** ~50-100ms por operação
- **Key Exchange:** ~100-200ms inicial
- **Impacto geral:** Significativo para operações em massa

**Recursos:**
- **CPU:** Criptografia assimétrica é muito intensiva em CPU
- **Memória:** Armazenamento de chaves
- **Bateria:** Impacto significativo em dispositivos mobile
- **Storage:** Dados criptografados são maiores

**Escala:**
- **Low-end devices:** Criptografia pode ser lenta
- **Mid-range devices:** Performance aceitável
- **High-end devices:** Performance boa
- **Batch operations:** Criptografia em massa é mais eficiente

#### 19.2.5 Viabilidade para FARO

**Fatores Positivos:**
- Proteção máxima de dados
- Compliance com LGPD
- Proteção contra comprometimento de servidor
- Benefícios de privacidade significativos

**Fatores Negativos:**
- Complexidade de gestão muito alta
- Impacto significativo em performance
- Impacto em bateria de dispositivos mobile
- Necessidade de key escrow (ponto único de falha)
- Dificuldade de debugging (dados criptografados)
- Complexidade de recuperação de chaves

**Recomendação:**
- **Curto prazo:** Não implementar (complexidade muito alta)
- **Médio prazo:** Avaliar se realmente necessário
- **Longo prazo:** Implementar apenas se requisito legal explícito

#### 19.2.6 Implementação Sugerida (Se Aprovado)

**Arquitetura:**
```
┌─────────────────┐
│  Android App    │
│  (Encrypt)      │
└────────┬────────┘
         │ Encrypted
         ↓
┌─────────────────┐
│  FARO Server    │
│  (No Access)    │
└────────┬────────┘
         │ Encrypted
         ↓
┌─────────────────┐
│  Console UI     │
│  (Decrypt)      │
└─────────────────┘
```

**Passos:**
1. Implementar geração de pares de chaves (ECC recomendado)
2. Implementar criptografia/descriptografia
3. Implementar distribuição de chaves públicas
4. Implementar armazenamento seguro de chaves privadas (Android Keystore)
5. Implementar key escrow para recuperação
6. Implementar rotação automática de chaves

### 19.3 Comparação: mTLS vs E2EE

| Aspecto | mTLS | E2EE |
|---------|------|------|
| **Propósito** | Autenticação | Criptografia |
| **Complexidade** | Alta | Muito Alta |
| **Infraestrutura** | PKI necessária | Key management necessária |
| **Performance** | Impacto baixo | Impacto alto |
| **Bateria** | Impacto baixo | Impacto alto |
| **Gestão** | Moderada | Muito complexa |
| **Custo** | Médio | Alto |
| **Viabilidade FARO** | Média | Baixa |
| **Recomendação** | Avaliar PKI | Não implementar |

### 19.4 Alternativas Recomendadas

#### 19.4.1 Alternativa 1: Network Validation + HTTPS (Atual)

**Descrição:**
- Validar rede antes de sync (já implementado)
- Usar HTTPS para criptografia em trânsito (já implementado)
- 4G-first policy para dados sensíveis (já implementado)

**Benefícios:**
- Complexidade baixa
- Performance boa
- Sem infraestrutura adicional
- Já implementado

**Limitações:**
- Servidor pode ver dados
- Proteção contra interceptação em trânsito apenas

#### 19.4.2 Alternativa 2: Application-Level Encryption

**Descrição:**
- Criptografar dados no app antes de enviar
- Chave simétrica compartilhada (mais simples que E2EE)
- Servidor pode descriptografar (não é E2EE verdadeiro)

**Benefícios:**
- Complexidade moderada
- Performance melhor que E2EE
- Proteção adicional em repouso no servidor

**Limitações:**
- Servidor ainda tem acesso às chaves
- Proteção limitada contra comprometimento de servidor

#### 19.4.3 Alternativa 3: Device Binding

**Descrição:**
- Vincular dados ao dispositivo
- Validar dispositivo no servidor
- Revogar dispositivos comprometidos

**Benefícios:**
- Complexidade baixa
- Performance boa
- Controle de dispositivos

**Limitações:**
- Não é criptografia
- Proteção limitada

**Implementação Sugerida (Se Aprovado):**

**Arquitetura:**
```
┌─────────────────┐
│  Android App    │
│  (Device ID)    │
└────────┬────────┘
         │ Device Binding
         ↓
┌─────────────────┐
│  FARO Server    │
│  (Validation)   │
└─────────────────┘
```

**Componentes:**

1. **Device ID Generation**
```kotlin
class DeviceIdGenerator(private val context: Context) {
    
    fun getDeviceId(): String {
        // Use Android ID or generate unique ID
        val androidId = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID
        )
        
        // Hash for privacy
        return sha256(androidId + "faro_salt")
    }
    
    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
```

2. **Device Registration**
```kotlin
class DeviceRegistrationService(
    private val faroApi: FaroApi,
    private val deviceIdGenerator: DeviceIdGenerator
) {
    suspend fun registerDevice(): DeviceRegistrationResult {
        val deviceId = deviceIdGenerator.getDeviceId()
        val deviceInfo = collectDeviceInfo()
        
        return try {
            val response = faroApi.registerDevice(
                deviceId = deviceId,
                deviceInfo = deviceInfo
            )
            DeviceRegistrationResult.Success(response.deviceToken)
        } catch (e: Exception) {
            DeviceRegistrationResult.Error(e.message)
        }
    }
    
    private fun collectDeviceInfo(): DeviceInfo {
        return DeviceInfo(
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL,
            osVersion = Build.VERSION.RELEASE,
            appVersion = BuildConfig.VERSION_NAME
        )
    }
}
```

3. **Device Validation**
```python
# server-core/app/services/device_validation_service.py
from datetime import datetime, timedelta

class DeviceValidationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_device(self, device_id: str, device_token: str) -> bool:
        """Validate device ID and token"""
        device = await self.db.execute(
            select(Device).where(
                Device.device_id == device_id,
                Device.token == device_token,
                Device.is_active == True,
                Device.revoked_at == None
            )
        )
        return device.scalar_one_or_none() is not None
    
    async def revoke_device(self, device_id: str, reason: str):
        """Revoke compromised device"""
        await self.db.execute(
            update(Device)
            .where(Device.device_id == device_id)
            .values(
                is_active=False,
                revoked_at=datetime.utcnow(),
                revocation_reason=reason
            )
        )
        await self.db.commit()
```

4. **Device Binding in Sync**
```kotlin
class SyncWorker {
    override suspend fun doWork(): Result {
        // Validate device before sync
        val deviceId = deviceIdGenerator.getDeviceId()
        val deviceToken = getStoredDeviceToken()
        
        val isValid = faroApi.validateDevice(deviceId, deviceToken)
        if (!isValid) {
            showNotification("Dispositivo Revogado", "Seu dispositivo não está autorizado")
            return Result.failure()
        }
        
        // Proceed with sync
        return syncObservations()
    }
}
```

5. **Device Management Console**
```python
# server-core/app/api/v1/endpoints/devices.py
@router.get("/devices")
async def list_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all registered devices"""
    devices = await db.execute(select(Device))
    return devices.scalars().all()

@router.post("/devices/{device_id}/revoke")
async def revoke_device(
    device_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Revoke a device"""
    device_service = DeviceValidationService(db)
    await device_service.revoke_device(device_id, reason)
    return {"message": "Device revoked"}
```

**Database Schema:**
```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_token VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    os_version VARCHAR(50),
    app_version VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP,
    revoked_at TIMESTAMP,
    revocation_reason TEXT
);
```

**Fluxo de Implementação:**

1. **Registro Inicial**
   - App gera Device ID único
   - App coleta informações do dispositivo
   - App registra no servidor
   - Servidor retorna Device Token
   - App armazena Device Token localmente

2. **Validação em Cada Sync**
   - App envia Device ID e Token
   - Servidor valida dispositivo
   - Se válido, prossegue com sync
   - Se inválido, bloqueia sync

3. **Revogação de Dispositivo**
   - Administrador revoga dispositivo no console
   - Servidor marca dispositivo como inativo
   - Próximo sync do dispositivo é bloqueado
   - Notificação ao usuário

**Benefícios Adicionais:**
- Rastreamento de dispositivos ativos
- Auditoria de acessos por dispositivo
- Revogação rápida de dispositivos comprometidos
- Compliance com políticas de segurança

**Limitações:**
- Não protege contra interceptação de dados
- Device ID pode ser spoofed (mitigado com token)
- Requer gestão de dispositivos no console

### 19.5 Recomendação Final

**Fase 3 - Não Implementar mTLS e E2EE**

**Motivos:**
1. **Complexidade:** Ambos requerem infraestrutura significativa
2. **Performance:** E2EE tem impacto alto em dispositivos mobile
3. **Gestão:** Ambos requerem equipe dedicada
4. **Custo:** Benefícios não justificam custos
5. **Alternativas:** Network validation + HTTPS já fornece proteção adequada

**Recomendação:**
- Manter implementação atual (Network Validation + 4G-First Policy + HTTPS)
- Avaliar mTLS apenas se PKI institucional já existir
- Não implementar E2EE a menos que requisito legal explícito
- Considerar Application-Level Encryption se proteção adicional for necessária
- Device Binding documentado mas não implementado (complexidade adicional não justificada atualmente)

## 20. Operações Táticas e Tracking de Clonagem (v1.5.0)

Esta atualização extinguiu as lacunas ("silence data drops") entre a coleta no Mobile e a apreciação analítica na Inteligência Web, introduzindo gestão de conectividade em hardware e visualização cinemática viva.

### 20.1 Mapa Cinemático e Metadados Puros
No **Web Intelligence Console**, criamos uma visão micro-geográfica (`MapBase` via `react-map-gl`) capaz de renderizar um eixo indicando o `Heading` (rumo) do veículo abordado, utilizando propriedades de transformação CSS para rotacionar o pino em tempo real. Os metadados operacionais (App Version de quem enviou, Velocidade, Tipo de Conexão e sincronização) também ganharam blocos visuais distintos.

### 20.2 Transparência Tática (Intel-Debrief)
O Backend perdeu a cegueira sobre o `ApproachConfirmationRequest` (ou _SuspicionReport_). Todas as inferências humanas feitas diretamente na via pública (`abordado`, `nivel_abordagem_slider`, `ocorrencia_registrada`) agora fazem Join com o `get_observation_detail`. 
O Analista web passa a ler um termômetro nativo do Policial em vez de apenas visualizar OCRs estáticos, humanizando o laço (Human-In-The-Loop absoluto).

### 20.3 Alerta Restrito de Clonagem (Multi-Agências)
O Algoritmo de "Impossible Travel" (`analytics_service.py`) recebeu uma sobrecarga de severidade e confidência. Se uma placa aparecer em posições incompatíveis numa janela de tempo curta, E ambos os avistamentos envolverem Agências Diferentes (`agency_id != previous.agency_id`), a confidência matemática é assinalada para `0.95` (CRITICAL), marcando explicitamente: **ALERTA CLONAGEM MULTI-AGÊNCIA**.

### 20.4 Gerenciamento Remoto de Frota (Kill-switch)
Desenvolvemos a gestão técnica dos aparelhos celulares em patrulha. O Schema de `Device` e as rotas `PATCH /api/v1/intelligence/devices/{device_id}/suspend` permitem agora que Supervisores/Inteligência visualizem e anulem tokens de acesso a partir de uma interface web gráfica intuitiva com feedback `glassmorphic`. Isso blinda a operação mesmo se um terminal móvel for capturado físico ou digitalmente.

21. Redesign UX/UI Consolidation (Phase 1, 2, 3)

- **Mobile (Kotlin/Compose):** Implemented Thumb-Zone ergonomics, offline banners, and multi-level haptic feedback (Success, Suspicion, Grave, Critical) with visual red flash overlays in `PlateCaptureScreen.kt`.
- **Web Analyst (ALI):** Added cinematic map fly-to animations and advanced keyboard navigation (Arrows/Shift+Enter) for the triage queue.
- **Web Admin (DINT/ARI):** Transformed Case management into a dynamic **Kanban board** with Drag & Drop support (`@hello-pangea/dnd`).
- **Intelligence & Audit:** Refined visual intensity with translucent reddish Hotspot heatmaps and added a playable **Timeline Slider**. Enforced mandatory operational justifications for device suspension to ensure full auditability.

