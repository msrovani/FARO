# Modelo de dados do F.A.R.O.

## Objetivo

Sustentar o ciclo completo:

- observacao de campo
- OCR assistido e correcao humana
- suspeicao estruturada
- reanalise da inteligencia
- feedback ao campo
- eventos analiticos e auditoria

## Tabelas principais (estado atual)

### Operacao de campo

- `vehicleobservation`
- `plateread`
- `suspicionreport`
- `syncqueue`
- `assets`
- `externalquery`

### Inteligencia

- `intelligencereview`
- `intelligencereviewversion`
- `feedbackevent` (legado)
- `analystfeedbackevent` (estruturado)
- `analystfeedbacktemplate`
- `watchlist`
- `watchlisthit`
- `intelligencecase`
- `caselink`

### Algoritmos e analytics

- `impossibletravelevent`
- `routeanomalyevent`
- `sensitiveassetzone`
- `sensitiveassetrecurrenceevent`
- `convoyevent`
- `roamingevent`
- `suspicionscore`
- `suspicionscorefactor`
- `routepattern`
- `algorithmrun`
- `algorithmexplanation`

### Governanca

- `user`
- `role`
- `unit`
- `device`
- `auditlog`

## Chaves e relacoes obrigatorias

- `vehicleobservation.user_id -> user.id`
- `vehicleobservation.device_id -> device.id`
- `plateread.observation_id -> vehicleobservation.id`
- `suspicionreport.observation_id -> vehicleobservation.id`
- `intelligencereview.suspicion_report_id -> suspicionreport.id`
- `analystfeedbackevent.observation_id -> vehicleobservation.id`
- `watchlisthit.watchlist_id -> watchlist.id`
- `caselink.case_id -> intelligencecase.id`

## Indices e geoespacial

### Ja implementado em migration `0002_operational_indexes`

- GiST em colunas geoespaciais relevantes
- compostos de consulta para:
  - placa + tempo
  - eventos analiticos por severidade/periodo
  - auditoria por ator/acao
  - feedback por usuario/alvo

## Diretriz de uso PostGIS

- `POINT` para local de observacao
- `LINESTRING` para corredor de rota
- `POLYGON` para bounding box e zonas sensiveis

## Lacunas atuais

- validacao de performance dos indices em volume real
- plano formal de particionamento para tabelas muito volumosas
- politica explicita de retenao/expurgo por classificacao de dado

## Observacao de governanca

Coexistem fluxo legado (`feedbackevent`) e fluxo estruturado (`analystfeedbackevent`).
O backend ja consolida leitura/escrita dos dois para compatibilidade, mas a estrategia de deprecacao do legado ainda precisa ser formalizada.
