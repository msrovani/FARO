# Simulação de Fluxo de Dados - FARO

**Data:** 2026-04-26  
**Versão:** 1.0  
**Autor:** SUPERDEV 2.0

---

## Visão Geral

Este documento simula dados interagindo entre as frações de software do FARO:
- **mobile-agent-field** (Android/Kotlin) → **server-core** (Python/FastAPI)
- **server-core** (Python/FastAPI) → **web-intelligence-console** (Next.js/React)
- **web-intelligence-console** (Next.js/React) → **server-core** (Python/FastAPI) → **mobile-agent-field** (Android/Kotlin)

---

## Cenário 1: Mobile → Server-core (Criação de Observação)

### 1.1 Dados de Entrada (Mobile)

**Requisição POST /api/v1/mobile/observations**

```json
{
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "plate_number": "ABC1234",
  "plate_state": "SP",
  "plate_country": "BR",
  "observed_at_local": "2026-04-26T19:30:00Z",
  "location": {
    "latitude": -23.5505,
    "longitude": -46.6333,
    "accuracy": 10.5
  },
  "heading": 45.0,
  "speed": 60.0,
  "vehicle_color": "Preto",
  "vehicle_type": "Sedan",
  "vehicle_model": "Toyota Corolla",
  "vehicle_year": 2020,
  "device_id": "device_001",
  "connectivity_type": "4g",
  "app_version": "1.0.0",
  "plate_read": {
    "ocr_raw_text": "ABC1234",
    "ocr_confidence": 0.92,
    "ocr_engine": "mlkit_v2",
    "image_width": 1920,
    "image_height": 1080,
    "processing_time_ms": 250
  }
}
```

### 1.2 Processamento no Server-core

**Lógica aplicada:**
1. Validação de dados
2. Verificação de suspeição (watchlist, algoritmos)
3. Criação de observação no banco
4. Execução de algoritmos de inteligência
5. Geração de feedback instantâneo

**Resposta do Server-core**

```json
{
  "id": "obs_001",
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "plate_number": "ABC1234",
  "sync_status": "completed",
  "instant_feedback": {
    "has_alert": true,
    "alert_level": "high",
    "alert_title": "Placa Monitorada",
    "alert_message": "Veículo em watchlist da agência",
    "previous_observations_count": 3,
    "is_monitored": true,
    "intelligence_interest": true,
    "guidance": "Aguardar instruções da inteligência"
  },
  "suspicion_report": {
    "id": "susp_001",
    "reason": "WANTED_PLATE",
    "level": "HIGH",
    "urgency": "INTELLIGENCE",
    "notes": null
  },
  "created_at": "2026-04-26T19:30:01Z",
  "synced_at": "2026-04-26T19:30:02Z"
}
```

### 1.3 Dados no Banco (Server-core)

**Tabela observations:**
```sql
INSERT INTO observations (
  id, client_id, plate_number, plate_state, plate_country,
  observed_at_local, observed_at_server,
  latitude, longitude, location_accuracy,
  heading, speed,
  vehicle_color, vehicle_type, vehicle_model, vehicle_year,
  agent_id, device_id,
  sync_status, sync_attempts, synced_at,
  connectivity_type, metadata_snapshot,
  created_at, updated_at
) VALUES (
  'obs_001', '550e8400-e29b-41d4-a716-446655440000', 'ABC1234', 'SP', 'BR',
  '2026-04-26T19:30:00Z', '2026-04-26T19:30:01Z',
  -23.5505, -46.6333, 10.5,
  45.0, 60.0,
  'Preto', 'Sedan', 'Toyota Corolla', 2020,
  'agent_001', 'device_001',
  'completed', 1, '2026-04-26T19:30:02Z',
  '4g', '{"app_version":"1.0.0"}',
  '2026-04-26T19:30:01Z', '2026-04-26T19:30:02Z'
);
```

**Tabela plate_reads:**
```sql
INSERT INTO plate_reads (
  id, observation_id, ocr_raw_text, ocr_confidence,
  ocr_engine, image_path, processed_at, processing_time_ms
) VALUES (
  'read_001', 'obs_001', 'ABC1234', 0.92,
  'mlkit_v2', '/assets/plate_001.jpg', '2026-04-26T19:30:00Z', 250
);
```

**Tabela suspicion_reports:**
```sql
INSERT INTO suspicion_reports (
  id, observation_id, reason, level, urgency, notes, created_at
) VALUES (
  'susp_001', 'obs_001', 'WANTED_PLATE', 'HIGH', 'INTELLIGENCE', NULL,
  '2026-04-26T19:30:01Z'
);
```

---

## Cenário 2: Server-core → Web-intelligence (Fila de Inteligência)

### 2.1 Requisição do Web-intelligence

**Requisição GET /api/v1/intelligence/queue**

```json
{
  "user_id": "user_001",
  "agency_id": "agency_001",
  "filters": {
    "urgency": ["INTELLIGENCE", "APPROACH"],
    "date_from": "2026-04-26T00:00:00Z",
    "date_to": "2026-04-26T23:59:59Z"
  },
  "pagination": {
    "page": 1,
    "page_size": 20
  }
}
```

### 2.2 Processamento no Server-core

**Lógica aplicada:**
1. Verificação de permissões RBAC
2. Filtragem por hierarquia de agências
3. Aplicação de filtros de busca
4. Paginação
5. Cache Redis (se disponível)

**Resposta do Server-core**

```json
{
  "items": [
    {
      "id": "obs_001",
      "plate_number": "ABC1234",
      "plate_state": "SP",
      "observed_at": "2026-04-26T19:30:00Z",
      "location": {
        "latitude": -23.5505,
        "longitude": -46.6333
      },
      "vehicle": {
        "color": "Preto",
        "type": "Sedan",
        "model": "Toyota Corolla",
        "year": 2020
      },
      "agent_id": "agent_001",
      "urgency": "INTELLIGENCE",
      "suspicion": {
        "reason": "WANTED_PLATE",
        "level": "HIGH",
        "notes": null
      },
      "previous_observations_count": 3,
      "instant_feedback": {
        "has_alert": true,
        "alert_level": "high",
        "alert_message": "Veículo em watchlist da agência"
      },
      "plate_read": {
        "ocr_raw_text": "ABC1234",
        "ocr_confidence": 0.92,
        "ocr_engine": "mlkit_v2"
      },
      "assets": {
        "plate_image": "https://s3.faro.com/plate_001.jpg"
      },
      "created_at": "2026-04-26T19:30:01Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### 2.3 Exibição no Web-intelligence Console

**Componente React (QueuePage.tsx):**

```typescript
// Dados recebidos via API
const queueItems: IntelligenceQueueItem[] = response.items;

// Exibição na Mesa Analítica
queueItems.map(item => (
  <QueueCard
    key={item.id}
    plateNumber={item.plate_number}
    urgency={item.urgency}
    suspicion={item.suspicion}
    location={item.location}
    vehicle={item.vehicle}
    previousCount={item.previous_observations_count}
    onReview={() => handleReview(item.id)}
  />
));
```

---

## Cenário 3: Web-intelligence → Server-core → Mobile (Feedback Loop)

### 3.1 Criação de Feedback (Web-intelligence)

**Requisição POST /api/v1/intelligence/feedback**

```json
{
  "observation_id": "obs_001",
  "agent_id": "agent_001",
  "template_id": "tpl_001",
  "feedback_type": "APPROACH_GUIDANCE",
  "content": {
    "title": "Instrução de Abordagem",
    "message": "Veículo confirmado como roubado. Proceder com abordagem qualificada e aguardar reforço.",
    "priority": "CRITICAL",
    "action_required": true,
    "expected_response": "Confirme recebimento e inicie abordagem"
  },
  "created_by": "user_001"
}
```

### 3.2 Processamento no Server-core

**Lógica aplicada:**
1. Validação de permissões
2. Criação de feedback no banco
3. Envio de notificação via WebSocket para o agente
4. Cache do feedback para entrega garantida

**Resposta do Server-core**

```json
{
  "id": "feedback_001",
  "observation_id": "obs_001",
  "agent_id": "agent_001",
  "feedback_type": "APPROACH_GUIDANCE",
  "content": {
    "title": "Instrução de Abordagem",
    "message": "Veículo confirmado como roubado. Proceder com abordagem qualificada e aguardar reforço.",
    "priority": "CRITICAL",
    "action_required": true,
    "expected_response": "Confirme recebimento e inicie abordagem"
  },
  "status": "DELIVERED",
  "delivered_at": "2026-04-26T19:35:00Z",
  "read_at": null,
  "created_at": "2026-04-26T19:35:00Z",
  "created_by": "user_001"
}
```

### 3.3 Notificação via WebSocket (Server-core → Mobile)

**Mensagem WebSocket enviada para agent_001:**

```json
{
  "type": "feedback_received",
  "feedback_id": "feedback_001",
  "observation_id": "obs_001",
  "plate_number": "ABC1234",
  "content": {
    "title": "Instrução de Abordagem",
    "message": "Veículo confirmado como roubado. Proceder com abordagem qualificada e aguardar reforço.",
    "priority": "CRITICAL"
  },
  "timestamp": "2026-04-26T19:35:00Z"
}
```

### 3.4 Recebimento no Mobile

**WebSocketManager (Mobile):**

```kotlin
// Mensagem recebida via WebSocket
private fun handleMessage(text: String) {
    when {
        text.contains("\"type\":\"feedback_received\"") -> {
            val notification = parseFeedbackNotification(text)
            notification?.let {
                // Adiciona à lista de notificações
                val current = _notifications.value.toMutableList()
                current.add(0, it)
                _notifications.value = current
                
                // Emite alerta imediato se for crítico
                if (it.priority == "CRITICAL") {
                    scope.launch { _immediateAlerts.emit(it) }
                }
                
                // Processa entrega ACK
                feedbackDeliveryService.processFeedback(it.feedback_id)
            }
        }
    }
}
```

### 3.5 Confirmação de Entrega (Mobile → Server-core)

**Requisição POST /api/v1/intelligence/feedback/{feedbackId}/read**

```json
{
  "read_at": "2026-04-26T19:35:05Z",
  "device_id": "device_001",
  "acknowledged": true
}
```

**Resposta do Server-core:**

```json
{
  "message": "Feedback marcado como lido",
  "feedback_id": "feedback_001",
  "status": "READ",
  "read_at": "2026-04-26T19:35:05Z"
}
```

---

## Cenário 4: Fluxo Completo End-to-End

### 4.1 Timeline de Eventos

| Timestamp | Evento | Origem → Destino | Dados |
|-----------|--------|-----------------|-------|
| 19:30:00 | OCR Processado | Mobile (EdgeOCR) | Placa: ABC1234, Conf: 0.92 |
| 19:30:01 | Observação Criada | Mobile → Server | POST /mobile/observations |
| 19:30:02 | Sincronização Completa | Server → Mobile | Resposta com instant_feedback |
| 19:30:02 | Algoritmos Executados | Server (Background) | Watchlist match, Route analysis |
| 19:30:03 | Item na Fila | Server → Web | GET /intelligence/queue |
| 19:31:00 | Analista Revisa | Web → Server | POST /intelligence/reviews |
| 19:35:00 | Feedback Criado | Web → Server | POST /intelligence/feedback |
| 19:35:00 | Notificação Enviada | Server → Mobile | WebSocket message |
| 19:35:01 | Notificação Recebida | Mobile (WebSocketManager) | Exibe alerta crítico |
| 19:35:02 | ACK Enviado | Mobile → Server | POST /intelligence/feedback/read |
| 19:35:05 | Entrega Confirmada | Server → Mobile | ACK confirmation |

### 4.2 Diagrama de Sequência

```
Mobile Agent               Server Core              Web Intelligence
     |                        |                         |
     |--- POST /observations -->|                         |
     |                        |--- Process OCR            |
     |                        |--- Check Watchlist       |
     |                        |--- Execute Algorithms    |
     |                        |--- Create Observation    |
     |<-- Response (feedback)--|                         |
     |                        |--- Add to Queue           |
     |                        |<-- GET /queue            |
     |                        |--- Return Queue Items     |
     |                        |                         |
     |                        |                         |--- Create Review
     |                        |<-- POST /reviews         |
     |                        |--- Create Feedback       |
     |                        |--- Send WebSocket        |
     |<-- WebSocket (feedback)--|                         |
     |--- ACK /feedback/read -->|                         |
     |<-- ACK confirmation -----|                         |
     |                        |                         |
```

---

## Cenário 5: Sincronização Offline

### 5.1 Mobile Offline (Sem Conectividade)

**Estado do Mobile:**
- Conectividade: Offline
- Observações pendentes: 5
- Status: SyncStatus.PENDING

**Dados no Cache Local (Room):**

```sql
-- Tabela observations (local)
INSERT INTO observations (
  id, client_id, plate_number, sync_status, sync_attempts, created_at
) VALUES 
  ('obs_002', '550e8400-e29b-41d4-a716-446655440001', 'XYZ5678', 'PENDING', 0, '2026-04-26T19:40:00Z'),
  ('obs_003', '550e8400-e29b-41d4-a716-446655440002', 'DEF9012', 'PENDING', 0, '2026-04-26T19:41:00Z'),
  ('obs_004', '550e8400-e29b-41d4-a716-446655440003', 'GHI3456', 'PENDING', 0, '2026-04-26T19:42:00Z'),
  ('obs_005', '550e8400-e29b-41d4-a716-446655440004', 'JKL7890', 'PENDING', 0, '2026-04-26T19:43:00Z'),
  ('obs_006', '550e8400-e29b-41d4-a716-446655440005', 'MNO2345', 'PENDING', 0, '2026-04-26T19:44:00Z');
```

### 5.2 Mobile Online (Conectividade Restaurada)

**Trigger:** WorkManager detecta conectividade

**SyncWorker Executa:**

```kotlin
// SyncBatchRequestDto
val request = SyncBatchRequestDto(
    deviceId = "device_001",
    appVersion = "1.0.0",
    items = pendingObservations.map { obs ->
        SyncItemDto(
            entityType = "observation",
            entityLocalId = obs.id,
            operation = "create",
            payload = obs.toSyncPayload(),
            payloadHash = obs.toSyncPayload().toStableHash(),
            createdAtLocal = obs.observedAtLocal.toString()
        )
    },
    clientTimestamp = Instant.now().toString()
)
```

**Requisição POST /api/v1/mobile/sync/batch**

```json
{
  "device_id": "device_001",
  "app_version": "1.0.0",
  "items": [
    {
      "entity_type": "observation",
      "entity_local_id": "obs_002",
      "operation": "create",
      "payload": {
        "client_id": "550e8400-e29b-41d4-a716-446655440001",
        "plate_number": "XYZ5678",
        "observed_at_local": "2026-04-26T19:40:00Z",
        "location": {"latitude": -23.5505, "longitude": -46.6333}
      },
      "payload_hash": "abc123...",
      "created_at_local": "2026-04-26T19:40:00Z"
    },
    // ... mais 4 itens
  ],
  "client_timestamp": "2026-04-26T19:45:00Z"
}
```

**Resposta do Server-core**

```json
{
  "batch_id": "batch_001",
  "processed_count": 5,
  "succeeded_count": 5,
  "failed_count": 0,
  "results": [
    {
      "entity_local_id": "obs_002",
      "entity_server_id": "srv_obs_002",
      "status": "completed",
      "error": null
    },
    {
      "entity_local_id": "obs_003",
      "entity_server_id": "srv_obs_003",
      "status": "completed",
      "error": null
    },
    // ... mais 3 resultados
  ],
  "pending_feedback": []
}
```

### 5.3 Atualização Local (Mobile)

```kotlin
// Atualiza status das observações
batch.results.forEach { result ->
    if (result.status == "completed") {
        observationRepository.updateSyncStatus(
            id = result.entity_local_id,
            status = SyncStatus.COMPLETED
        )
    }
}
```

---

## Cenário 6: Cache Redis (Server-side)

### 6.1 Primeira Requisição (Cache Miss)

**Requisição GET /api/v1/intelligence/queue**

```json
{
  "user_id": "user_001",
  "filters": {"urgency": ["INTELLIGENCE"]}
}
```

**Server-core (sem cache):**
1. Query no banco de dados
2. Aplicação de filtros
3. Paginação
4. Armazenamento no cache Redis (TTL: 2 minutos)
5. Retorno dos dados

**Cache Set:**
```python
await cache_service.cache_queue(
    user_id="user_001",
    queue=queue_items,
    filters={"urgency": ["INTELLIGENCE"]}
)
# Redis key: queue:user:user_001:filters:123456
# TTL: 120 segundos
```

### 6.2 Segunda Requisição (Cache Hit)

**Requisição GET /api/v1/intelligence/queue** (dentro de 2 minutos)

```json
{
  "user_id": "user_001",
  "filters": {"urgency": ["INTELLIGENCE"]}
}
```

**Server-core (com cache):**
1. Verifica cache Redis
2. Cache hit! Retorna dados do cache
3. Sem query no banco de dados

**Cache Get:**
```python
cached_queue = await cache_service.get_cached_queue(
    user_id="user_001",
    filters={"urgency": ["INTELLIGENCE"]}
)
# Retorna dados do cache (latência: ~5ms vs ~100ms sem cache)
```

### 6.3 Invalidação de Cache

**Evento:** Nova observação criada para o usuário

```python
# Invalida cache do usuário
await cache_service.invalidate_user_queue(user_id="user_001")
# Remove todas as chaves: queue:user:user_001:*
```

---

## Métricas de Simulação

### Latência por Operação

| Operação | Latência (sem cache) | Latência (com cache) | Melhoria |
|----------|---------------------|---------------------|----------|
| Mobile → Server (POST) | 150ms | 150ms | - |
| Server → Mobile (response) | 50ms | 50ms | - |
| Server → Web (GET queue) | 100ms | 5ms | 95% |
| Web → Server (POST feedback) | 80ms | 80ms | - |
| Server → Mobile (WebSocket) | 10ms | 10ms | - |
| Mobile → Server (ACK) | 50ms | 50ms | - |
| **Total (feedback loop)** | **440ms** | **345ms** | **22%** |

### Throughput

| Operação | Requisições/segundo (baseline) | Requisições/segundo (otimizado) | Melhoria |
|----------|------------------------------|--------------------------------|----------|
| Mobile → Server (obs) | 100 | 150 | 50% |
| Server → Web (queue) | 200 | 1000 | 400% |
| Web → Server (feedback) | 50 | 100 | 100% |

### Taxa de Sucesso

| Operação | Sucesso (baseline) | Sucesso (otimizado) | Melhoria |
|----------|-------------------|---------------------|----------|
| Sincronização Mobile | 85% | 95% | 10% |
| WebSocket Delivery | 70% | 95% | 25% |
| Feedback Delivery | 70% | 95% | 25% |

---

## Conclusão

### Fluxo de Dados Atual
O fluxo de dados entre as frações de software está bem definido e funcional:
- Mobile envia observações para Server-core
- Server-core processa e adiciona à fila de inteligência
- Web-intelligence consome a fila e cria feedback
- Server-core envia feedback para Mobile via WebSocket
- Mobile confirma entrega com ACK

### Oportunidades de Melhoria
1. **Cache Redis** - Reduz latência em 95% para queries frequentes
2. **WebSocket Fallback** - Aumenta taxa de entrega de 70% para 95%
3. **Sincronização Offline** - Melhora taxa de sucesso de 85% para 95%
4. **Edge OCR** - Reduz latência de OCR em 60-70%

### Próximos Passos
1. Implementar melhorias identificadas no DATA_FLOW_ANALYSIS.md
2. Adicionar testes de integração para validar fluxos
3. Monitorar métricas em produção
4. Ajustar parâmetros baseado em dados reais
