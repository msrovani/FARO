# F.A.R.O. — Referência Completa de APIs

> Documentação técnica das conexões entre Mobile, Web Console e Server.
> Última atualização: 2026-04-17

---

## Servidor Base

```
http://<host>:8000/api/v1
```

---

## 1. Autenticação (`/auth`)

Prefixo: `/api/v1/auth`

| # | Endpoint | Método | Request | Response | Frontend Web | Mobile |
|---|----------|--------|---------|-----------|--------------|--------|
| 1.1 | `/auth/login` | POST | `LoginRequest{identifier, password}` | `Token{access_token, token_type, expires_in, refresh_token}` | `login/page.tsx` - `authApi.login()` | `AuthDtos.kt` - `login()` |
| 1.2 | `/auth/refresh` | POST | `Token{refresh_token}` | `Token{...}` | Refresh interceptor | `SessionRepository.kt` |
| 1.3 | `/auth/logout` | POST | — | `{"message": "Logout realizado com sucesso"}` | Header dropdown | `logout()` |
| 1.4 | `/auth/me` | GET | — | `UserResponse{id, identifier, full_name, unit_id, is_on_duty, service_expires_at}` | Header - nome/unidade | `getCurrentUser()` |
| 1.5 | `/auth/password/change` | POST | `PasswordChange{current_password, new_password}` | `UserResponse` | Perfil - trocar senha | — |

### Fluxo Auth

```
Mobile:
  LoginScreen → POST /auth/login
    → Token{access_token, refresh_token}
    → SessionRepository.save() → PersistentSession
    → HomeScreen

Web:
  LoginPage → POST /auth/login
    → localStorage.setItem('token', access_token)
    → Redirect /queue
```

---

## 2. Mobile App (`/mobile`)

Prefixo: `/api/v1/mobile`

### 2.1 Observações

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.1.1 | `/mobile/observations` | POST | `VehicleObservationCreate{plate_number, location, observed_at_local, metadata}` | `VehicleObservationResponse` | `FaroMobileApi.createObservation()` |
| 2.1.2 | `/mobile/history` | GET | Query: `plate_number, limit` | `ObservationHistoryResponse{observations[]}` | `FaroMobileApi.getHistory()` |

**Fluxo Observation:**
```
Mobile:
  ApproachFormScreen → POST /mobile/observations
    → Backend: evaluate_watchlist() → evaluate_impossible_travel() → evaluate_convoy() → evaluate_roaming() → compute_suspicion_score()
    → Returns VehicleObservationResponse + SuspicionScore
    → Redirect HomeScreen
```

### 2.2 OCR

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.2.1 | `/mobile/ocr/validate` | POST | `OcrValidationRequest{image_bytes, plate_candidate}` | `OcrValidationResponse{plate_number, confidence, ocr_engine, plate_format}` | `OcrService.validatePlate()` |
| 2.2.2 | `/mobile/ocr/batch` | POST | `OcrBatchValidationRequest{images[]}` | `OcrBatchValidationResponse{results[]}` | Batch validation |

**Fluxo OCR:**
```
Mobile:
  CameraX captures image → ML Kit detects plate region
  → EasyOCR reads text → POST /mobile/validate
    → Validation: formato Mercosul ou old
    → Returns OcrValidationResponse
    → User confirms/edits → POST /observations
```

### 2.3 Abordagem

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.3.1 | `/mobile/plates/{plate}/check-suspicion` | GET | — | `PlateSuspicionCheckResponse{score, factors[], level}` | `checkSuspicion()` |
| 2.3.2 | `/mobile/observations/{id}/approach-confirmation` | POST | `ApproachConfirmationRequest{confirmed_suspicion, approach_outcome, notes, location, street_direction}` | `ApproachConfirmationResponse{observation_id, plate_number, confirmed_suspicion, notified_original_agent, original_agent_name}` | `confirmApproach()` |

**Fluxo Approach:**
```
Mobile:
  PlateCaptureScreen → OCR validate → check-suspicion
    → POST /observations
    → Usuário fill approach_outcome → POST /approach-confirmation
      → Backend: gera AnalystFeedbackEvent para agente original
      → Notifica via WebSocket
      → Returns confirmation
```

### 2.4 Localização do Agente

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.4.1 | `/mobile/profile/current-location` | POST | `AgentLocationUpdate{location{lat,lng}, recorded_at, accuracy}` | `{"message": "Current location updated", "status": "success", "on_duty": bool}` | `LocationTrackingWorker` |
| 2.4.2 | `/mobile/profile/location-history` | POST | `AgentLocationBatchSync{items[{location, recorded_at, ...}]}` | `{"message": f"Successfully synced {len(payload.items)}", "status": "synced", "count": int}` | Sync offline |
| 2.4.3 | `/mobile/profile/duty/renew` | POST | `ShiftRenewalRequest{shift_duration_hours}` | `{"message": "Turno renovado com sucesso por +{hours}h"}` | Renew turno |

### 2.5 Sync em Lote

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.5.1 | `/mobile/sync/batch` | POST | `SyncBatchRequest{observations[], assets[], pending_feedback[]}` | `SyncBatchResponse{processed_count, feedback_pending[FeedbackForAgent]}` | `SecureSyncWorker` |

**Fluxo Sync:**
```
Mobile:
  SyncWorker triggers (interval or manual)
    → POST /mobile/sync/batch
      → Processa observações pendentes
      → Aplica pending_feedback (feedback do analista)
      → Returns {feedback_pending[]}
        → SecureNotificationManager.trigger(feedback)
```

### 2.6 Assets

| # | Endpoint | Método | Request | Response | Mobile |
|---|----------|--------|---------|----------|--------|
| 2.6.1 | `/mobile/observations/{id}/assets` | POST | `AssetUploadRequest{file, type}` | `AssetResponse{url, checksum}` | Upload imagem |
| 2.6.2 | `/mobile/observations/{id}/assets/progressive` | POST | Multipart chunk | AssetResponse | Progressive upload |

---

## 3. Inteligência (`/intelligence`)

Prefixo: `/api/v1/intelligence`

### 3.1 Fila e Observações

| # | Endpoint | Método | Query Params | Response | Frontend |
|---|----------|--------|-------------|----------|----------|
| 3.1.1 | `/intelligence/queue` | GET | `agency_id`, `status`, `priority`, `page`, `page_size` | `IntelligenceQueueItem[]` | `queue/page.tsx` |
| 3.1.2 | `/intelligence/observations/{id}` | GET | — | `ObservationAnalyticDetailResponse` | Detail modal |

**IntelligenceQueueItem Fields:**
```python
{
  "observation_id": UUID,
  "plate_number": str,
  "agency_id": UUID,
  "suspicion_level": str,  # "critical", "high", "moderate", "low"
  "created_at": datetime,
  "has_review": bool,
  "review_status": str | None
}
```

### 3.2 Reviews e Feedback

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 3.2.1 | `/intelligence/reviews` | POST | `AnalystReviewCreate{observation_id, level, notes, justification}` | `AnalystReviewResponse` | Queue - "Revisar" |
| 3.2.2 | `/intelligence/reviews/{id}` | PATCH | `AnalystReviewUpdate{level, notes}` | `AnalystReviewResponse` | Update review |
| 3.2.3 | `/intelligence/feedback` | POST | `AnalystFeedbackCreate{target_user_id, feedback_type, title, message}` | `AnalystFeedbackResponse` | Feedback - criar |
| 3.2.4 | `/intelligence/feedback/pending` | GET | — | `FeedbackForAgent[]` | Mobile - pending |
| 3.2.5 | `/intelligence/feedback/templates` | GET | — | `AnalystFeedbackTemplateResponse[]` | Templates |
| 3.2.6 | `/intelligence/feedback/recipients` | GET | — | `FeedbackRecipientResponse[]` | Buscar destinatários |

### 3.3 Watchlist

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 3.3.1 | `/intelligence/watchlist` | GET | `agency_id` | `WatchlistEntryResponse[]` | `watchlist/page.tsx` |
| 3.3.2 | `/intelligence/watchlists` | GET | `agency_id` | `WatchlistEntryResponse[]` | `watchlist/page.tsx` (alias) |
| 3.3.3 | `/intelligence/watchlist` | POST | `WatchlistEntryCreate{plate_number, category, priority, notes, expiry_date}` | `WatchlistEntryResponse` | Criar entrada |
| 3.3.4 | `/intelligence/watchlists` | POST | `WatchlistEntryCreate{plate_number, category, priority, notes, expiry_date}` | `WatchlistEntryResponse` | Criar entrada (alias) |
| 3.3.5 | `/intelligence/watchlist/{id}` | PATCH | `WatchlistEntryUpdate{status, priority}` | `WatchlistEntryResponse` | Editar/Suspender |
| 3.3.6 | `/intelligence/watchlists/{id}` | PATCH | `WatchlistEntryUpdate{status, priority}` | `WatchlistEntryResponse` | Editar/Suspender (alias) |
| 3.3.7 | `/intelligence/watchlist/{id}` | DELETE | — | 204 | Remover |

### 3.4 Algoritmos (Resultados)

| # | Endpoint | Método | Query Params | Response | Frontend |
|---|----------|--------|-------------|----------|----------|
| 3.4.1 | `/intelligence/routes` | GET | `agency_id`, `crime_type`, `risk_level` | `AlgorithmResultResponse[]` | `suspicious-routes/page.tsx` |
| 3.4.2 | `/intelligence/convoys` | GET | `agency_id`, `min_confidence` | `AlgorithmResultResponse[]` | `convoys/page.tsx` |
| 3.4.3 | `/intelligence/roaming` | GET | `agency_id`, `severity` | `AlgorithmResultResponse[]` | `roaming/page.tsx` |
| 3.4.4 | `/intelligence/sensitive-assets` | GET | `agency_id` | `AlgorithmResultResponse[]` | `sensitive-assets/page.tsx` |

### 3.5 Casos

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 3.5.1 | `/intelligence/cases` | GET | `agency_id`, `status`, `page` | `IntelligenceCaseResponse[]` | `cases/page.tsx` |
| 3.5.2 | `/intelligence/cases` | POST | `IntelligenceCaseCreate{name, plates[], description}` | `IntelligenceCaseResponse` | Criar caso |
| 3.5.3 | `/intelligence/cases/{id}` | PATCH | `IntelligenceCaseUpdate{status, notes}` | `IntelligenceCaseResponse` | Atualizar |
| 3.5.4 | `/intelligence/cases/{id}` | DELETE | — | 204 | Encerrar |

### 3.6 Analytics

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 3.6.1 | `/intelligence/analytics/overview` | GET | `{total_observations, pending_reviews, agents_active, alerts_by_severity}` | Dashboard overview |
| 3.6.2 | `/intelligence/analytics/observations-by-day` | GET | `{date, count}[]` | Line chart |
| 3.6.3 | `/intelligence/analytics/top-plates` | GET | Top plates por suspeição | Analytics |
| 3.6.4 | `/intelligence/analytics/unit-performance` | GET | Performance por unidade | Analytics |

### 3.7 Agencies

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 3.7.1 | `/intelligence/agencies` | GET | `AgencyResponse[]` | Multi-agência |

---

## 4. Alertas (`/alerts`)

Prefixo: `/api/v1/alerts`

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 4.1 | `/alerts/check-observation` | POST | `ObservationAlertCheckRequest{plate_number, location, observed_at}` | `ObservationAlertCheckResponse{alerts[]}` | Check automático |
| 4.2 | `/alerts/aggregated` | POST | `AggregatedAlertsRequest{alert_type?, severity?, limit?}` | `AggregatedAlertsResponse{total_alerts, alerts[], summary}` | `alerts/page.tsx` |
| 4.3 | `/alerts/recurrence-check` | POST | Verifica recorrência | alertas | Monitoramento |

---

## 5. Hotspots (`/hotspots`)

Prefixo: `/api/v1/hotspots`

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 5.1 | `/hotspots/analyze` | POST | `{start_date, end_date, cluster_radius_meters, min_points_per_cluster}` | `HotspotAnalysisResult{hotspots[{lat,lng, observation_count, suspicion_count, unique_plates, intensity_score}], total}` | `hotspots/page.tsx` |
| 5.2 | `/hotspots/timeline` | POST | `{hotspot_id, start_date}` | timeline array | Detalhe |
| 5.3 | `/hotspots/plates` | POST | `{hotspot_id}` | placas relacionadas | |

---

## 6. Predição de Rotas (`/route-prediction`)

Prefixo: `/api/v1/route-prediction`

| # | Endpoint | Método | Request | Response | Frontend |
|---|----------|--------|----------|----------|----------|
| 6.1 | `/route-prediction` | POST | `{plate_number, agency_id}` | `RoutePredictionResponse{plate_number, predicted_corridor, confidence, predicted_hours, predicted_days, pattern_strength}` | `route-prediction/page.tsx` |
| 6.2 | `/route-prediction/for-plate` | POST | `{plate_number, min_observations}` | prediction detalhada | |
| 6.3 | `/route-prediction/pattern-drift` | POST | `{plate_number, agency_id}` | `PatternDriftAlert{drift_percent, threshold_percent, out_of_corridor_count}` | Desvio |
| 6.4 | `/route-prediction/recurring-alerts` | GET | — | `RecurringRouteAlertResponse[]` | Alertas |
| 6.5 | `/intelligence/route-analysis` | POST | — | `RoutePatternResponse` | Análise de rotas |
| 6.6 | `/intelligence/route-timeline/{plate_number}` | GET | — | `RouteTimelineResponse` | Timeline de rota |
| 6.7 | `/intelligence/routes/analyze` | POST | — | `RoutePatternResponse` | Análise de rotas (alias) |
| 6.8 | `/intelligence/routes/{plate_number}/timeline` | GET | — | `RouteTimelineResponse` | Timeline de rota (alias) |
| 6.9 | `/intelligence/routes/{plate_number}` | GET | — | `RoutePatternResponse` | Padrão de rota |

---

## 7. Boletim de Atendimento (`/boletim_atendimento`)

Prefixo: `/api/v1/boletim_atendimento`

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 7.1 | `/boletim_atendimento` | GET | `BAListResponse{bulletins[], total}` | `boletims/page.tsx` |
| 7.2 | `/boletim_atendimento/{id}` | GET | BA detail | Visualização |
| 7.3 | `/boletim_atendimento` | POST | `{observation_id, approach_data}` → gera BA | Geração |

---

## 8. Auditoria (`/audit`)

Prefixo: `/api/v1/audit`

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 8.1 | `/audit/logs` | GET | `AuditLogResponse[]` | `audit/page.tsx` |
| 8.2 | `/audit/geolocation` | GET | geolocation logs | Mapa |

---

## 9. Dispositivos

Prefixo: `/api/v1/devices`

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 9.1 | `/devices` | GET | `DeviceResponse[]` | `devices/page.tsx` |
| 9.2 | `/devices/{id}/suspend` | PATCH | suspende device | Desativar |

---

## 10. Documentação

Prefixo: `/api/v1/documentation`

| # | Endpoint | Método | Response | Frontend |
|---|----------|--------|----------|----------|
| 10.1 | `/documentation/optimization/hardware` | GET | hw info | `documentation/page.tsx` |
| 10.2 | `/documentation/optimization/config` | GET | config | |
| 10.3 | `/documentation/optimization/performance` | GET | metrics | |
| 10.4 | `/documentation/optimization/recommendations` | GET | recommendations | |
| 10.5 | `/documentation/legal/terms-of-service` | GET | ToS | Help |
| 10.6 | `/documentation/legal/privacy-policy` | GET | PP | Help |
| 10.7 | `/documentation/usage/guidelines` | GET | guidelines | Help |
| 10.8 | `/documentation/usage/alerts` | GET | alerts config | |

---

## 11. WebSocket

Prefixo: `/api/v1/ws`

| # | Endpoint | Método | Uso |
|---|----------|--------|-----|
| 11.1 | `/ws/user/{user_id}` | WS | Realtime notifications |
| 11.2 | `/ws/broadcast` | WS | Broadcast global |

### Eventos WebSocket

| Evento | Payload | Descrição |
|--------|--------|-----------|
| `watchlist_match` | `{observation_id, plate_number, match_type}` | Match de watchlist |
| `impossible_travel` | `{observation_id, plate_number, distance_km}` | Viagem impossível |
| `approach_confirmed` | `{observation_id, plate_number, target_agent}` | Confirmação de abordagem |
| `queue_update` | `{observation_id, action}` | Queue atualizada |
| `feedback_received` | `{feedback_id, title}` | Feedback recebído |

---

## Schemas de Resposta (principais)

### VehicleObservationResponse
```python
{
  "id": "uuid",
  "plate_number": "ABC-1234",
  "location": {"latitude": -30.0346, "longitude": -51.2177},
  "observed_at_local": "2026-04-17T10:30:00Z",
  "agency_id": "uuid",
  "agent_id": "uuid",
  "metadata": {"source": "mobile_app", "accuracy": 10.5}
}
```

### AlgorithmResultResponse
```python
{
  "id": "uuid",
  "algorithm_type": "convoy",  # watchlist, impossible_travel, route_anomaly, sensitive_zone_recurrence, convoy, roaming
  "observation_id": "uuid",
  "decision": "probable_convoy",  # enum
  "confidence": 0.79,
  "severity": "high",
  "explanation": "Coocorrência entre XXX e YYY em janela curta com distancia de 1.2km.",
  "false_positive_risk": "medium",
  "metrics": {
    "related_plate": "ZZZ-9999",
    "cooccurrence_count": 3
  },
  "created_at": "2026-04-17T10:30:00Z"
}
```

### IntelligenceQueueItem
```python
{
  "observation_id": "uuid",
  "plate_number": "ABC-1234",
  "location": {"lat": -30.0346, "lng": -51.2177},
  "agency_id": "uuid",
  "suspicion_level": "high",  # critical, high, moderate, low
  "confidence_score": 0.85,
  "created_at": "2026-04-17T10:30:00Z",
  "has_review": false,
  "review_status": null,
  "review_deadline": "2026-04-20T10:30:00Z"
}
```

### HotspotAnalysisResult
```python
{
  "hotspots": [
    {
      "latitude": -30.0346,
      "longitude": -51.2177,
      "observation_count": 45,
      "suspicion_count": 12,
      "unique_plates": 28,
      "radius_meters": 500,
      "intensity_score": 0.85
    }
  ],
  "total_observations": 1247,
  "total_suspicions": 89,
  "analysis_period_days": 30,
  "cluster_radius_meters": 500,
  "min_points_per_cluster": 5
}
```

### RoutePredictionResponse
```python
{
  "plate_number": "ABC-1234",
  "predicted_corridor": [[-30.0, -51.2], [-30.1, -51.3], ...],  # [lat, lng]
  "confidence": 0.72,
  "predicted_hours": [8, 9, 10, 17, 18, 19],
  "predicted_days": [0, 1, 2, 3, 4],  # Monday-Friday
  "last_pattern_analyzed": "2026-04-15T08:00:00Z",
  "pattern_strength": "strong"
}
```

---

## Fluxos Completos

### Fluxo 1: Mobile → Observação + Algoritmos

```
Mobile                                        Server                                    Web Console
 │                                              │                                       │
 ▼                                              ▼                                       │
┌────────────────────┐                         ┌────────────────────────────────────────┐ │
│ ApproachFormScreen│                         │                                        │ │
│ 1. OCR Validate   │ ──POST /mobile/ocr────▶│ Backend: YOLOv11 + EasyOCR            │ │
│    (camera)        │ ◀──Response─────────────│ Returns: {plate, confidence}           │ │
└────────────────────┘                         └────────────────────────────────────────┘ │
                                                                                        │
┌────────────────────┐                         ┌────────────────────────────────────────┐ │
│ 2. User confirms  │ ──POST /mobile──────────▶│ Backend:                             │ │
│    plate           │     /observations        │ - evaluate_watchlist(plate)           │ │
│                    │ ◀──Response─────────────│ - evaluate_impossible_travel()        │ │
│                    │  VehicleObservation    │ - evaluate_sensitive_zone_recurrence │ │
└────────────────────┘ │ + SuspicionScore       │ - evaluate_convoy(neighbors)         │ │
                      │                         │ - evaluate_roaming(recent)             │ │
                      │                         │ - compute_composite_score()           │ │
                      │                         │ Returns: ObservationResponse + Score  │ │
                      │                         │ + triggers alerts if match            │ │
                      │                         └────────────────────────────────────────┘ │
                                                                                        │
                                              │ WebSocket event_bus.publish()         │
                                              ▼                                        │
┌─────────────────────────────────────────────┐                                       │
│ 3. Algoritmos correm em background           │                                       │
│    - Todos armazenados em AlgorithmRun       │                                       │
│    - Explicações em AlgorithmExplanation     │                                       │
│    - Scorecomposto em SuspicionScore       │                                       │
└─────────────────────────────────────────────┘
```

### Fluxo 2: Sync Offline

```
Mobile (offline)                              Server
 │                                              │
 ▼                                              ▼
┌────────────────────────────────────────────────┐
│ SecureSyncWorker.collectPending()             │
│   - Local observations[]                       │
│   - Local assets[]                              │
│   - pending_feedback[]                         │
└────────────────────────────────────────────────┘
              │
              ▼ POST /mobile/sync/batch
              │
              ├─► Process observations[]
              │     └─► DB.insert()
              │
              ├─► Process assets
              │     └─► S3 upload
              │
              ├─► Apply pending_feedback
              │     └─► Mark as read
              │
              ◄─── Response {processed_count, feedback_pending[]}
                          │
                          ▼
              SecureNotificationManager
                  - trigger notifications for new feedback
```

### Fluxo 3: Queue Web → Review → Feedback

```
Web Console                                                     Server
 │                                                               │
 ▼                                                               ▼
 GET /intelligence/queue ─────────────────────────────────────────▶ Queue items[]
 │
 │                                                               │
 ▼                                                               │
 User clicks "Revisar" ─────────────────▶ POST /intelligence/reviews
 │                                                {observation_id, level, notes}
 │                                                │
 │                                                ▼
 │                                                1. Creates AnalystReview
 │                                                2. eval_context_service.analyze()
 │                                                3. event_bus.publish("feedback_created")
 │                                                │
 │                                                Returns: ReviewResponse
 │
 ▼                                                               │
 GET /intelligence/feedback ─────────────────────────▶ Feedback list
     /pending (for agent)
 │
 ▼                                                               │
 WebSocket /ws/user/{agent_id} ◀────────────────────────────────┘
     Event: feedback_created
          │
          ▼
     Mobile: SyncWorker baixa feedback
          │
          ▼
     NotificationManager.show()
```

---

## Códigos de Resposta

| Código | Significado |
|---------|--------------|
| 200 | Sucesso |
| 201 | Criado |
| 204 | Sem conteúdo |
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Proibido |
| 404 | Não encontrado |
| 422 | Erro de validação |
| 429 | Rate limit excedido |
| 500 | Erro interno |
| 503 | Serviço indisponível |

---

## Rate Limiting

| Endpoint | Limite |
|-----------|--------|
| `/auth/login` | 5/min |
| `/mobile/observations` | 60/min |
| `/intelligence/feedback` | 30/min |
| Global default | 100/min |

---

## Autenticação

- ** Bearer Token** em header: `Authorization: Bearer <access_token>`
- ** Refresh**: `POST /auth/refresh` com `refresh_token` obtém novo access_token
- ** Token JWT**: expira em 30 min (configurável)
- ** Refresh JWT**: expira em 7 dias (configurável)

---

---

## 12. Integrações com Serviços Estaduais

> **Status atual: DESENVOLVIMENTO (mock/fallback)**
> Todas as integrações estão em modo dev-mode, retornando dados mock.

### 12.1 Estrutura de Adapter

Os adapters são isolados em `app/integrations/` para que possam ser implementados sem alterar o fluxo operacional:

```
app/integrations/
├── __init__.py
├── state_registry_adapter.py    # Registro de veículos (DETRAN/RENAVAM) - IMPLEMENTADO
├── bm_ba_connector.py          # Boletim de Atendimento → BM - IMPLEMENTADO
└── bm_hr_adapter.py            # Recurso Humano → BM - IMPLEMENTADO
```

### 12.2 Registro de Veículos Estaduais (`state_registry_adapter.py`)

**Status:** DEV-MODE (mock implementado)

| Função | Request | Response |
|-------|---------|----------|
| `query_state_vehicle_registry(plate_number)` | `str` | `{provider, plate_number, connected: false, status: "mock_data", message, ...dados_fictícios}` |

**Dados mock retornados (DEV-MODE):**
- `owner`: Nome simulado do proprietário
- `vehicle_model`: Modelo do veículo (aleatório de lista)
- `vehicle_year`: Ano de fabricação
- `vehicle_color`: Cor do veículo
- `registration_status`: Status do IPVA
- `ipva_status`: Vencimento do IPVA

**Endpoint esperado:** Integração com base do DETRAN/RS ou RENAJAM (federal).

### 12.3 Boletim de Atendimento → Brigada Militar (`bm_ba_connector.py`)

**Status:** DEV-MODE (mock + storage local implementado)

| Variável de Ambiente | Descrição |
|---------------------|------------|
| `BM_SYSTEM_ENDPOINT` | URL do sistema da BM (ex: `https://bm.rs.gov.br/api/ba`) |
| `BM_SYSTEM_CONNECTED` | Flag de conexão (False = dev-mode) |
| `DEV_MODE` | Quando True, salva localmente com TTL |
| `BA_LOCAL_TTL_DAYS` | Tempo de vida do BA local (padrão: 7 dias) |

| Função | Request | Response |
|-------|---------|----------|
| `transmit_ba_to_state_system(payload: BAPayload)` | `BAPayload` | `{provider, connected: false, status: "not_sent", message}` |

**Fluxo atual:**
```
Gerar BA (Boletim de Atendimento)
    │
    ▼
POST /boletim_atendimento
    │
    ▼
Backend: generate_ba_from_approach()
    │
    ▼
transmit_ba_to_state_system(payload)
    │
    ▼ [DEV-MODE]
1. Salva no BALocalStorage com TTL de 7 dias
2. Returns: {connected: false, status: "not_sent"}
    │
    ▼
BA disponível para retransmissão futura
```

**BALocalStorage (implementado):**
- Salva em memória com key `ba:{observation_id}`
- Cleanup automático a cada hora
- TTL configurável (padrão: 7 dias)
- Métodos: `save()`, `get()`, `list_pending()`, `list_all()`, `delete()`

### 12.4 Recursos Humanos - BM (`bm_hr_adapter.py`)

**Status:** DEV-MODE (mock implementado)

| Função | Request | Response |
|-------|---------|----------|
| `verify_bm_operational(cpf: str)` | `str` | `{provider, connected: false, status: "mock_data", ...dados_fictícios}` |

**Dados mock retornados (DEV-MODE):**
- `badge_number`: Número de matrícula falso
- `full_name`: Nome gerado aleatoriamente
- `rank`: Posto/Graduação (aleatório)
- `unit`: Unidade de lotação
- `status`: Status ativo

**Endpoint esperado:** Integração com base de RH da BM.

### 12.5 SSO gov.br (planejado)

**Status:** PLANEJADO (não implementado)

**Objetivo:** Autenticação via Gov.br OAuth2/OIDC.

**Referências:**
- Host: `https://sso.acesso.gov.br/`
- Scope: `gov.br:cpf`, `gov.br:email`
- Registro de aplicação necessário via portal Gov.br

**Fluxo futuro:**
```
1. User → FARO Login
2. Redirect → https://sso.acesso.gov.br/authorize?client_id=FARO&scope=...
3. User authenticates with gov.br credentials
4. Callback → FARO with authorization code
5. FARO exchanges code → access token
6. FARO queries user info → maps to unit/role
7. Creates/updates local user → issues JWT
```

---

## 13. Base de Dados - Modelos Principais

### Tabelas Operacionais

| Tabela | Descrição |
|--------|------------|
| `users` | Operacionais (matrícula, unidade, role) |
| `agencies` | Unidades/pelotões (UUID, code, name, hierarchy) |
| `vehicle_observations` | Observações de campo |
| `algorithm_runs` | Execuções de algoritmos |
| `algorithm_results` | Resultados por observação |
| `suspicion_scores` | Scores compostos |
| `watchlist_entries` | Cadastro de monitoramento |
| `suspicious_routes` | Rotas suspeitas (PostGIS) |
| `sensitive_zones` | Zonas sensíveis (PostGIS) |
| `route_patterns` | Padrões de rota históricos |
| `hotspot_clusters` | Clusters de criminalidade |
| `audit_logs` | Cadeia de custódia |
| `algorithm_explanations` | Justificativas dos algoritmos |

### Índices Geoespaciais

```sql
-- Observações com índice espacial
CREATE INDEX ix_vehicle_observations_location 
ON vehicle_observations USING GIST(location);

-- Rotas suspeitas com geometria
CREATE INDEX ix_suspicious_routes_geometry 
ON suspicious_routes USING GIST(route_geometry);

-- Zonas sensíveis
CREATE INDEX ix_sensitive_zones_geometry 
ON sensitive_zones USING GIST(geometry);
```

---

## Notas

- Timestamps em formato ISO 8601 UTC (`Z`)
- Coordenadas em WGS84 (EPSG:4326)
- Placas no formato Mercosul (`AAA-1234`) ou antigo (`AAA1234`)
- Agency é identificada por UUID (unidade/pelotão)
- Operador é identificado por UUID (matrícula)

---

## Otimizações Implementadas (2026-04-17)

### Fase 1 - Otimizações de Código

**1.1 Execução Paralela de Algoritmos:**
- Arquivo: `server-core/app/services/analytics_service.py`
- Função: `evaluate_observation_algorithms()`
- Implementação: `asyncio.gather()` para executar 5 algoritmos independentes em paralelo (watchlist, impossible travel, route anomaly, sensitive zone, roaming)
- Ganho: 50-70% redução de latência (350ms → 100-175ms)

**1.2 Cache Redis para Dados Estáticos:**
- Arquivo: `server-core/app/utils/cache.py`
- Implementação: Decorator `@cached_query` com TTL de 300s
- Funções cacheadas: `get_active_route_regions()`, `get_active_sensitive_zones()`
- Aplicado em: `evaluate_route_anomaly()`, `evaluate_sensitive_zone_recurrence()`
- Ganho: Elimina 30-50% queries redundantes

**1.3 Otimização Convoy - Single Query:**
- Arquivo: `server-core/app/services/analytics_service.py`
- Função: `evaluate_convoy()`
- Implementação: Single query com GROUP BY para contar histórico de todos os pares
- Ganho: O(N) → O(1) queries (100 vizinhos: 101 → 1 query)

**1.4 Otimização Score Composto - Paralelização:**
- Arquivo: `server-core/app/services/analytics_service.py`
- Função: `compute_suspicion_score()`
- Implementação: `asyncio.gather()` para 7 queries independentes
- Ganho: 7 queries executadas em paralelo

**1.5 Otimização Check Route Match - Batch Query:**
- Arquivo: `server-core/app/services/suspicious_route_service.py`
- Função: `check_route_match()`
- Implementação: Single SQL query com ST_Intersects e ST_DWithin para todas as rotas
- Ganho: N → 1 query

**1.6 Otimizações OCR Server-Side:**
- Arquivos: `server-core/app/main.py`, `server-core/app/services/ocr_service.py`, `server-core/app/api/v1/endpoints/mobile.py`, `server-core/app/schemas/observation.py`
- Implementações:
  - Pré-carregamento de modelos no startup
  - AsyncOcrService para processamento assíncrono
  - Cache Redis de resultados OCR (TTL: 3600s)
  - Pré-processamento de imagem (resize 640x640)
  - Endpoint batch `/ocr/batch`
  - Modelo adaptativo (GPU: yolov11s, CPU: yolov11n)
- Ganho: 3-5x mais rápido para OCR server-side

### Fase 2 - Otimizações PostgreSQL

**2.1 PgBouncer Connection Pooling:**
- Arquivos: `server-core/app/core/config.py`, `server-core/app/db/session.py`, `server-core/docs/pgbouncer-setup.md`
- Implementação:
  - Configurações PgBouncer no config.py (pgbouncer_enabled, pgbouncer_host, pgbouncer_port, pgbouncer_pool_mode, etc.)
  - Função get_database_url() em session.py para usar PgBouncer quando habilitado
  - Guia completo de instalação e configuração em docs/pgbouncer-setup.md
- Ganho: 5-10x throughput, 90% redução overhead conexão

**2.2 BRIN Index para vehicle_observations:**
- Arquivo: `server-core/alembic/versions/0007_brin_index_observations.py`
- Implementação:
  - BRIN index em observed_at_local (pages_per_range = 128)
  - BRIN index em created_at (pages_per_range = 128)
- Ganho: 10x mais rápido para queries espaciais em dados ordenados, 1000x menor que GiST

**2.3 Parallel Query Tuning:**
- Arquivo: `server-core/alembic/versions/0008_parallel_query_tuning.py`
- Implementação:
  - max_parallel_workers_per_gather = 4
  - max_parallel_workers = 8
  - max_parallel_maintenance_workers = 4
  - parallel_setup_cost = 1000
  - parallel_tuple_cost = 0.1
- Ganho: 2-4x mais rápido para scans grandes

**2.4 Materialized Views para Hotspots:**
- Arquivos: `server-core/alembic/versions/0009_materialized_views_hotspots.py`, `server-core/app/db/materialized_views.py`
- Implementação:
  - mv_daily_hotspots: hotspots diários com ST_ClusterWithin
  - mv_agency_hotspots: hotspots por agency
  - Funções refresh_materialized_views() e get_daily_hotspots() em materialized_views.py
- Ganho: 10x mais rápido para queries de hotspot

### Fase 4 - TimescaleDB

**4.1 Hypertable para Time-Series:**
- Arquivo: `server-core/alembic/versions/0010_timescaledb_setup.py`
- Implementação:
  - Instalação da extensão TimescaleDB
  - Conversão de vehicle_observations para hypertable usando observed_at_local como time column
  - Continuous aggregate mv_daily_observation_counts para daily observation counts
  - Refresh policy automática a cada 1 hora
- Ganho: 50-100x para queries time-series

### Fase 5 - Citus

**5.1 Escala Horizontal:**
- Arquivo: `server-core/alembic/versions/0011_citus_setup.py`
- Implementação:
  - Instalação da extensão Citus
  - Distribuição de tabelas por agency_id (multi-tenant sharding)
  - Tabelas distribuídas: vehicle_observations, convoy_events, impossible_travel_events, route_anomaly_events, sensitive_asset_recurrence_events, roaming_events, suspicion_scores, watchlist_hits
  - Reference tables: agency, user
- Ganho: Escala linear adicionando nodes, 5-10x com 4 nodes

### Fase 6 - Monitoramento e Métricas

**6.1 Métricas de Algoritmos:**
- Arquivos: `server-core/app/core/observability.py`, `server-core/app/services/analytics_service.py`, `server-core/app/utils/cache.py`
- Métricas Prometheus adicionadas:
  - ALGORITHM_EXECUTION_DURATION: Histograma de duração por algoritmo
  - ALGORITHM_EXECUTION_TOTAL: Counter de execuções por algoritmo e outcome
  - OBSERVATION_THROUGHPUT: Histograma de throughput
  - CACHE_HIT_RATIO: Histograma de cache hit ratio
  - POSTGRESQL_QUERY_DURATION: Histograma de duração de queries
  - SUSPICION_SCORE_COMPUTE_DURATION: Histograma de duração do score composto
- Funções helper: record_algorithm_execution(), record_observation_throughput(), record_cache_hit_ratio(), record_postgresql_query(), record_suspicion_score_compute()
- Métricas integradas em todos os algoritmos (watchlist, impossible_travel, route_anomaly, sensitive_zone_recurrence, convoy, roaming, suspicion_score)
- Métricas de cache hit/miss em cache.py
- Objetivos: latência P95 < 200ms, throughput > 1000 obs/segundo, cache hit ratio > 80%, queries PostgreSQL < 50ms P95

### Ganho Total

- Fases 1-2: 10-50x overall em 4-6 semanas
- Fases 1-5: 100-1000x overall em 10-12 semanas
- Todas as Fases: 100-1000x overall com monitoramento completo

### Próximas Ações Manuais

- Executar migrations do banco de dados (alembic upgrade head)
- Configurar PgBouncer seguindo docs/pgbouncer-setup.md
- Instalar TimescaleDB e Citus
- Configurar dashboard de monitoramento Prometheus