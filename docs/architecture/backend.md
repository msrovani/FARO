# Arquitetura do backend

## Estilo arquitetural

O `server-core` segue `modular monolith`, com fronteiras internas claras e extraivel no futuro, sem microservico prematuro.

## Modulos de dominio

- auth
- users
- devices
- observations
- plate_reads / ocr
- suspicions
- alerts
- intelligence_reviews
- route_analysis
- feedback
- integrations
- analytics
- audit
- storage
- workers / sync
- **suspicious_routes** (cadastro de rotas suspeitas)
- **hotspot_analysis** (analise de hotspots de criminalidade)
- **route_prediction** (previsao de rotas baseada em padroes)
- **alert_service** (alertas automaticos)

## Capacidades ja implementadas

- auth JWT com refresh
- observacao com idempotencia de cliente
- suspeicao estruturada
- sync em lote com retorno de feedback pendente
- confirmacao de abordagem
- upload de assets para storage S3-compatible
- fila de inteligencia e revisao versionada
- watchlist, casos e analytics overview
- auditoria consultavel
- publicacao e consumo de eventos Redis Streams
- **cadastro de rotas suspeitas (SuspiciousRoute) com PostGIS**
- **analise de hotspots de criminalidade com clustering espacial**
- **previsao de rotas baseada em padroes historicos**
- **servico de alertas automaticos para rotas recorrentes**
- **expansao de ConvoyEvent com padroes temporais**
- **expansao de RoamingEvent com padroes de area**

## Capacidades de robustez aplicadas

- fallback seguro para indisponibilidade temporaria de Redis no publish
- worker dedicado para consumo assincorno
- rate limiting baseline por middleware
- migration de indices geoespaciais e operacionais (`0002`)
- aliases de rota para evitar quebra de clientes

## Integracoes externas

Base estadual:

- adapter separado pronto para conexao real
- no ambiente dev retorna fallback `sem conexao`

Regra:

- nao espalhar chamadas externas pelos endpoints
- manter integracao centralizada em modulo/adapters

## Pendencias estruturais

- testes automatizados de integracao em ambiente com Postgres/PostGIS/Redis
- calibracao dos algoritmos com dado real
- plano formal de deprecacao do fluxo legado de feedback
- politicas de retencao/exportacao e classificacao de sensibilidade
