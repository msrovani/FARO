# Roadmap, epicos e sprints

## Estado de progresso por epico

### Epico 1 - Fundacao da plataforma

Status: `parcial avancado`

- monorepo com 3 componentes separado
- contratos base de auth/mobile/intelligence
- docker stack inicial
- pendente: padrao unico de CI para todos os componentes

### Epico 2 - APK do agente de campo

Status: `parcial avancado`

- telas principais e fluxo operacional basico
- autenticacao real com sessao persistida
- pendente: build reproduzivel com wrapper gradle no repo

### Epico 3 - OCR e captura

Status: `parcial`

- captura e OCR assistido evoluidos
- upload de assets implementado no sync pos-observacao
- pendente: bateria de testes em dispositivos diferentes e tuning de performance

### Epico 4 - Offline-first e sincronizacao

Status: `parcial avancado`

- sync em lote com idempotencia
- retorno de `pending_feedback` no sync
- pendente: cenarios de falha automatizados E2E (rede intermitente + retry)

### Epico 5 - Backend transacional

Status: `avancado`

- observacao, suspeicao, historico, feedback, assets
- endpoint de confirmacao de abordagem
- pendente: testes de regressao HTTP + banco

### Epico 6 - Motor de alertas

Status: `parcial`

- regras heuristicas e score composto ja alimentam fila
- pendente: governance completa de regras e calibracao institucional

### Epico 7 - Modulo web da inteligencia

Status: `avancado`

- dashboard, fila, detalhe, revisao, feedback
- watchlist, casos, audit, rotas, convoy, roaming, ativo sensivel
- pendente: refinamento de UX para alta densidade de dados

### Epico 8 - Reanalise e feedback

Status: `avancado`

- formulario estruturado de review
- templates de feedback
- envio para agente/equipe com leitura pendente
- pendente: estrategia de deprecacao do fluxo legado de feedback

### Epico 9 - Analise de rotas

Status: `parcial avancado`

- endpoints e modulos web ativos
- migration de indices geoespaciais aplicada no codigo
- pendente: validacao de qualidade com base real e tuning de thresholds

### Epico 10 - Metadados e BI

Status: `parcial`

- overview e indicadores iniciais no web
- pendente: camada de snapshots consolidados e dashboards de comando

### Epico 11 - Seguranca, auditoria e governanca

Status: `parcial avancado`

- RBAC basico, auditoria e rate limit baseline
- pendente: politicas de retencao, export control e hardening de seguranca interna

### Epico 12 - Hardening e producao

Status: `iniciado`

- worker assincorno e migration incremental
- pendente: CI/CD completo, observabilidade de producao e teste de carga

## Proximos sprints recomendados

### Sprint A - Integracoes e confiabilidade

- implementar conector real da base estadual (adapter ja pronto)
- incluir monitoramento de falhas por integracao externa
- validar fluxo operacional completo com fallback e com conexao ativa

### Sprint B - Qualidade de release

- adicionar `gradlew` no mobile e pipeline de build Android
- suite automatizada de integracao backend (Postgres/PostGIS/Redis)
- gate de qualidade em PR (lint/type-check/tests)

### Sprint C - Inteligencia aplicada

- calibrar os 7 algoritmos em dados reais (false positive/false negative)
- refinar score composto e explicacoes para analista
- elevar painis de BI com foco em produtividade util

### Sprint D - Governanca e producao

- politicas de classificacao e retencao de dados
- observabilidade por SLO operacional
- plano de rollout, playbook de incidente e checklist de go-live
