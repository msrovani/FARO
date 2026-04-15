# UX operacional do APK

## Objetivo

Permitir registro rapido e confiavel em ambiente de rua, com baixa digitacao e alto contexto operacional.

## Principios de UX

- poucos toques
- botoes grandes
- contraste forte
- texto curto e legivel
- feedback de status claro
- operacao com rede ruim como padrao

## Fluxo principal

1. abrir registro de veiculo
2. capturar placa (camera/OCR assistido) ou editar manualmente
3. confirmar placa final
4. registrar suspeicao estruturada quando necessario
5. concluir com sync imediato ou fila offline

## Comportamentos obrigatorios

### OCR assistido

- OCR nunca fecha sozinho
- operador confirma/corrige sempre
- leitura bruta e contexto devem permanecer auditaveis

### Offline-first

- registro primeiro local, depois sync
- status de sync visivel (`pendente`, `sincronizado`, `falhou`)
- sem perda de dado em oscilacao de rede

### Retorno ao campo

- app recebe `pending_feedback` no sync
- historico exibe feedback pendente
- operador consegue marcar leitura

## Metadados coletados automaticamente

- timestamps local e servidor
- geolocalizacao e precisao
- heading/velocidade quando disponivel
- usuario/unidade/dispositivo
- conectividade e versao do app

## Estado atual

Ja integrado:

- auth real com sessao persistida
- sync com retorno de feedback
- upload de assets no fluxo de sincronizacao

Pendente:

- build Android reproduzivel via wrapper no repositorio
- validacao ampla em diversidade de hardware de camera
