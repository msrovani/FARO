# Arquitetura dos componentes

## Diagrama logico

```text
APK Mobile (campo)
  -> captura/OCR assistido
  -> persistencia local
  -> sync idempotente
  -> recebimento de feedback

Backend (modular monolith)
  -> auth/RBAC
  -> observacoes/suspeicoes
  -> eventos (Redis Streams)
  -> score e algoritmos
  -> auditoria e storage

Web Inteligencia
  -> dashboard
  -> fila analitica
  -> revisao estruturada
  -> watchlist/casos/rotas
  -> feedback ao campo
```

## Fluxos principais

### Fluxo 1 - Registro de campo

1. agente registra placa e contexto
2. app envia ou enfileira para sync offline
3. backend valida, persiste e retorna contexto imediato

### Fluxo 2 - Revisao da inteligencia

1. item entra na fila analitica
2. analista revisa com justificativa
3. sistema registra versao de review e auditoria
4. feedback e enviado para campo

### Fluxo 3 - Confirmacao de abordagem

1. agente confirma resultado da abordagem
2. backend atualiza trilha do registro
3. se houver suspeicao previa, primeiro agente recebe retorno

## Limites de responsabilidade

### Mobile

- captura e operacao rapida
- nada de regra analitica pesada local

### Web

- decisao humana, triagem e governanca
- nao replica fluxo de rua

### Backend

- contratos, seguranca e integracoes
- processamento online/offline
- explicabilidade e rastreabilidade
