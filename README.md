# F.A.R.O.

F.A.R.O. (Ferramenta de Analise de Rotas e Observacoes) e uma plataforma integrada para abordagem veicular, inteligencia operacional e protecao do ativo, com 3 componentes obrigatorios e separados:

1. `mobile-agent-field` (APK do agente de campo)
2. `web-intelligence-console` (modulo web da inteligencia)
3. `server-core` (backend + banco + eventos)

## Estado atual consolidado

Ja implementado:

- fluxo mobile com autenticacao real (`login/refresh/logout`)
- sync em lote com retorno de `pending_feedback`
- upload de assets mobile (`imagem/audio`) para backend
- confirmacao de abordagem com retorno ao agente original da suspeicao
- fallback dev para base estadual em adapter dedicado
- fila analitica web com revisao estruturada e feedback
- modulos web de rota, comboio, roaming, ativo sensivel, watchlist, casos, auditoria e feedback
- worker assincorno de Redis Streams
- migration de indices geoespaciais e operacionais (`0002_operational_indexes`)
- rate limiting baseline no backend
- **visualizacoes de mapa para inteligencia policial** (frontend web):
  - componente base de mapa OpenStreetMap (react-map-gl)
  - marcadores para hotspots, rotas suspeitas e alertas
  - pagina de visualizacao de hotspots com filtros e timeline
  - pagina de cadastro/visualizacao de rotas suspeitas
  - pagina de previsao de rotas baseada em padroes historicos
  - pagina de alertas com filtros e acoes de aprovacao
  - pagina de eventos de convoy
  - pagina de eventos de roaming
- **funcionalidades avancadas de backend**:
  - cadastro de rotas suspeitas (SuspiciousRoute) com PostGIS
  - analise de hotspots de criminalidade com clustering espacial
  - previsao de rotas baseada em padroes historicos
  - servico de alertas automaticos para rotas recorrentes
  - expansao de ConvoyEvent com padroes temporais e analise de rotas
  - expansao de RoamingEvent com padroes de area e tracking de recorrencia

Pendente:

- conector real com base estadual
- build Android reproduzivel no repositorio (wrapper `gradlew`)
- testes automatizados de integracao end-to-end
- hardening de observabilidade e governanca de producao
- integracao frontend com endpoints reais (substituir mock data)
- criacao de endpoints para ConvoyEvents e RoamingEvents no backend

## Estrutura

- `mobile-agent-field/`
- `web-intelligence-console/`
- `server-core/`
- `infra/`
- `database/`
- `docs/`
- `openmemory.md`

## Documentacao

- [Memoria tecnica consolidada](./openmemory.md)
- [Indice de documentacao](./docs/README.md)

## Validacao executada recentemente

- `npm run type-check` em `web-intelligence-console` (OK)

Limitacoes de ambiente desta sessao:

- `npm run build` no web com falha `spawn EPERM`
- runtime Python e Java/Gradle indisponiveis para validacoes locais completas
