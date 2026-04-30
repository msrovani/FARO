# F.A.R.O. Analytics Dashboard

Dashboard analítico em tempo real para monitoramento do sistema F.A.R.O.

## ⚠️ Nota sobre Portas

- **Porta 9000**: Reservada para MinIO S3 (storage)
- **Porta 9001**: Reservada para MinIO Console (UI de gerenciamento)
- **Porta 9002**: Usada pelo Analytics Dashboard (para evitar conflitos com MinIO)

## 🚀 Como Executar

### Modo Standalone (Recomendado)
```bash
cd analytics-dashboard
pip install -r requirements.txt
python app.py
```

Acesse: **http://localhost:9002/dashboard**

### Integrado ao Server Core
```python
# Em server-core/app/main.py
# O dashboard está na raiz do projeto: analytics-dashboard/
# Adicione ao PYTHONPATH ou use import relativo
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'analytics-dashboard'))
from app import app as dashboard_app

# O servidor principal já roda na porta 8000
# O dashboard pode rodar em outra porta ou como rota
```

## 📊 Abas do Dashboard (8 tabs)

| # | Aba | Descrição |
|---|-----|-----------|
| 1 | **Overview** | Métricas HTTP, DB, Cache, Alerts, PgBouncer, Redis |
| 2 | **Alerts** | Lista de alertas actifs em tempo real |
| 3 | **Database** | Pool de conexões, overflow, status de saúde |
| 4 | **Circuit Breakers** | Status de cada circuit breaker (mobile_sync, ocr_processing, etc) |
| 5 | **Usabilidade** | Conectividade: usuários online/offline, WiFi/4G/3G, qualidade de rede |
| 6 | **Analytics** | OCR (mobile/server), suspeitas por severidade, alertas por algoritmo |
| 7 | **Auditoria** | Logs de auditoria com filtros (tipo, data, TTL) |
| 8 | **Histórico Alertas** | Histórico de alertas com paginação |

## 🎛️ Slider de Refresh

O painel superior possui um slider para controlar o intervalo de coleta de dados:

| Índice | Intervalo | Label |
|-------|-----------|-------|
| 0 | 2000ms | 2s (online) |
| 1 | 5000ms | 5s (default) |
| 2 | 8000ms | 8s |
| 3 | 15000ms | 15s |
| 4 | 30000ms | 30s |
| 5 | 60000ms | 1min |
| 6 | 300000ms | 5min |
| 7 | 900000ms | 15min |
| 8 | 1800000ms | 30min |

**Funcionamento:** O slider altera dinamicamente o intervalo de polling. Cada alteração reinicia o ciclo de coleta com o novo intervalo.

## 📱 Responsividade

- Interface adaptável para desktop e mobile
- Grid responsivo: `grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))`
- Nav tabs roláveis em dispositivos pequeños
- Dark mode nativo

## 🔌 Conexão ao DB

O dashboard busca dados através de múltiplas fontes:

### 1. Server-core (preferido)
Busca métricas do endpoint `/api/v1/metrics` do server-core (porta 8000):
- Métricas Prometheus (HTTP requests, DB pool, cache)
- Queries reais ao PostgreSQL

### 2. Fallback (modo standalone)
Se o server-core não estiver disponível, usa métricas próprias com valores default.

### Métricas Reais do DB (implementadas)

O endpoint `/api/v1/metrics` retorna dados reais:

| Métrica | Fonte | Descrição |
|--------|-------|-----------|
| `observations_today` | vehicleobservation | Observações de hoje |
| `alerts_today` | alert | Alertas de hoje |
| `suspicion_critical` | suspicionreport | Suspeitas críticas |
| `suspicion_high` | suspicionreport | Suspeitas altas |
| `suspicion_medium` | suspicionreport | Suspeitas médias |
| `suspicion_low` | suspicionreport | Suspeitas baixas |
| `suspicion_confirmed` | intelligencereview | Suspeitas confirmadas |
| `suspicion_rejected` | intelligencereview | Suspeitas rejeitadas |
| `suspicion_accuracy` | calculado | Taxa de acerto |
| `algo_watchlist` | watchlistentry | Entradas ativas na watchlist |

## 🌐 Endpoints

| Endpoint | Descrição |
|----------|-----------|
| `/dashboard` | Interface HTML do dashboard |
| `/api/v1/health` | Status completo JSON (metrics + alerts + recommendations) |
| `/api/v1/metrics` | Métricas atuais |
| `/api/v1/alerts` | Lista de alertas |
| `/api/v1/audit/logs` | Logs de auditoria |
| `/api/v1/monitoring/history` | Histórico de alertas |
| `/api/v1/monitoring/history/stats` | Estatísticas de alertas |
| `/ws` | WebSocket para updates em tempo real |

### Exemplos de API

```bash
# Health check completo
curl http://localhost:9002/api/v1/health

# Métricas
curl http://localhost:9002/api/v1/metrics

# Alertas
curl http://localhost:9002/api/v1/alerts

# Logs de auditoria
curl "http://localhost:9002/api/v1/audit/logs?ttl_days=30"

# Histórico de alertas
curl "http://localhost:9002/api/v1/monitoring/history?limit=100"
```

## 🔌 WebSocket

O dashboard conecta via WebSocket para updates em tempo real:

```javascript
const ws = new WebSocket('ws://localhost:9002/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data.metrics);
};
```

**Fallback:** Se WebSocket não conectar, usa polling HTTP a cada intervalo configurado.

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|---------|-----------|
| `HOST` | `0.0.0.0` | Host para bind |
| `PORT` | `9002` | Porta do dashboard |
| `DASHBOARD_REFRESH_MS` | `5000` | Intervalo de refresh |

### Timeout de Servidor

O timeout para buscar métricas do server-core é 5 segundos.

## 🔧 Troubleshooting

### Dashboard não carrega
- Verificar se a porta 9002 está disponível
- Verificar logs do terminal

### Métricas não aparecem
- Verificar se o server-core está rodando na porta 8000
- Verificar conexão com banco de dados
- Verificar campo `query_error` na resposta

### WebSocket não conecta
- Verificar firewall
- O fallback usa polling automático

### Dados mostram zeros
- Server-core pode não estar rodando
- Campos têm valores default quando DB indisponível
- Verificar `query_error` na resposta JSON

## 📊 Fluxo de Dados

```
Dashboard JavaScript (polling)
    ↓ fetch('/api/v1/health')
analytics_dashboard FastAPI
    ↓ HTTP → server-core:8000/api/v1/metrics
server-core (Prometheus + DB queries)
    ↓ SQLAlchemy
PostgreSQL (dados reais)
```

## 📄 Licença

MIT License - F.A.R.O. Project