# Onboarding para novos devs

## Objetivo

Dar contexto rapido para entrar no F.A.R.O. com seguranca tecnica, sem quebrar a separacao entre os 3 componentes:

1. `mobile-agent-field`
2. `web-intelligence-console`
3. `server-core`

## 1. Entenda o produto antes do codigo

O F.A.R.O. nao e app unico. O ciclo operacional correto e:

`campo -> backend -> inteligencia -> backend -> retorno ao campo`

Principios obrigatorios:

- offline-first no mobile
- OCR assistido, nunca autonomo
- humano no loop na inteligencia
- backend explicavel e auditavel

## 2. Leitura obrigatoria (ordem recomendada)

1. [openmemory.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/openmemory.md)
2. [docs/README.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/docs/README.md)
3. [docs/architecture/evolution-log.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/docs/architecture/evolution-log.md)
4. [docs/api/contracts.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/docs/api/contracts.md)
5. [docs/data-model/model.md](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/docs/data-model/model.md)

## 3. Estado atual resumido

### Ja implementado

- fluxo mobile com login/refresh/logout real
- sessao multiperfil no APK para celular compartilhado por multiplos agentes
- sync em lote com retorno de `pending_feedback`
- upload de assets mobile para backend (`/mobile/observations/{id}/assets`)
- confirmacao de abordagem com retroalimentacao ao primeiro agente
- fallback dev para base estadual em adapter separado
- fila analitica web com revisao estruturada e feedback
- modulos web de rotas, comboio, roaming, ativo sensivel, watchlist, casos, auditoria
- worker assincorno em Redis Streams
- migration `0002` para indices operacionais e geoespaciais
- migration `0003` com base multiagencia (`agency`) e escopo por `agency_id`

### Parcial / pendente

- conexao real com base estadual
- pipeline de teste automatizado de integracao (backend + db + redis)
- build Android reproduzivel por wrapper versionado
- calibracao de algoritmos em dados reais

## 4. Setup local

### Backend

```bash
cd server-core
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd web-intelligence-console
npm install
npm run dev
```

### Infra

```bash
cd infra/docker
docker-compose up -d
```

## 5. Validacao minima antes de commit

### Web

```bash
cd web-intelligence-console
npm run type-check
```

### Backend

```bash
cd server-core
python -m compileall app
```

## 6. Arquivos chave por componente

### Backend

- [mobile.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/app/api/v1/endpoints/mobile.py)
- [intelligence.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/app/api/v1/endpoints/intelligence.py)
- [stream_worker.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/app/workers/stream_worker.py)
- [storage_service.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/app/services/storage_service.py)
- [0002_operational_indexes.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/alembic/versions/0002_operational_indexes.py)
- [0003_multi_tenant_agency_scope.py](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/server-core/alembic/versions/0003_multi_tenant_agency_scope.py)

### Web

- [src/app/page.tsx](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/web-intelligence-console/src/app/page.tsx)
- [src/app/queue/page.tsx](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/web-intelligence-console/src/app/queue/page.tsx)
- [src/app/services/api.ts](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/web-intelligence-console/src/app/services/api.ts)

### Mobile

- [MainActivity.kt](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/mobile-agent-field/app/src/main/java/com/faro/mobile/presentation/MainActivity.kt)
- [SyncWorker.kt](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/mobile-agent-field/app/src/main/java/com/faro/mobile/data/worker/SyncWorker.kt)
- [SessionRepository.kt](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/mobile-agent-field/app/src/main/java/com/faro/mobile/data/session/SessionRepository.kt)
- [SessionStore.kt](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/mobile-agent-field/app/src/main/java/com/faro/mobile/data/session/SessionStore.kt)
- [FaroMobileApi.kt](/c:/Users/msrov/OneDrive/Área%20de%20Trabalho/FARO/mobile-agent-field/app/src/main/java/com/faro/mobile/data/remote/FaroMobileApi.kt)

## 7. Identidade Visual BMRS (Obrigatório)

O sistema F.A.R.O. é **software oficial da Brigada Militar do Rio Grande do Sul**. Todo desenvolvedor deve respeitar:

### Cores institucionais

```css
/* Vermelho Militar BMRS */
--bmrs-red: #8B0000;         /* Principal */
--bmrs-red-dark: #5C0000;  /* Hover/fundo */
--bmrs-red-light: #A00000;  /* Bordas/divisores */

/* Dourado Institucional */
--bmrs-gold: #FFD700;       /* Destaque/acento */
--bmrs-gold-light: #FFEC8B; /* Hover suave */

/* Classificação */
--classified-red: #742a2a;  /* Alertas de sigilo */
```

### Elementos obrigatórios em toda tela

1. **Marca d'água** "SIGILOSO" rotacionada em fundo (3% opacidade)
2. **Badge de classificação** no header: "SISTEMA CLASSIFICADO"
3. **Matrícula do usuário** visível no header
4. **Footer institucional** com "BMRS - SSI"
5. **Termo de uso** acessível em `/terms`

### Componentes reutilizáveis

```typescript
// Header institucional
import { BMRSHeader } from "@/app/components/BMRSHeader";

// Footer institucional  
import { BMRSFooter } from "@/app/components/BMRSFooter";

// Console shell (sidebar + header completo)
import { ConsoleShell } from "@/app/components/console-shell";
```

### Nomenclatura e termos

- Usar **português formal** em todos os labels
- Evitar jargão técnico nas interfaces
- Preferir: "Fila de Triagem" ao invés de "Queue"
- Preferir: "Retorno ao Campo" ao invés de "Feedback"
- Preferir: "Abordagem" ao invés de "Approach"

## 8. Artefatos de desenvolvimento

O projeto deve manter "pegadas" de desenvolvimento governamental:

### Documentação técnica
- Documento SSI com numeração oficial (ex: SSI/2026/00047)
- Referências a legislação aplicável (Lei 12.527/2011, Lei 12.965/2014)
- Assinaturas digitais ICP-Brasil simuladas

### Versionamento
- Builds com timestamp oficial
- Ambiente claramente identificado (PRODUÇÃO/HOMOLOGAÇÃO)
- Hash de commit visível nos créditos

### Segurança
- Páginas marcadas como `robots: noindex, nofollow`
- Alertas de monitoramento em todas as interfaces
- Termos de responsabilidade com aceite obrigatório

## 9. Regras de mudanca

- nao misturar responsabilidades entre mobile, web e backend
- nao reverter alteracoes de outros sem alinhamento
- nao declarar pronto sem validacao executada
- nao esconder limitacao de ambiente ou build
- **manter identidade visual BMRS em todo novo componente**
- **nunca remover marca d'agua ou alertas de classificacao**
