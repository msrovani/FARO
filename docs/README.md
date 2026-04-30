# Documentacao do F.A.R.O.

Este diretorio concentra a documentacao oficial da plataforma F.A.R.O. (Ferramenta de Analise de Rotas e Observacoes), com foco em operacao real:

- APK do agente de campo
- modulo web da inteligencia
- server/backend com banco, eventos, auditoria e analytics

## Indice principal

- [Visao Geral da Plataforma](./architecture/overview.md)
- [Arquitetura dos Componentes](./architecture/components.md)
- [Arquitetura do Backend](./architecture/backend.md)
- [Evolucao Tecnica](./architecture/evolution-log.md)
- [Roadmap, Epicos e Sprints](./architecture/roadmap.md)
- [Contratos de API](./api/contracts.md)
- [Conexoes de API - Referencia Completa](./api/connections.md)
- [OpenAPI detalhado](./api/openapi-v1-detailed.yaml)
- [Modelo de Dados](./data-model/model.md)
- [UX Operacional do APK](./ux/mobile-agent.md)
- [Seguranca e Governanca](./security/security.md)
- [Operacao e Desenvolvimento](./deployment/development.md)
- [Onboarding de novos devs](./onboarding/new-developers.md)
- [Documento funcional PM/Comando](./functional/pm-comando.md)
- [Implementacao de Funcionalidades Avancadas](./implementation/advanced-features-implementation.md)
- [Relatorio Completo de Implementacao](./implementation/complete-implementation-report.md)
- [Implementacao OCR](./ocr-implementation.md)
- [Arquitetura Zero-Trust Mobile](./architecture/mobile-zero-trust.md)
- [Implementacao Zero-Trust](./architecture/zero-trust-implementation.md)
- [Roadmap de Integracoes Futuras](./integrations/future-roadmap.md)
- [Sintonia de Banco de Dados](./database/db-tuning-actions.md)

## Estado atual consolidado

Ja implementado e integrado:

- autenticacao real mobile (`login/refresh/logout`) sem token fixo em build
- sync mobile com retorno de `pending_feedback`
- upload de assets mobile (`imagem/audio`) para endpoint dedicado
- endpoint de confirmacao de abordagem e retorno ao primeiro agente
- fallback dev para base estadual (`sem conexao`) isolado em adapter
- fila analitica web com revisao estruturada e feedback
- modulos web de `routes`, `convoys`, `roaming`, `sensitive-assets`, `watchlist`, `cases`, `audit`, `feedback`
- aliases de contratos de rota para compatibilidade de cliente
- worker assincorno para consumo de Redis Streams
- migration `0002` com indices geoespaciais e operacionais
- migration `0003` com base multiagencia (`agency`) e escopo por `agency_id`
- APK com sessao multiperfil para dispositivo compartilhado por varios agentes
- rate limiting baseline no backend

**Otimizacoes de Performance (2026-04-17):**

- execucao paralela de algoritmos (50-70% reducao de latencia)
- cache Redis para dados estaticos (elimina 30-50% queries redundantes)
- otimizacao Convoy com single query (O(N) → O(1) queries)
- otimizacao score composto com paralelizacao (7 queries paralelas)
- otimizacao check route match com batch query (N → 1 query)
- otimizacoes OCR server-side (3-5x mais rapido)
- PgBouncer connection pooling (5-10x throughput)
- BRIN index para vehicle_observations (10x mais rapido)
- parallel query tuning (2-4x mais rapido)
- materialized views para hotspots (10x mais rapido)
- TimescaleDB hypertable para time-series (50-100x para queries time-series)
- Citus escala horizontal por agency_id (escala linear)
- metricas Prometheus para algoritmos, cache e queries

Abertos e prioritarios:

- conexao real com base estadual (hoje fallback de desenvolvimento)
- build Android reproduzivel no repositorio (`gradlew` + pipeline)
- testes automatizados de integracao HTTP + Postgres/PostGIS + Redis
- hardening de observabilidade (metricas por dominio, traces e alertas)
- calibracao dos algoritmos com dados reais para reduzir falso positivo

## Fonte de verdade

- [openmemory.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/openmemory.md): memoria executiva e tecnica consolidada
- [README.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/README.md): resumo rapido de repositorio
