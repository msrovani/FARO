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

## Simulação de Dados (Testes de Carga)

**Total de Dados Simulados:** ~768,000 registros

**Breakdown:**
- VehicleObservation: 536,941
- ImpossibleTravelEvent: 38,632
- WatchlistHit: 37,000
- ConvoyEvent: 37,059
- RouteAnomalyEvent: 37,000
- RoamingEvent: 37,000
- SensitiveAssetRecurrenceEvent: 36,900
- WatchlistEntry: 4,779
- RouteRegionOfInterest: 1,855
- SensitiveAssetZone: 1,855

**Configuração de Teste:**
- 100 eventos por algoritmo por rodada
- 5,000 observações mobile por rodada com lotes alternados (10, 50, 100, 200, etc.)
- Processamento em batches dinâmicos com estratégia adaptativa
- 0% taxa de erro em 271+ rodadas
- Latência média: ~14.46s por rodada (5,600 operações)

**Estratégia Adaptativa Implementada:**
- 4 modos de inserção (BATCH, PARALLEL_BATCH, COPY, INDIVIDUAL)
- Gatilhos dinâmicos baseados em congestionamento do banco, taxa de erro e latência
- Batch sizing dinâmico (10-200 itens)
- Monitoramento em tempo real de conexões ativas e queries bloqueadas

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
