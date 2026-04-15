# Seguranca e governanca

## Controles obrigatorios do F.A.R.O.

- autenticacao JWT com refresh
- autorizacao por perfil (RBAC)
- validacao de payload em fronteira de API
- trilha de auditoria para acoes sensiveis
- storage de evidencias fora do banco relacional
- separacao de acessos entre campo e inteligencia

## Perfis principais

- `field_agent`
- `intelligence`
- `supervisor`
- `admin`

## Controles implementados

- auth e refresh token no backend
- RBAC basico por endpoint
- audit log para operacoes sensiveis
- rate limiting baseline em middleware
- fallback seguro de barramento para nao derrubar fluxo principal
- upload de assets para S3-compatible com metadados e auditoria

## Controles pendentes para maturidade

- politica formal de retencao/expurgo por classificacao de dado
- controle de exportacao de dados sensiveis
- estrategia de revogacao global/forcada de sessao
- observabilidade de seguranca com alertas de abuso interno
- revisao criptografica e classificacao de sensibilidade por dominio

## Regra de confiabilidade de dado

Nenhum input e confiavel por default:

- OCR pode errar
- operador pode corrigir de forma incorreta
- integracao externa pode estar indisponivel ou inconsistente

Por isso, o sistema deve manter dado bruto + dado confirmado + contexto + justificativa.

## Governanca de decisao analitica

Toda decisao de inteligencia que confirma, descarta, escala ou vincula caso deve ter:

- justificativa textual
- ator responsavel
- timestamp
- historico de versao quando houver retificacao
