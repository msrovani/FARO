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

## 14. Proximos passos recomendados

1. implementar conector oficial da base estadual no adapter existente
2. adicionar `gradlew` ao mobile e pipeline de build Android
3. criar testes de integracao backend com Postgres/PostGIS/Redis
4. calibrar thresholds dos 7 algoritmos em dataset operacional
5. reforcar observabilidade por dominio (fila, sync, feedback, rotas)
