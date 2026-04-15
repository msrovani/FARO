# Visao geral da plataforma

## Objetivo operacional

O F.A.R.O. transforma registros de campo em decisao de inteligencia com retorno ao proprio agente, em um ciclo fechado:

1. campo registra
2. backend valida e enriquece
3. inteligencia reanalisa e decide
4. backend devolve feedback
5. campo recebe e aplica no proximo contato

## Componentes obrigatorios

### 1) APK mobile do agente de campo

Foco:

- velocidade de uso
- baixa digitacao
- OCR assistido
- operacao offline

### 2) Modulo web da inteligencia

Foco:

- triagem de suspeicoes
- revisao estruturada com justificativa
- correlacao de eventos
- watchlist, casos, rotas e feedback
- **visualizacoes de mapa para inteligencia policial**:
  - hotspots de criminalidade com filtros e timeline
  - cadastro/visualizacao de rotas suspeitas
  - previsao de rotas baseada em padroes historicos
  - alertas com filtros e acoes de aprovacao
  - eventos de convoy e roaming

### 3) Server/backend + banco

Foco:

- contratos versionados
- auth e RBAC
- persistencia transacional
- eventos internos
- score analitico explicavel
- trilha de auditoria

## Diretrizes tecnicas

- arquitetura backend em `modular monolith`
- sem mistura de responsabilidades entre campo e inteligencia
- sem dependencia de conectividade perfeita
- sem OCR autonomo como decisor
- sem score opaco sem explicacao legivel

## Estado atual resumido

Ja em operacao de desenvolvimento:

- auth real no mobile
- sync com feedback pendente
- upload de assets para storage
- confirmacao de abordagem
- console web com modulos analiticos principais
- worker assincorno com Redis Streams

Em evolucao:

- integracao estadual real (hoje fallback dev)
- testes automatizados de integracao
- build Android reproduzivel via wrapper no repo
