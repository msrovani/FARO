# Contratos de API (resumo operacional)

## Convencoes

- prefixo: `/api/v1`
- formato: `application/json` (exceto upload multipart)
- auth: `Bearer JWT`
- idempotencia mobile: `client_id` por observacao
- paginacao: `page` e `page_size` quando aplicavel

## Auth

### `POST /api/v1/auth/login`

- autentica usuario e retorna `access_token` + `refresh_token`

### `POST /api/v1/auth/refresh`

- renova sessao via refresh token

### `POST /api/v1/auth/logout`

- encerra sessao atual

## Mobile

### `POST /api/v1/mobile/observations`

- cria observacao com idempotencia
- retorna `instant_feedback` enriquecido com:
  - contexto estadual (`state_registry_status`)
  - suspeicao previa (`prior_suspicion_context`)
  - sinal de confirmacao em campo (`requires_suspicion_confirmation`)

Nota de ambiente dev:

- integracao estadual atual retorna fallback:
  - `connected: false`
  - `status: "no_connection"`
  - `message: "sem conexao com base estadual"`

### `POST /api/v1/mobile/observations/{observation_id}/suspicion`

- registra suspeicao estruturada do campo

### `POST /api/v1/mobile/observations/{observation_id}/approach-confirmation`

- confirma resultado da abordagem em campo
- quando existe suspeicao previa, gera feedback ao agente original

### `POST /api/v1/mobile/observations/{observation_id}/assets`

- upload multipart de evidencias:
  - `asset_type`: `image` ou `audio`
  - `file`: binario

### `POST /api/v1/mobile/sync/batch`

- sincroniza observacoes offline
- retorna `pending_feedback` consolidado (legado + estruturado)

### `GET /api/v1/mobile/history`

- historico recente do agente

### `GET /api/v1/mobile/observations/{id}/feedback`

- feedback associado a observacao

## Inteligencia

### `GET /api/v1/intelligence/queue`

- fila analitica para triagem e priorizacao

### `GET /api/v1/intelligence/observations/{id}`

- detalhe completo do registro analitico

### `POST /api/v1/intelligence/reviews`
### `PATCH /api/v1/intelligence/reviews/{id}`

- cria/atualiza revisao estruturada com versionamento

### `GET /api/v1/intelligence/feedback/pending`
### `POST /api/v1/intelligence/feedback`
### `POST /api/v1/intelligence/feedback/{id}/read`

- ciclo completo de retorno ao campo (consulta, envio e leitura)

### `GET /api/v1/intelligence/feedback/templates`
### `POST /api/v1/intelligence/feedback/templates`
### `GET /api/v1/intelligence/feedback/recipients`

- templates e busca assistida de destinatarios

### `GET /api/v1/intelligence/watchlists`
### `POST /api/v1/intelligence/watchlists`
### `PATCH /api/v1/intelligence/watchlists/{id}`

- cadastro e monitoramento de watchlist

### `GET /api/v1/intelligence/routes`
### `GET /api/v1/intelligence/convoys`
### `GET /api/v1/intelligence/roaming`
### `GET /api/v1/intelligence/sensitive-assets`

- consultas de eventos por algoritmo

### `POST /api/v1/intelligence/route-analysis`
### `POST /api/v1/intelligence/routes/analyze` (alias)

- analise de padrao de rota por placa

### `GET /api/v1/intelligence/route-timeline/{plate_number}`
### `GET /api/v1/intelligence/routes/{plate_number}/timeline` (alias)

- timeline operacional da placa

### `GET /api/v1/intelligence/routes/{plate_number}`

- retorna ultimo padrao de rota persistido ou calcula sob demanda

### `GET /api/v1/intelligence/cases`
### `POST /api/v1/intelligence/cases`
### `PATCH /api/v1/intelligence/cases/{id}`

- gestao de casos/dossies

### `GET /api/v1/intelligence/analytics/overview`
### `GET /api/v1/intelligence/analytics/observations-by-day`
### `GET /api/v1/intelligence/analytics/top-plates`
### `GET /api/v1/intelligence/analytics/unit-performance`

- indicadores operacionais para dashboard

## Auditoria

### `GET /api/v1/audit/logs`

- trilha auditavel de acoes sensiveis

## Observacoes importantes

- rate limiting baseline ja esta ativo no backend
- fallback estadual e intencional para desenvolvimento
- OpenAPI detalhada endpoint por endpoint esta em:
  - `docs/api/openapi-v1-detailed.yaml`
