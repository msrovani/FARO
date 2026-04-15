# Evolucao Tecnica do F.A.R.O.

## Objetivo

Registrar a evolucao real (sem mock) do projeto, com foco em:

- entregas implementadas
- validacoes executadas
- pendencias abertas
- riscos tecnicos remanescentes

## 2026-04-12 - Consolidacao de mobile + backend operacional

### Mobile (agente de campo)

- autenticacao real conectada ao backend:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
- sessao persistida em DataStore (`access_token`, `refresh_token`, expiracao, contexto de usuario)
- interceptor de rede sem token fixo em `BuildConfig`
- `SyncWorker` atualizado para:
  - renovar token automaticamente antes de sincronizar
  - consumir `pending_feedback` de `/api/v1/mobile/sync/batch`
  - persistir inbox local de feedback
  - enviar assets de observacao (imagem/audio) apos sync da observacao
- UI atualizada para fluxo real:
  - login real
  - home com dados de sessao/sync
  - historico com feedback pendente e acao de marcar leitura

### Backend (server-core)

- endpoint novo para upload de assets mobile:
  - `POST /api/v1/mobile/observations/{observation_id}/assets`
- storage S3-compatible integrado no fluxo de upload
- persistencia de metadados em `assets`
- auditoria de upload adicionada

## 2026-04-12 - Hardening de backend analitico e banco

### Backend

- middleware de rate limit baseline em memoria
- aliases de rotas para compatibilidade:
  - `POST /api/v1/intelligence/routes/analyze`
  - `GET /api/v1/intelligence/routes/{plate}/timeline`
  - `GET /api/v1/intelligence/routes/{plate}`
- endpoint de rota por placa com retorno de padrao persistido ou calculo sob demanda

### Banco

- migration `0002_operational_indexes` criada com foco em:
  - indices geoespaciais (GiST)
  - indices compostos para consultas analiticas e auditoria

## 2026-04-11 - Ciclo operacional legado estadual + suspeicao previa

### Fluxo implementado

- observacao mobile aciona enriquecimento operacional com:
  - status de cadastro estadual
  - suspeicao previa para placa
- novo endpoint:
  - `POST /api/v1/mobile/observations/{observation_id}/approach-confirmation`
- confirma abordagem em campo e devolve feedback ao agente que abriu a primeira suspeicao

### Integracao estadual em desenvolvimento

- adapter dedicado criado para desacoplamento (`state_registry_adapter`)
- fallback dev explicitamente retornado:
  - `connected: false`
  - `status: "no_connection"`
  - `message: "sem conexao com base estadual"`

## 2026-04-11 - Pipeline de eventos com worker assincorno

- publicacao de eventos reforcada para nao quebrar fluxo principal quando Redis indisponivel
- worker dedicado de Redis Streams implementado (`XGROUP`, `XREADGROUP`, `XACK`)
- consumo inicial para reprocessamento de observacoes:
  - `observation_created`
  - `sync_completed` (observation/completed)

## 2026-04-11 - Expansao do modulo web de inteligencia

- console com modulos dedicados:
  - `queue`, `routes`, `convoys`, `roaming`, `sensitive-assets`
  - `watchlist`, `cases`, `feedback`, `audit`
- fluxo de revisao estruturada com feedback ao campo
- templates de feedback e busca assistida de destinatarios

## Validacoes executadas no ciclo

- `npm run type-check` em `web-intelligence-console`: OK
- `npm run build` em `web-intelligence-console`: falhou por restricao de ambiente (`spawn EPERM`)
- validacoes Python/Android locais: limitadas por indisponibilidade de runtime no ambiente atual

## Pendencias abertas

- conexao real com base estadual (hoje fallback de desenvolvimento)
- build Android reproduzivel com `gradlew` versionado no repo
- testes de integracao HTTP + Postgres/PostGIS + Redis
- calibracao de threshold dos algoritmos em dados reais
- observabilidade por dominio (metrica/tracing/alerta operacional)

## Riscos tecnicos remanescentes

- heuristicas analiticas ainda em v1 (risco de ruido em baixa densidade)
- coexistencia de fluxo legado e estruturado de feedback exige plano de deprecacao
- sem suite automatizada de integracao, regressao pode passar despercebida
