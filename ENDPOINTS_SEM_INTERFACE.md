# F.A.R.O. - Endpoints Backend sem Interface Frontend

## Overview
Este documento lista todos os endpoints do backend que não possuem interface frontend completa ou estão subutilizados.

---

## 1. Endpoints Alerts (11 endpoints) - 4 sem interface

### Backend: `server-core/app/api/v1/endpoints/alerts.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/alerts/check-observation` | POST | **SEM INTERFACE** | Verifica alertas para nova observação |
| `/alerts/rules` | GET | **PARCIAL** | Usado em alerts-management |
| `/alerts/rules` | POST | **PARCIAL** | Formulário não implementado |
| `/alerts/rules/{id}` | PATCH | **PARCIAL** | Edição não implementada |
| `/alerts/rules/{id}` | DELETE | **PARCIAL** | Implementado |
| `/alerts/stats` | GET | **PARCIAL** | Usado em alerts-management |
| `/alerts/{id}/acknowledge` | POST | **SEM INTERFACE** | Confirmação de alerta |
| `/intelligence/alerts/aggregated` | POST | **COMPLETO** | alerts/page.tsx |

### Endpoints Sem Interface:

#### 1. POST `/alerts/check-observation`
**Função:** Verifica todas as condições de alerta para uma nova observação
**Uso:** Chamado automaticamente quando nova observação é criada
**Interface Necessária:** Painel de diagnóstico para testes manuais

#### 2. POST `/alerts/{id}/acknowledge` 
**Função:** Confirma/acknowledge um alerta específico
**Uso:** Para operadores confirmarem alertas
**Interface Necessária:** Botão de acknowledge na página de alertas

---

## 2. Endpoints Mobile (13 endpoints) - 3 sem interface

### Backend: `server-core/app/api/v1/endpoints/mobile.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/mobile/observations` | POST | **COMPLETO** | App Android |
| `/mobile/observations/{id}` | GET | **PARCIAL** | mobileApi.getObservation |
| `/mobile/observations/{id}/feedback` | GET | **SEM INTERFACE** | Feedback específico |
| `/mobile/history` | GET | **PARCIAL** | mobileApi.getHistory |
| `/mobile/shift-renewal` | POST | **SEM INTERFACE** | Renovação de turno |
| `/mobile/agent-location/batch` | POST | **SEM INTERFACE** | Batch de localizações |
| `/mobile/plate-validation` | POST | **PARCIAL** | OCR validation |
| `/mobile/plate-validation/batch` | POST | **PARCIAL** | Batch OCR |
| `/mobile/plate-suspicion-check` | POST | **PARCIAL** | Verificação de suspeita |
| `/mobile/approach-confirmation` | POST | **PARCIAL** | Confirmação de abordagem |
| `/mobile/assets/upload` | POST | **PARCIAL** | Upload de arquivos |
| `/mobile/assets/upload/progressive` | POST | **PARCIAL** | Upload progressivo |
| `/mobile/assets/{bucket}/{key}` | GET | **PARCIAL** | Download de assets |

### Endpoints Sem Interface:

#### 1. GET `/mobile/observations/{id}/feedback`
**Função:** Obtém feedback específico para uma observação
**Uso:** Agentes verem feedback de suas observações
**Interface Necessária:** Seção de feedback no detalhe da observação

#### 2. POST `/mobile/shift-renewal`
**Função:** Renovação de turno do agente
**Uso:** Início/fim de turno
**Interface Necessária:** Painel de gestão de turnos

#### 3. POST `/mobile/agent-location/batch`
**Função:** Envio em lote de localizações do agente
**Uso:** Sincronização de GPS
**Interface Necessária:** Dashboard de GPS em tempo real

---

## 3. Endpoints Suspicion (12 endpoints) - 8 sem interface

### Backend: `server-core/app/api/v1/endpoints/suspicion.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/suspicion/reports` | GET | **SEM INTERFACE** | Lista de relatórios |
| `/suspicion/reports` | POST | **SEM INTERFACE** | Criar relatório |
| `/suspicion/reports/{id}` | GET | **SEM INTERFACE** | Detalhe do relatório |
| `/suspicion/reports/{id}` | PATCH | **SEM INTERFACE** | Atualizar relatório |
| `/suspicion/reports/{id}/feedback` | POST | **SEM INTERFACE** | Feedback do relatório |
| `/suspicion/reports/{id}/second-approach` | POST | **SEM INTERFACE** | Segunda abordagem |
| `/suspicion/reports/{id}/close` | POST | **SEM INTERFACE** | Fechar relatório |
| `/suspicion/reports/{id}/reopen` | POST | **SEM INTERFACE** | Reabrir relatório |
| `/suspicion/reports/batch` | POST | **SEM INTERFACE** | Batch de relatórios |
| `/suspicion/reports/search` | GET | **SEM INTERFACE** | Busca avançada |
| `/suspicion/reports/statistics` | GET | **SEM INTERFACE** | Estatísticas |
| `/suspicion/reports/export` | GET | **SEM INTERFACE** | Exportação |

### Endpoints Sem Interface:

**TODOS os 12 endpoints não têm interface frontend!**
- Sistema completo de gestão de suspeitas não implementado
- Módulo inteiro disponível no backend sem UI

---

## 4. Endpoints Audit (7 endpoints) - 2 sem interface

### Backend: `server-core/app/api/v1/endpoints/audit.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/audit/logs` | GET | **COMPLETO** | audit/page.tsx |
| `/audit/geolocation` | GET | **COMPLETO** | audit/geolocation/page.tsx |
| `/audit/geolocation/export/{format}` | GET | **PARCIAL** | Botão exportar |
| `/audit/agent-movement/analyze` | POST | **COMPLETO** | agent-movement/page.tsx |
| `/audit/agent-movement/coverage-map` | POST | **COMPLETO** | agent-movement/page.tsx |
| `/audit/agent-movement/correlation` | POST | **COMPLETO** | agent-movement/page.tsx |
| `/audit/agent-movement/tactical-positioning` | POST | **COMPLETO** | agent-movement/page.tsx |

### Endpoints Parciais:

#### 1. GET `/audit/geolocation/export/{format}`
**Função:** Exportação de geolocalização em PDF/DOCX/XLSX
**Status:** Botão existe mas funcionalidade não implementada

---

## 5. Endpoints Agents (4 endpoints) - 2 sem interface

### Backend: `server-core/app/api/v1/endpoints/agents.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/agents` | GET | **SEM INTERFACE** | Lista de agentes |
| `/agents/{id}` | GET | **SEM INTERFACE** | Detalhe do agente |
| `/agents/{id}/status` | PATCH | **SEM INTERFACE** | Atualizar status |
| `/agents/{id}/location` | POST | **SEM INTERFACE** | Atualizar localização |

### Endpoints Sem Interface:

**TODOS os 4 endpoints não têm interface frontend!**
- Gestão completa de agentes não implementada

---

## 6. Endpoints Devices (2 endpoints) - 2 sem interface

### Backend: `server-core/app/api/v1/endpoints/devices.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/devices` | GET | **SEM INTERFACE** | Lista de dispositivos |
| `/devices/{id}/heartbeat` | POST | **SEM INTERFACE** | Heartbeat do dispositivo |

### Endpoints Sem Interface:

**TODOS os 2 endpoints não têm interface frontend!**
- Gestão de dispositivos não implementada

---

## 7. Endpoints Monitoring (3 endpoints) - 3 sem interface

### Backend: `server-core/app/api/v1/endpoints/monitoring.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/monitoring/health` | GET | **SEM INTERFACE** | Health check |
| `/monitoring/metrics` | GET | **SEM INTERFACE** | Métricas do sistema |
| `/monitoring/performance` | GET | **SEM INTERFACE** | Performance |

### Endpoints Sem Interface:

**TODOS os 3 endpoints não têm interface frontend!**
- Monitoramento do sistema não implementado

---

## 8. Endpoints Assets (1 endpoint) - 1 sem interface

### Backend: `server-core/app/api/v1/endpoints/assets.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/assets/{bucket}/{key}` | GET | **PARCIAL** | Acesso via URL helper |

---

## 9. Endpoints WebSocket (1 endpoint) - 1 sem interface

### Backend: `server-core/app/api/v1/endpoints/websocket.py`

| Endpoint | Método | Status Frontend | Observação |
|----------|--------|-----------------|------------|
| `/ws` | WebSocket | **SEM INTERFACE** | Tempo real |

---

## Resumo por Prioridade

### **ALTA PRIORIDADE** (Módulos inteiros sem UI)

1. **Suspicion Reports** (12 endpoints)
   - Sistema completo de gestão de suspeitas
   - Feedback, segunda abordagem, estatísticas
   - **Impacto:** Alto - funcionalidade crítica não exposta

2. **Agents Management** (4 endpoints)
   - Gestão de agentes, status, localização
   - **Impacto:** Médio - operações administrativas

3. **Devices Management** (2 endpoints)
   - Gestão de dispositivos móveis
   - **Impacto:** Médio - suporte técnico

### **MÉDIA PRIORIDADE** (Endpoints específicos)

1. **Alerts Acknowledge** (1 endpoint)
   - Confirmação de alertas
   - **Impacto:** Alto - operações do dia a dia

2. **Mobile Feedback** (1 endpoint)
   - Feedback para agentes
   - **Impacto:** Alto - ciclo fechado

3. **Shift Management** (1 endpoint)
   - Gestão de turnos
   - **Impacto:** Médio - operações

### **BAIXA PRIORIDADE** (Endpoints de suporte)

1. **Monitoring** (3 endpoints)
   - Health check, métricas
   - **Impacto:** Baixo - suporte técnico

2. **WebSocket** (1 endpoint)
   - Tempo real
   - **Impacto:** Médio - melhoria de UX

---

## Recomendações de Implementação

### Fase 1: Funcionalidades Críticas
1. **Suspicion Reports UI** - Criar página completa
2. **Alert Acknowledge** - Botão na página de alertas
3. **Mobile Feedback** - Seção no detalhe da observação

### Fase 2: Gestão Administrativa
1. **Agents Management** - CRUD completo de agentes
2. **Devices Management** - Gestão de dispositivos
3. **Shift Management** - Painel de turnos

### Fase 3: Monitoramento e Melhorias
1. **Monitoring Dashboard** - Saúde do sistema
2. **WebSocket Integration** - Tempo real
3. **Export Functions** - Botões funcionais

---

## Total de Endpoints Sem Interface: **38 de 107 (35%)**

**Status Atual:** 65% dos endpoints têm interface frontend
**Meta:** 90%+ de cobertura para produção

---

*Data da Análise: 2026-04-30*
*Próxima Revisão: Após implementação das melhorias*
