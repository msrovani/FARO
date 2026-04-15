# Documento funcional para PM/Comando

## 1. O que e o F.A.R.O.

O F.A.R.O. e uma plataforma operacional de abordagem veicular com inteligencia integrada. Ele foi desenhado para:

- reduzir digitacao do policial em campo
- aumentar qualidade do informe
- devolver retorno util para quem lancou
- dar capacidade de triagem e decisao para inteligencia

## 2. Como a plataforma esta separada

### APK do agente de campo

Uso rapido em rua: capturar placa, confirmar OCR, registrar suspeicao e sincronizar mesmo com rede ruim.

### Modulo web da inteligencia

Mesa de triagem e decisao: fila analitica, revisao estruturada, watchlist, casos, rotas, feedback e auditoria.

### Backend e banco

Nucleo institucional: contratos, validacao, eventos, score analitico, trilha de auditoria e armazenamento de evidencias.

## 3. Fluxo operacional atual

1. agente registra observacao
2. backend retorna contexto imediato (inclusive suspeicao previa quando houver)
3. inteligencia recebe na fila e revisa com justificativa
4. inteligencia envia feedback ao campo
5. agente de campo pode confirmar abordagem
6. sistema retroalimenta o agente que abriu a primeira suspeicao

## 4. Integracao com base estadual (estado atual)

Ja existe fronteira tecnica pronta, mas a conexao real ainda nao foi implementada.

No ambiente de desenvolvimento, o retorno e controlado:

- `connected: false`
- `status: "no_connection"`
- `message: "sem conexao com base estadual"`

Isso permite testar o fluxo completo sem mascarar a ausencia da integracao oficial.

## 5. O que ja entrega valor operacional

- autenticacao real no app de campo
- sync em lote com retorno de feedback pendente
- upload de foto/audio vinculado a observacao
- fila analitica com score e revisao estruturada
- feedback ao campo por usuario ou equipe
- modulos de watchlist, casos, rotas, comboio, roaming e ativo sensivel
- auditoria consultavel

## 6. O que ainda falta para maturidade institucional

- conexao real com base estadual
- build Android reproduzivel no repositorio (`gradlew`)
- testes automatizados de integracao
- calibracao dos algoritmos com historico real
- observabilidade operacional por SLO/SLA

## 7. Indicadores recomendados para comando

Indicadores de valor (nao so volume):

- tempo medio ate triagem
- tempo medio ate feedback ao campo
- taxa de suspeicao confirmada x descartada
- taxa de OCR corrigido
- taxa de retorno lido pelo agente
- recorrencia por area sensivel e faixa horaria
- casos que evoluiram para ocorrencia vinculada

## 8. Criterio de sucesso operacional

O sistema so e considerado bem sucedido quando:

- o agente usa em poucos toques, mesmo em rede ruim
- a inteligencia reduz ruido e melhora decisao
- o comando enxerga produtividade util, nao volume bruto
- a cadeia de eventos fica auditavel de ponta a ponta
