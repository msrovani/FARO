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
- [OpenAPI detalhado](./api/openapi-v1-detailed.yaml)
- [Modelo de Dados](./data-model/model.md)
- [UX Operacional do APK](./ux/mobile-agent.md)
- [Seguranca e Governanca](./security/security.md)
- [Operacao e Desenvolvimento](./deployment/development.md)
- [Onboarding de novos devs](./onboarding/new-developers.md)
- [Documento funcional PM/Comando](./functional/pm-comando.md)
- [ADR 0001 - Modular Monolith](./adr/0001-modular-monolith.md)
- [ADR 0002 - Camera/OCR/Rotas](./adr/0002-camerax-mlkit-route-analysis.md)
- [Implementacao de Funcionalidades Avancadas](./implementation/advanced-features-implementation.md)
- [Relatorio Completo de Implementacao](./implementation/complete-implementation-report.md)

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

Abertos e prioritarios:

- conexao real com base estadual (hoje fallback de desenvolvimento)
- build Android reproduzivel no repositorio (`gradlew` + pipeline)
- testes automatizados de integracao HTTP + Postgres/PostGIS + Redis
- hardening de observabilidade (metricas por dominio, traces e alertas)
- calibracao dos algoritmos com dados reais para reduzir falso positivo

## Fonte de verdade

- [openmemory.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/openmemory.md): memoria executiva e tecnica consolidada
- [README.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/README.md): resumo rapido de repositorio
