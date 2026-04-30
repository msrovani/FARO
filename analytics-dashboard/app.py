"""
F.A.R.O. Analytics Dashboard - FastAPI
===================================
Dashboard analítico em tempo real para monitoramento do sistema.
Pode rodar separadamente do server-core.

Uso:
    python -m analytics-dashboard.app
    # Acesse: http://localhost:9002/dashboard

Ou integrado ao server-core:
    from analytics_dashboard.api import router
    app.include_router(router, prefix="/analytics")
"""
from __future__ import annotations

import time
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================================
# Data Models
# ============================================================================


class SystemMetrics(BaseModel):
    """Métricas do sistema em tempo real."""
    timestamp: datetime
    uptime_seconds: float
    
    # HTTP
    http_requests_total: int = 0
    http_errors_5xx: int = 0
    http_latency_p95: float = 0.0
    
    # Database
    db_pool_size: int = 0
    db_pool_available: int = 0
    db_pool_overflow: int = 0
    db_healthy: bool = True
    
    # PgBouncer
    pgbouncer_in_use: bool = False
    pgbouncer_available: int = 0
    pgbouncer_used: int = 0
    pgbouncer_recommended: bool = False
    
    # Cache Redis
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_ratio: float = 0.0
    redis_healthy: bool = True
    
    # Circuit Breakers
    circuit_breakers: dict = {}
    
    # Mobile Sync
    sync_pending: int = 0
    sync_failures: int = 0
    
    # Alerts
    active_alerts: int = 0
    
    # User Connectivity (Usability)
    user_online: int = 0
    user_offline: int = 0
    user_wifi: int = 0
    user_4g: int = 0
    user_3g: int = 0
    network_quality_avg: float = 0.0
    
    # OCR Analytics
    ocr_mobile_success_rate: float = 0.0
    ocr_server_success_rate: float = 0.0
    ocr_corrections_total: int = 0
    ocr_latency_avg: float = 0.0
    
    # Alert Operations
    alerts_today: int = 0
    alerts_fired_today: int = 0
    
    # Suspicion Analytics
    suspicion_confirmed: int = 0
    suspicion_rejected: int = 0
    suspicion_accuracy: float = 0.0
    suspicion_recurrence: int = 0
    suspicion_critical: int = 0
    suspicion_high: int = 0
    suspicion_medium: int = 0
    suspicion_low: int = 0
    
    # Alerts by Algorithm
    algo_watchlist: int = 0
    algo_impossible_travel: int = 0
    algo_route_anomaly: int = 0
    algo_sensitive_zone: int = 0
    algo_convoy: int = 0
    algo_roaming: int = 0


class Alert(BaseModel):
    """Alerta individual."""
    id: str
    name: str
    severity: str
    urgency: str
    message: str
    timestamp: datetime
    acknowledged: bool = False


class HealthStatus(BaseModel):
    """Status geral de saúde."""
    status: str  # healthy, warning, critical
    timestamp: datetime
    metrics: SystemMetrics
    alerts: list[Alert]
    recommendations: list[str]


# ============================================================================
# WebSocket Manager
# ============================================================================


class ConnectionManager:
    """Gerencia conexões WebSocket para updates em tempo real."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ============================================================================
# Metrics Collector
# ============================================================================


class MetricsCollector:
    """Coleta métricas de várias fontes."""
    
    def __init__(self):
        self.start_time = time.time()
        self._http_requests = 0
        self._http_errors = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._sync_failures = 0
        self._alerts: list[Alert] = []
        
        # Usability/Analytics metrics - DEFAULT TO ZERO (no demo data)
        self._user_online = 0
        self._user_offline = 0
        self._user_wifi = 0
        self._user_4g = 0
        self._user_3g = 0
        self._network_quality = 0.0
        
        self._ocr_mobile_rate = 0.0
        self._ocr_server_rate = 0.0
        self._ocr_corrections = 0
        self._ocr_latency = 0.0
        
        self._alerts_today = 0
        self._suspicion_confirmed = 0
        self._suspicion_rejected = 0
        self._suspicion_accuracy = 0.0
        self._suspicion_recurrence = 0
        
        self._severity_critical = 0
        self._severity_high = 0
        self._severity_medium = 0
        self._severity_low = 0
        
        self._algo_watchlist = 0
        self._algo_impossible = 0
        self._algo_route = 0
        self._algo_sensitive = 0
        self._algo_convoy = 0
        self._algo_roaming = 0
        
        # Flag to track if DB is available
        self._db_available = False
        self._server_available = False
    
    async def collect(self) -> SystemMetrics:
        """Coleta todas as métricas disponíveis."""
        
        # Try to get metrics from main app if available
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            uptime_seconds=time.time() - self.start_time,
        )
        
        # Try to get from main server via HTTP
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                for port in [8000, 8080]:
                    try:
                        resp = await client.get(f"http://localhost:{port}/api/v1/metrics")
                        if resp.status_code == 200:
                            data = resp.json()
                            print(f"[MetricsCollector] Connected to server on port {port}")
                            print(f"[MetricsCollector] Received data keys: {list(data.keys())}")
                            # Update metrics from server response
                            metrics.db_pool_size = data.get("db_pool_size", 0)
                            metrics.db_pool_available = data.get("db_pool_available", 0)
                            metrics.db_pool_overflow = data.get("db_pool_overflow", 0)
                            metrics.db_healthy = data.get("db_healthy", True)
                            metrics.pgbouncer_in_use = data.get("pgbouncer_in_use", False)
                            metrics.cache_hit_ratio = data.get("cache_hit_ratio", 0.0)
                            metrics.redis_healthy = data.get("redis_healthy", True)
                            metrics.circuit_breakers = data.get("circuit_breakers", {})
                            
                            # Usability metrics
                            metrics.user_online = data.get("user_online", 0)
                            metrics.user_offline = data.get("user_offline", 0)
                            metrics.user_wifi = data.get("user_wifi", 0)
                            metrics.user_4g = data.get("user_4g", 0)
                            metrics.user_3g = data.get("user_3g", 0)
                            metrics.network_quality_avg = data.get("network_quality_avg", 0.0)
                            
                            # OCR metrics
                            metrics.ocr_mobile_success_rate = data.get("ocr_mobile_success_rate", 0.0)
                            metrics.ocr_server_success_rate = data.get("ocr_server_success_rate", 0.0)
                            metrics.ocr_corrections_total = data.get("ocr_corrections_total", 0)
                            metrics.ocr_latency_avg = data.get("ocr_latency_avg", 0.0)
                            
                            # Alert metrics
                            metrics.alerts_today = data.get("alerts_today", 0)
                            metrics.suspicion_confirmed = data.get("suspicion_confirmed", 0)
                            metrics.suspicion_rejected = data.get("suspicion_rejected", 0)
                            metrics.suspicion_accuracy = data.get("suspicion_accuracy", 0.0)
                            metrics.suspicion_recurrence = data.get("suspicion_recurrence", 0)
                            
                            # Severity metrics
                            metrics.suspicion_critical = data.get("suspicion_critical", 0)
                            metrics.suspicion_high = data.get("suspicion_high", 0)
                            metrics.suspicion_medium = data.get("suspicion_medium", 0)
                            metrics.suspicion_low = data.get("suspicion_low", 0)
                            
                            # Algorithm metrics
                            metrics.algo_watchlist = data.get("algo_watchlist", 0)
                            metrics.algo_impossible_travel = data.get("algo_impossible_travel", 0)
                            metrics.algo_route_anomaly = data.get("algo_route_anomaly", 0)
                            metrics.algo_sensitive_zone = data.get("algo_sensitive_zone", 0)
                            metrics.algo_convoy = data.get("algo_convoy", 0)
                            metrics.algo_roaming = data.get("algo_roaming", 0)
                            
                            self._server_available = True
                            print(f"[MetricsCollector] Server available: True")
                            break
                    except Exception as e:
                        print(f"[MetricsCollector] Error connecting to port {port}: {e}")
                        continue
        except Exception as e:
            print(f"[MetricsCollector] Server not available: {e}")
            pass  # Server not available, run standalone
        
        # Fallback to default values if server not available
        if not self._server_available:
            metrics.user_online = self._user_online
            metrics.user_offline = self._user_offline
            metrics.user_wifi = self._user_wifi
            metrics.user_4g = self._user_4g
            metrics.user_3g = self._user_3g
            metrics.network_quality_avg = self._network_quality
            
            metrics.ocr_mobile_success_rate = self._ocr_mobile_rate
            metrics.ocr_server_success_rate = self._ocr_server_rate
            metrics.ocr_corrections_total = self._ocr_corrections
            metrics.ocr_latency_avg = self._ocr_latency
            
            metrics.alerts_today = self._alerts_today
            metrics.suspicion_confirmed = self._suspicion_confirmed
            metrics.suspicion_rejected = self._suspicion_rejected
            metrics.suspicion_accuracy = self._suspicion_accuracy
            metrics.suspicion_recurrence = self._suspicion_recurrence
            metrics.suspicion_critical = self._severity_critical
            metrics.suspicion_high = self._severity_high
            metrics.suspicion_medium = self._severity_medium
            metrics.suspicion_low = self._severity_low
            
            metrics.algo_watchlist = self._algo_watchlist
            metrics.algo_impossible_travel = self._algo_impossible
            metrics.algo_route_anomaly = self._algo_route
            metrics.algo_sensitive_zone = self._algo_sensitive
            metrics.algo_convoy = self._algo_convoy
            metrics.algo_roaming = self._algo_roaming
        
        # Update alerts based on metrics
        await self._update_alerts(metrics)
        
        return metrics
    
    async def _update_alerts(self, metrics: SystemMetrics):
        """Atualiza lista de alertas baseado nas métricas."""
        self._alerts = []
        
        # Check critical conditions
        if not metrics.db_healthy:
            self._alerts.append(Alert(
                id="db-unhealthy",
                name="Database Unhealthy",
                severity="critical",
                urgency="critical",
                message="Database is not responding",
                timestamp=datetime.utcnow(),
            ))
        
        if metrics.pgbouncer_recommended:
            self._alerts.append(Alert(
                id="pgbouncer-off",
                name="PgBouncer Recommended",
                severity="warning",
                urgency="high",
                message="Database overloaded + PgBouncer not in use. Enable PGBOUNCER_ENABLED=true",
                timestamp=datetime.utcnow(),
            ))
        
        if metrics.db_pool_overflow > 10:
            self._alerts.append(Alert(
                id="db-overflow",
                name="Database Pool Overflow",
                severity="warning",
                urgency="medium",
                message=f"Database pool overflow: {metrics.db_pool_overflow} connections",
                timestamp=datetime.utcnow(),
            ))
        
        # Check circuit breakers
        for endpoint, status in metrics.circuit_breakers.items():
            if status.get("state") == "open":
                self._alerts.append(Alert(
                    id=f"cb-open-{endpoint}",
                    name=f"Circuit Breaker Open: {endpoint}",
                    severity="critical",
                    urgency="high",
                    message=f"Circuit breaker for {endpoint} is OPEN",
                    timestamp=datetime.utcnow(),
                ))
        
        # Check Redis
        if not metrics.redis_healthy:
            self._alerts.append(Alert(
                id="redis-down",
                name="Redis Unavailable",
                severity="warning",
                urgency="medium",
                message="Redis cache is not responding",
                timestamp=datetime.utcnow(),
            ))
    
    def get_recommendations(self, metrics: SystemMetrics) -> list[str]:
        """Gera recomendações baseadas nas métricas."""
        recs = []
        
        if metrics.pgbouncer_recommended:
            recs.append("[URGENT] Enable PgBouncer - set PGBOUNCER_ENABLED=true")
        
        if metrics.db_pool_overflow > 10:
            recs.append(f"Database pool overflow ({metrics.db_pool_overflow}). Increase DATABASE_POOL_SIZE")
        
        if metrics.cache_hit_ratio < 0.5:
            recs.append(f"Cache hit ratio low ({metrics.cache_hit_ratio:.1%}). Consider increasing TTL")
        
        if metrics.http_errors_5xx > 10:
            recs.append(f"High error rate ({metrics.http_errors_5xx}%). Check logs")
        
        for endpoint, status in metrics.circuit_breakers.items():
            if status.get("state") == "open":
                recs.append(f"Circuit breaker open for {endpoint}. Check backend service")
        
        if not recs:
            recs.append("System healthy")
        
        return recs


collector = MetricsCollector()


# ============================================================================
# FastAPI App
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    print("[START] F.A.R.O. Analytics Dashboard starting...")
    print("[DASHBOARD] Dashboard: http://localhost:9002/dashboard")
    print("[API] API: http://localhost:9002/api/v1")
    print("[WS] WebSocket: ws://localhost:9002/ws")
    
    yield
    
    # Shutdown
    print("[STOP] Analytics Dashboard shutting down...")


app = FastAPI(
    title="F.A.R.O. Analytics Dashboard",
    description="Real-time monitoring dashboard for F.A.R.O.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routes
# ============================================================================


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "F.A.R.O. Analytics Dashboard",
        "version": "1.0.0",
        "dashboard": "/dashboard",
        "api": "/api/v1",
        "ws": "/ws",
    }


@app.get("/dashboard", tags=["Dashboard"])
async def dashboard():
    """Serve dashboard HTML."""
    return HTMLResponse(DASHBOARD_HTML)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates with actual metrics."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and send real metrics
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            elif data == "metrics":
                # Send actual metrics when requested
                metrics = await collector.collect()
                alerts = collector._alerts
                recommendations = collector.get_recommendations(metrics)
                
                # Convert datetime to string for JSON serialization
                metrics_dict = metrics.model_dump()
                if 'timestamp' in metrics_dict and isinstance(metrics_dict['timestamp'], datetime):
                    metrics_dict['timestamp'] = metrics_dict['timestamp'].isoformat()
                
                # Convert alert timestamps to string
                alerts_dict = []
                for alert in alerts:
                    alert_data = alert.model_dump()
                    if 'timestamp' in alert_data and isinstance(alert_data['timestamp'], datetime):
                        alert_data['timestamp'] = alert_data['timestamp'].isoformat()
                    alerts_dict.append(alert_data)
                
                await websocket.send_json({
                    "type": "metrics",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics_dict,
                    "alerts": alerts_dict,
                    "recommendations": recommendations,
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/v1/metrics", tags=["API"])
async def get_metrics():
    """Get current system metrics."""
    metrics = await collector.collect()
    return metrics


@app.get("/api/v1/health", tags=["API"])
async def get_health():
    """Get full health status with recommendations."""
    metrics = await collector.collect()
    alerts = collector._alerts
    recommendations = collector.get_recommendations(metrics)
    
    # Determine overall status
    status = "healthy"
    if any(a.severity == "critical" for a in alerts):
        status = "critical"
    elif any(a.severity == "warning" for a in alerts):
        status = "warning"
    
    return HealthStatus(
        status=status,
        timestamp=datetime.utcnow(),
        metrics=metrics,
        alerts=alerts,
        recommendations=recommendations,
    )


@app.get("/api/v1/alerts", tags=["API"])
async def get_alerts():
    """Get active alerts."""
    return {"alerts": collector._alerts}


@app.post("/api/v1/alerts/{alert_id}/acknowledge", tags=["API"])
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    for alert in collector._alerts:
        if alert.id == alert_id:
            alert.acknowledged = True
            return {"success": True, "alert_id": alert_id}
    return {"success": False, "error": "Alert not found"}


@app.get("/api/v1/audit/logs", tags=["API"])
async def get_audit_logs(
    resource_type: str = None,
    start_date: str = None,
    end_date: str = None,
    ttl_days: str = "30",
    page: str = "1",
    page_size: str = "50",
):
    """Get audit logs from the main server."""
    import httpx
    
    # Calculate TTL date if needed
    from datetime import datetime, timedelta
    calculated_start = start_date
    
    # Handle TTL=0 (no limit) or TTL>0 (limit by days)
    days = int(ttl_days) if ttl_days.isdigit() else 30
    if days > 0:
        calculated_start = (datetime.utcnow() - timedelta(days=days)).isoformat()
    # If days = 0, calculated_start stays None = no date limit
    
    # Try to get from main server
    server_available = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for port in [8000, 8080]:
                try:
                    params = {}
                    if resource_type:
                        params['resource_type'] = resource_type
                    if calculated_start:
                        params['start_date'] = calculated_start
                    if end_date:
                        params['end_date'] = end_date
                    params['page'] = page
                    params['page_size'] = page_size
                    
                    resp = await client.get(f"http://localhost:{port}/api/v1/audit/logs", params=params)
                    if resp.status_code == 200:
                        server_available = True
                        return resp.json()
                    elif resp.status_code == 401:
                        # Endpoint requires auth, skip to next port or return demo data
                        continue
                except Exception:
                    continue
    except Exception:
        pass
    
    # Return demo data for audit logs when server unavailable or requires auth
    from datetime import datetime, timedelta
    import uuid
    
    # Generate some demo audit logs
    demo_logs = []
    current_time = datetime.utcnow()
    
    # Sample audit log entries
    sample_actions = [
        ("user_login", "User", "Usuário autenticado"),
        ("api_access", "API", "Acesso à API"),
        ("observation_create", "Observation", "Observação registrada"),
        ("suspicion_create", "Suspicion", "Suspeição registrada"),
        ("alert_fire", "Alert", "Alerta disparado"),
        ("agent_location", "Agent", "Localização atualizada"),
    ]
    
    # Generate demo logs based on requested page size
    page_size_int = int(page_size)
    for i in range(min(page_size_int, 20)):  # Max 20 demo logs
        action, resource_type_demo, message = sample_actions[i % len(sample_actions)]
        log_time = current_time - timedelta(minutes=i*5)
        
        demo_logs.append({
            "id": str(uuid.uuid4()),
            "action": action,
            "resource_type": resource_type_demo,
            "resource_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "user_name": f"Agente_{i+1:03d}",
            "ip_address": f"192.168.1.{100 + (i % 155)}",
            "user_agent": "F.A.R.O. Mobile Agent v1.0",
            "timestamp": log_time.isoformat(),
            "details": {"message": message, "status": "success"},
            "session_id": str(uuid.uuid4()),
        })
    
    # Filter by resource type if specified
    if resource_type:
        demo_logs = [log for log in demo_logs if log["resource_type"] == resource_type]
    
    return {
        "data": demo_logs,
        "total": len(demo_logs),
        "page": int(page),
        "page_size": int(page_size),
        "server_available": server_available,
        "demo": True
    }


@app.get("/api/v1/monitoring/history", tags=["API"])
async def get_alert_history(
    alert_group: str = None,
    severity: str = None,
    start_date: str = None,
    end_date: str = None,
    acknowledged: bool = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get alert history from the main server."""
    import httpx
    
    # Try to get from main server
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for port in [8000, 8080]:
                try:
                    params = {}
                    if alert_group: params['alert_group'] = alert_group
                    if severity: params['severity'] = severity
                    if start_date: params['start_date'] = start_date
                    if end_date: params['end_date'] = end_date
                    if acknowledged is not None: params['acknowledged'] = str(acknowledged).lower()
                    params['limit'] = str(limit)
                    params['offset'] = str(offset)
                    
                    resp = await client.get(f"http://localhost:{port}/api/v1/monitoring/history", params=params)
                    if resp.status_code == 200:
                        return resp.json()
                except Exception:
                    continue
    except Exception:
        pass
    
    # NO DEMO DATA - Return empty with error indicator
    return {
        "error": "server_unavailable",
        "message": "Servidor não disponível. Mostrando 0 registros.",
        "data": [],
        "server_available": False
    }


@app.get("/api/v1/monitoring/history/stats", tags=["API"])
async def get_alert_stats(days: int = 30):
    """Get alert statistics."""
    # Try main server first
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for port in [8000, 8080]:
                try:
                    resp = await client.get(f"http://localhost:{port}/api/v1/monitoring/history/stats?days={days}")
                    if resp.status_code == 200:
                        return resp.json()
                except httpx.RequestError:
                    continue
                except httpx.HTTPStatusError:
                    continue
    except Exception:
        pass
    
    # NO DEMO DATA - Return zeros with error indicator
    return {
        "error": "server_unavailable",
        "message": "Servidor não disponível. Mostrando 0 alertas.",
        "total_alerts": 0,
        "by_severity": {"critical": 0, "warning": 0, "info": 0},
        "by_group": {},
        "unacknowledged": 0,
        "period_days": days,
        "server_available": False
    }


# Background task to broadcast metrics every 5 seconds
async def metrics_broadcaster():
    """Broadcast metrics to all connected clients."""
    while True:
        try:
            metrics = await collector.collect()
            alerts = collector._alerts
            recommendations = collector.get_recommendations(metrics)
            
            await manager.broadcast({
                "type": "metrics",
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics.model_dump(),
                "alerts": [a.model_dump() for a in alerts],
                "recommendations": recommendations,
            })
        except Exception as e:
            print(f"Error broadcasting: {e}")
        
        await asyncio.sleep(5)


# Start broadcaster on app startup
@app.on_event("startup")
async def startup():
    asyncio.create_task(metrics_broadcaster())


# ============================================================================
# Dashboard HTML
# ============================================================================


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>F.A.R.O. Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-dark: #0f1419;
            --bg-card: #1a2332;
            --bg-card-hover: #232f3e;
            --text-primary: #e7e9ea;
            --text-secondary: #8b98a5;
            --accent: #1d9bf0;
            --success: #00ba7c;
            --warning: #ffd400;
            --danger: #f4212e;
            --border: #2f3944;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .header {
            background: var(--bg-card);
            padding: 20px 30px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
        }
        
        .header h1 {
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .refresh-control {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        .refresh-control input[type="range"] {
            width: 120px;
            height: 6px;
            -webkit-appearance: none;
            background: var(--bg-card-hover);
            border-radius: 3px;
            outline: none;
            cursor: pointer;
        }
        
        .refresh-control input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
            transition: transform 0.15s;
        }
        
        .refresh-control input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.2);
        }
        
        .refresh-control input[type="range"]::-moz-range-thumb {
            width: 16px;
            height: 16px;
            background: var(--accent);
            border-radius: 50%;
            cursor: pointer;
            border: none;
        }
        
        #refresh-label {
            min-width: 40px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .status-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }
        
        .status-healthy { background: rgba(0, 184, 124, 0.2); color: var(--success); }
        .status-warning { background: rgba(255, 212, 0, 0.2); color: var(--warning); }
        .status-critical { background: rgba(244, 33, 46, 0.2); color: var(--danger); }
        
        /* Severity badges for alert history */
        .severity-critical { background: rgba(244, 33, 46, 0.2); color: #f4212e; }
        .severity-warning { background: rgba(255, 212, 0, 0.2); color: #ffcd00; }
        .severity-info { background: rgba(0, 122, 255, 0.2); color: #007aff; }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px 30px;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
        }
        
        .card h2 {
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric {
            font-size: 32px;
            font-weight: 700;
            margin: 10px 0;
        }
        
        .metric-label {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .metric-good { color: var(--success); }
        .metric-warning { color: var(--warning); }
        .metric-danger { color: var(--danger); }
        
        .alert-item {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid;
        }
        
        .alert-critical { background: rgba(244, 33, 46, 0.1); border-color: var(--danger); }
        .alert-warning { background: rgba(255, 212, 0, 0.1); border-color: var(--warning); }
        
        .alert-title {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }
        
        .alert-message {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        .alert-time {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 6px;
        }
        
        .rec-item {
            padding: 10px 14px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
            background: var(--bg-card-hover);
        }
        
        .rec-urgent { border-left: 3px solid var(--danger); }
        .rec-warning { border-left: 3px solid var(--warning); }
        .rec-ok { border-left: 3px solid var(--success); }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-dot-green { background: var(--success); }
        .status-dot-yellow { background: var(--warning); }
        .status-dot-red { background: var(--danger); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .last-update {
            font-size: 12px;
            color: var(--text-secondary);
            text-align: right;
            padding: 10px 30px;
        }
        
        .nav-tabs {
            display: flex;
            gap: 5px;
            padding: 0 30px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
        }
        
        .nav-tab {
            padding: 12px 20px;
            cursor: pointer;
            color: var(--text-secondary);
            border-bottom: 2px solid transparent;
        }
        
        .nav-tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .cb-indicator {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .cb-closed { background: rgba(0, 184, 124, 0.2); color: var(--success); }
        .cb-open { background: rgba(244, 33, 46, 0.2); color: var(--danger); }
        .cb-half { background: rgba(255, 212, 0, 0.2); color: var(--warning); }
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <span>📊</span>
            F.A.R.O. Analytics Dashboard
        </h1>
        <div id="global-status" class="status-badge status-healthy">
            <span class="status-indicator status-dot-green"></span>
            <span>HEALTHY</span>
        </div>
        <div class="refresh-control">
            <label for="refresh-slider">Refresh:</label>
            <input type="range" id="refresh-slider" min="0" max="8" value="1" step="1">
            <span id="refresh-label">5s</span>
        </div>
    </div>
    
    <div class="nav-tabs">
        <div class="nav-tab active" data-tab="overview">Overview</div>
        <div class="nav-tab" data-tab="alerts">Alerts</div>
        <div class="nav-tab" data-tab="db">Database</div>
        <div class="nav-tab" data-tab="circuit">Circuit Breakers</div>
        <div class="nav-tab" data-tab="usability">Usabilidade</div>
        <div class="nav-tab" data-tab="analytics">Analytics</div>
        <div class="nav-tab" data-tab="audit">Auditoria</div>
        <div class="nav-tab" data-tab="alert-history">Histórico Alertas</div>
    </div>
    
    <div id="overview" class="tab-content active">
        <div class="grid">
            <div class="card">
                <h2>HTTP Requests</h2>
                <div class="metric" id="http-requests">0</div>
                <div class="metric-label">Total requests</div>
            </div>
            
            <div class="card">
                <h2>HTTP Errors (5xx)</h2>
                <div class="metric" id="http-errors">0%</div>
                <div class="metric-label">Error rate</div>
            </div>
            
            <div class="card">
                <h2>Database Pool</h2>
                <div class="metric" id="db-pool">0/0</div>
                <div class="metric-label">Available / Total</div>
            </div>
            
            <div class="card">
                <h2>Cache Hit Ratio</h2>
                <div class="metric" id="cache-ratio">0%</div>
                <div class="metric-label">Hit ratio</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Active Alerts</h2>
                <div class="metric" id="alert-count">0</div>
                <div class="metric-label">Unacknowledged</div>
            </div>
            
            <div class="card">
                <h2>PgBouncer</h2>
                <div class="metric" id="pgbouncer-status">OFF</div>
                <div class="metric-label">Status</div>
            </div>
            
            <div class="card">
                <h2>Uptime</h2>
                <div class="metric" id="uptime">0s</div>
                <div class="metric-label">Since start</div>
            </div>
            
            <div class="card">
                <h2>Redis</h2>
                <div class="metric" id="redis-status">OK</div>
                <div class="metric-label">Status</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Recommendations</h2>
                <div id="recommendations">
                    <div class="rec-item rec-ok">System healthy</div>
                </div>
            </div>
        </div>
    </div>
    
    <div id="alerts" class="tab-content">
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Active Alerts</h2>
                <div id="alert-list">
                    <div style="color: var(--text-secondary); padding: 20px;">No active alerts</div>
                </div>
            </div>
        </div>
    </div>
    
    <div id="db" class="tab-content">
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Database Connection Pool</h2>
                <div class="metric" id="db-overflow">0</div>
                <div class="metric-label">Overflow Connections</div>
            </div>
        </div>
    </div>
    
    <div id="circuit" class="tab-content">
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Circuit Breakers</h2>
                <div id="circuit-list">
                    <div style="color: var(--text-secondary);">No circuit breakers</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- USABILITY TAB -->
    <div id="usability" class="tab-content">
        <div class="grid">
            <div class="card">
                <h2>Usuários Online</h2>
                <div class="metric" id="user-online">0</div>
                <div class="metric-label">Conectados ativos</div>
            </div>
            
            <div class="card">
                <h2>Usuários Offline</h2>
                <div class="metric" id="user-offline">0</div>
                <div class="metric-label">Desconectados</div>
            </div>
            
            <div class="card">
                <h2>WiFi</h2>
                <div class="metric" id="user-wifi">0</div>
                <div class="metric-label">Conectados via WiFi</div>
            </div>
            
            <div class="card">
                <h2>4G</h2>
                <div class="metric" id="user-4g">0</div>
                <div class="metric-label">Conectados via 4G</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Qualidade de Rede</h2>
                <div class="metric" id="network-quality">--</div>
                <div class="metric-label">Média da rede (1-4)</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Conectividade por Tipo</h2>
                <div id="connectivity-chart" style="height: 150px; display: flex; align-items: flex-end; justify-content: space-around; padding: 20px;">
                    <div style="text-align: center;"><div style="height: 60%; background: var(--accent); width: 40px; border-radius: 4px 4px 0 0;"></div><div style="margin-top: 8px;">WiFi</div></div>
                    <div style="text-align: center;"><div style="height: 80%; background: var(--success); width: 40px; border-radius: 4px 4px 0 0;"></div><div style="margin-top: 8px;">4G</div></div>
                    <div style="text-align: center;"><div style="height: 20%; background: var(--warning); width: 40px; border-radius: 4px 4px 0 0;"></div><div style="margin-top: 8px;">3G</div></div>
                    <div style="text-align: center;"><div style="height: 30%; background: var(--error); width: 40px; border-radius: 4px 4px 0 0;"></div><div style="margin-top: 8px;">Offline</div></div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- ANALYTICS TAB -->
    <div id="analytics" class="tab-content">
        <div class="grid">
            <div class="card">
                <h2>OCR Mobile</h2>
                <div class="metric" id="ocr-mobile-rate">--</div>
                <div class="metric-label">Taxa de acerto</div>
            </div>
            
            <div class="card">
                <h2>OCR Server</h2>
                <div class="metric" id="ocr-server-rate">--</div>
                <div class="metric-label">Taxa de acerto</div>
            </div>
            
            <div class="card">
                <h2>Alertas Hoje</h2>
                <div class="metric" id="alerts-today">0</div>
                <div class="metric-label">Total gerados</div>
            </div>
            
            <div class="card">
                <h2>Alertas por Algoritmo</h2>
                <div class="metric" id="alerts-by-algo">0</div>
                <div class="metric-label">watchlist</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Suspeitas Confirmadas</h2>
                <div class="metric" id="suspicion-confirmed">0</div>
                <div class="metric-label">Confirmadas</div>
            </div>
            
            <div class="card">
                <h2>Suspeitas Rejeitadas</h2>
                <div class="metric" id="suspicion-rejected">0</div>
                <div class="metric-label">Falso positivo</div>
            </div>
            
            <div class="card">
                <h2>Taxa de Acerto</h2>
                <div class="metric" id="suspicion-accuracy">--</div>
                <div class="metric-label">% acerto</div>
            </div>
            
            <div class="card">
                <h2>Reincidências</h2>
                <div class="metric" id="suspicion-recurrence">0</div>
                <div class="metric-label">2+ abordagens</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Severidade: CRITICAL</h2>
                <div class="metric" id="severity-critical">0</div>
                <div class="metric-label">Ativas</div>
            </div>
            
            <div class="card">
                <h2>Severidade: HIGH</h2>
                <div class="metric" id="severity-high">0</div>
                <div class="metric-label">Ativas</div>
            </div>
            
            <div class="card">
                <h2>Severidade: MEDIUM</h2>
                <div class="metric" id="severity-medium">0</div>
                <div class="metric-label">Ativas</div>
            </div>
            
            <div class="card">
                <h2>Severidade: LOW</h2>
                <div class="metric" id="severity-low">0</div>
                <div class="metric-label">Ativas</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Alertas por Algoritmo</h2>
                <div id="alerts-per-algorithm" style="padding: 20px;">
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>watchlist</span><span id="algo-watchlist">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>impossible_travel</span><span id="algo-impossible">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>route_anomaly</span><span id="algo-route">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>convoy</span><span id="algo-convoy">0</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border);">
                        <span>roaming</span><span id="algo-roaming">0</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- AUDIT TAB -->
    <div id="audit" class="tab-content">
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Filtros de Auditoria</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end;">
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Grupo / Tipo</label>
                        <select id="audit-group-filter" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                            <option value="">Todos</option>
                            <option value="observation">Observações</option>
                            <option value="review">Revisões</option>
                            <option value="suspicion">Suspeitas</option>
                            <option value="alert">Alertas</option>
                            <option value="auth">Autenticação</option>
                            <option value="device">Dispositivos</option>
                            <option value="feedback">Feedback</option>
                            <option value="watchlist">Watchlist</option>
                        </select>
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Data Início</label>
                        <input type="datetime-local" id="audit-start-date" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Data Fim</label>
                        <input type="datetime-local" id="audit-end-date" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">TTL (Retenção)</label>
                        <select id="audit-ttl" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                            <option value="0">Sem TTL (Ilimitado)</option>
                            <option value="30">1 Mês</option>
                            <option value="90">3 Meses</option>
                            <option value="180">6 Meses</option>
                            <option value="365">1 Ano</option>
                        </select>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button onclick="loadAuditLogs()" style="padding: 10px 20px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Buscar</button>
                    <button onclick="exportAudit(&quot;csv&quot;)" style="padding: 10px 20px; background: var(--success); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Exportar CSV</button>
                    <button onclick="exportAudit(&quot;json&quot;)" style="padding: 10px 20px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Exportar JSON</button>
                    <button onclick="resetAuditFilters()" style="padding: 10px 20px; background: var(--bg-card-hover); color: var(--text-primary); border: 1px solid var(--border); border-radius: 6px; cursor: pointer;">Limpar Filtros</button>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Registros de Auditoria</h2>
                <div id="audit-table-container" style="max-height: 400px; overflow-y: auto;">
                    <table id="audit-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead style="position: sticky; top: 0; background: var(--bg-card);">
                            <tr style="border-bottom: 2px solid var(--border);">
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Data/Hora</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Usuário</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Ação</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Tipo</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Recurso</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Detalhes</th>
                            </tr>
                        </thead>
                        <tbody id="audit-tbody">
                            <tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>
                        </tbody>
                    </table>
                </div>
                <div id="audit-pagination" style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border);">
                    <div style="color: var(--text-secondary); font-size: 12px;">
                        <span id="audit-total">0</span> registros encontrados
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="prevAuditPage()" id="audit-prev" style="padding: 8px 16px; background: var(--bg-card-hover); border: 1px solid var(--border); border-radius: 4px; cursor: pointer;" disabled>◀ Anterior</button>
                        <span id="audit-page" style="padding: 8px 16px; font-size: 13px;">Página 1</span>
                        <button onclick="nextAuditPage()" id="audit-next" style="padding: 8px 16px; background: var(--bg-card-hover); border: 1px solid var(--border); border-radius: 4px; cursor: pointer;" disabled>Próxima ▶</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- ALERT HISTORY TAB -->
    <div id="alert-history" class="tab-content">
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Filtros de Histórico de Alertas</h2>
                <div style="display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end;">
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Grupo de Alerta</label>
                        <select id="alert-group-filter" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                            <option value="">Todos</option>
                            <option value="faro_connection_pooling">Connection Pooling</option>
                            <option value="faro_database">Database</option>
                            <option value="faro_http">HTTP</option>
                            <option value="faro_circuit_breaker">Circuit Breaker</option>
                            <option value="faro_cache">Cache</option>
                            <option value="faro_system">Sistema</option>
                            <option value="faro_mobile_sync">Mobile Sync</option>
                            <option value="faro_user_connectivity">User Connectivity</option>
                            <option value="faro_ocr_analytics">OCR Analytics</option>
                            <option value="faro_alert_operations">Alert Operations</option>
                            <option value="faro_suspicion_analytics">Suspicion Analytics</option>
                            <option value="faro_sync_operations">Sync Operations</option>
                            <option value="faro_business_intelligence">Business Intelligence</option>
                        </select>
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Severidade</label>
                        <select id="alert-severity-filter" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                            <option value="">Todas</option>
                            <option value="critical">Critical</option>
                            <option value="warning">Warning</option>
                            <option value="info">Info</option>
                        </select>
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Data Início</label>
                        <input type="datetime-local" id="alert-start-date" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">Data Fim</label>
                        <input type="datetime-local" id="alert-end-date" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                    </div>
                    <div style="flex: 1; min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-size: 12px; color: var(--text-secondary);">TTL (Retenção)</label>
                        <select id="alert-ttl" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-card); color: var(--text-primary);">
                            <option value="0">Sem TTL (Ilimitado)</option>
                            <option value="30">1 Mês</option>
                            <option value="90">3 Meses</option>
                            <option value="180">6 Meses</option>
                            <option value="365">1 Ano</option>
                        </select>
                    </div>
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button onclick="loadAlertHistory()" style="padding: 10px 20px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Buscar</button>
                    <button onclick="exportAlertHistory(&quot;csv&quot;)" style="padding: 10px 20px; background: var(--success); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Exportar CSV</button>
                    <button onclick="exportAlertHistory(&quot;json&quot;)" style="padding: 10px 20px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Exportar JSON</button>
                    <button onclick="resetAlertHistoryFilters()" style="padding: 10px 20px; background: var(--bg-card-hover); color: var(--text-primary); border: 1px solid var(--border); border-radius: 6px; cursor: pointer;">Limpar Filtros</button>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Estatísticas</h2>
                <div id="alert-stats" style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 100px; padding: 12px; background: var(--bg-card-hover); border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold;" id="stat-total">0</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Total</div>
                    </div>
                    <div style="flex: 1; min-width: 100px; padding: 12px; background: rgba(244, 33, 46, 0.2); border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--danger);" id="stat-critical">0</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Críticos</div>
                    </div>
                    <div style="flex: 1; min-width: 100px; padding: 12px; background: rgba(255, 212, 0, 0.2); border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--warning);" id="stat-warning">0</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Warning</div>
                    </div>
                    <div style="flex: 1; min-width: 100px; padding: 12px; background: rgba(0, 184, 124, 0.2); border-radius: 6px; text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: var(--success);" id="stat-acknowledged">0</div>
                        <div style="font-size: 12px; color: var(--text-secondary);">Ack'd</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card" style="grid-column: span 2;">
                <h2>Histórico de Alertas</h2>
                <div id="alert-history-table-container" style="max-height: 400px; overflow-y: auto;">
                    <table id="alert-history-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                        <thead style="position: sticky; top: 0; background: var(--bg-card);">
                            <tr style="border-bottom: 2px solid var(--border);">
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Data/Hora</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Alerta</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Grupo</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Severidade</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Status</th>
                                <th style="padding: 12px 8px; text-align: left; color: var(--text-secondary);">Mensagem</th>
                            </tr>
                        </thead>
                        <tbody id="alert-history-tbody">
                            <tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>
                        </tbody>
                    </table>
                </div>
                <div id="alert-history-pagination" style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border);">
                    <div style="color: var(--text-secondary); font-size: 12px;">
                        <span id="alert-history-total">0</span> registros encontrados
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="prevAlertHistoryPage()" id="alert-history-prev" style="padding: 8px 16px; background: var(--bg-card-hover); border: 1px solid var(--border); border-radius: 4px; cursor: pointer;" disabled>◀ Anterior</button>
                        <span id="alert-history-page" style="padding: 8px 16px; font-size: 13px;">Página 1</span>
                        <button onclick="nextAlertHistoryPage()" id="alert-history-next" style="padding: 8px 16px; background: var(--bg-card-hover); border: 1px solid var(--border); border-radius: 4px; cursor: pointer;" disabled>Próxima ▶</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="last-update">
        Last update: <span id="last-update">--</span>
    </div>
    
    <script>
        // Global function for tab switching - define immediately at the top
        window.switchTab = function(tab, element) {
            console.log(`[switchTab] Switching to tab: ${tab}, element:`, element);
            
            try {
                // Remove active class from all tabs
                const allTabs = document.querySelectorAll('.nav-tab');
                console.log(`[switchTab] Found ${allTabs.length} tab elements`);
                allTabs.forEach(t => {
                    t.classList.remove('active');
                    console.log(`[switchTab] Removed active from tab: ${t.textContent}`);
                });
                
                // Remove active class from all tab contents
                const allContents = document.querySelectorAll('.tab-content');
                console.log(`[switchTab] Found ${allContents.length} content elements`);
                allContents.forEach(t => {
                    t.classList.remove('active');
                    console.log(`[switchTab] Removed active from content: ${t.id}`);
                });
                
                // Add active class to clicked tab element
                if (element) {
                    element.classList.add('active');
                    console.log(`[switchTab] Added active to clicked tab: ${element.textContent}`);
                } else {
                    console.warn(`[switchTab] Element is null, trying to find by data-tab`);
                    // Fallback: find tab by data-tab attribute
                    allTabs.forEach(t => {
                        if (t.getAttribute('data-tab') === tab) {
                            t.classList.add('active');
                            console.log(`[switchTab] Added active to tab by data-tab: ${t.textContent}`);
                        }
                    });
                }
                
                // Add active class to tab content
                const tabContent = document.getElementById(tab);
                if (tabContent) {
                    tabContent.classList.add('active');
                    console.log(`[switchTab] Tab content found and activated: ${tab}`);
                } else {
                    console.error(`[switchTab] Tab content NOT found: ${tab}`);
                    console.log(`[switchTab] Available content IDs:`, Array.from(allContents).map(c => c.id));
                }
            } catch (e) {
                console.error(`[switchTab] Error: ${e}`, e.stack);
            }
        };
        
        // Server status helper function
        function showServerStatus(tab, isOnline, message) {
            const statusEl = document.getElementById(`${tab}-server-status`);
            if (statusEl) {
                statusEl.className = isOnline ? 'server-status online' : 'server-status offline';
                statusEl.innerHTML = `<span class="status-dot"></span>${message}`;
            }
        }

        function setupTabListeners() {
            const navTabs = document.querySelector('.nav-tabs');
            if (!navTabs) {
                console.error('[Tabs] nav-tabs container not found');
                return;
            }
            
            navTabs.addEventListener('click', (e) => {
                const tabElement = e.target.closest('.nav-tab');
                if (!tabElement) return;
                
                const tabId = tabElement.getAttribute('data-tab');
                if (!tabId) {
                    console.warn('[Tabs] No data-tab attribute found');
                    return;
                }
                
                console.log(`[Tabs] Clicked tab: ${tabId}`);
                window.switchTab(tabId, tabElement);
            });
            
            console.log('[Tabs] Tab event listeners setup complete');
        }
        
        let ws = null;
        let reconnectAttempts = 0;
        let pollInterval = null;
        
        // Refresh intervals in milliseconds
        const refreshIntervals = [
            2000,   // 0: 2s (online)
            5000,   // 1: 5s (default - online)
            8000,   // 2: 8s (online)
            15000,  // 3: 15s
            30000,  // 4: 30s
            60000,  // 5: 1min
            300000, // 6: 5min
            900000, // 7: 15min
            1800000 // 8: 30min
        ];
        const refreshLabels = [
            '2s', '5s', '8s', '15s', '30s', '1min', '5min', '15min', '30min'
        ];
        
        // Initialize refresh slider
        function initDashboard() {
            console.log('[Init] Dashboard initialization');
            
            const slider = document.getElementById('refresh-slider');
            const label = document.getElementById('refresh-label');
            
            if (!slider) {
                console.error('[Init] Slider not found!');
                return;
            }
            
            console.log('[Init] Slider found, initializing');
            
            // Setup tab listeners
            setupTabListeners();
            
            // Set initial label
            const initialIdx = parseInt(slider.value);
            label.textContent = refreshLabels[initialIdx];
            
            // Start polling with initial interval
            console.log('[Init] Starting polling with interval:', refreshIntervals[initialIdx]);
            startPolling(refreshIntervals[initialIdx]);
            
            // Start WebSocket connection
            console.log('[Init] Starting WebSocket connection');
            connectWebSocket();
            
            slider.addEventListener('input', (e) => {
                const idx = parseInt(e.target.value);
                const interval = refreshIntervals[idx];
                label.textContent = refreshLabels[idx];
                console.log(`[Slider] Changed to index ${idx}, interval ${interval}ms`);
                
                // Restart polling with new interval
                if (pollInterval) {
                    clearInterval(pollInterval);
                }
                startPolling(interval);
            });
            
            console.log('[Init] Dashboard initialization complete');
        }
        
        // Try DOMContentLoaded, fallback to immediate execution
        let dashboardInitialized = false;
        function safeInitDashboard() {
            if (dashboardInitialized) {
                console.log('[Init] Dashboard already initialized, skipping');
                return;
            }
            dashboardInitialized = true;
            initDashboard();
        }
        
        // Always try to initialize on DOMContentLoaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', safeInitDashboard);
        } else {
            // If DOM is already loaded, initialize immediately
            console.log('[Init] DOM already loaded, initializing immediately');
            safeInitDashboard();
        }
        
        // Fallback: also try to initialize after a short delay
        setTimeout(() => {
            if (!dashboardInitialized) {
                console.warn('[Init] Dashboard not initialized after delay, forcing initialization');
                safeInitDashboard();
            }
        }, 1000);
        
        function startPolling(interval) {
            // Clear existing interval if any
            if (pollInterval) {
                console.log(`[Polling] Clearing existing interval`);
                clearInterval(pollInterval);
                pollInterval = null;
            }
            
            console.log(`[Polling] Starting new interval: ${interval}ms`);
            pollInterval = setInterval(async () => {
                try {
                    console.log(`[Polling] Fetching health data (interval: ${interval}ms)`);
                    const res = await fetch('/api/v1/health');
                    
                    if (!res.ok) {
                        console.error(`[Polling] HTTP error: ${res.status} ${res.statusText}`);
                        return;
                    }
                    
                    const data = await res.json();
                    console.log('[Polling] Health data received:', data);
                    
                    updateDashboard({
                        type: 'metrics',
                        timestamp: new Date().toISOString(),
                        metrics: data.metrics,
                        alerts: data.alerts,
                        recommendations: data.recommendations,
                    });
                } catch (e) {
                    console.error('[Polling] Error:', e);
                    document.getElementById('last-update').textContent = 'Error: ' + e.message;
                }
            }, interval);
            
            console.log(`[Polling] Started with interval: ${interval}ms`);
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
                // Request metrics immediately after connection
                ws.send('metrics');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'metrics') {
                    updateDashboard(data);
                } else if (data.type === 'pong') {
                    console.log('WebSocket pong received');
                }
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                reconnectAttempts++;
                setTimeout(connectWebSocket, Math.min(reconnectAttempts * 1000, 10000));
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            console.log('[updateDashboard] Called with data:', data);
            const { metrics, alerts, recommendations } = data;
            const timestamp = new Date(data.timestamp);
            
            const lastUpdateEl = document.getElementById('last-update');
            if (lastUpdateEl) {
                lastUpdateEl.textContent = timestamp.toLocaleTimeString();
                console.log('[updateDashboard] Updated last-update:', timestamp.toLocaleTimeString());
            } else {
                console.error('[updateDashboard] last-update element not found');
            }
            
            // Uptime
            if (document.getElementById('uptime')) {
                const uptimeSeconds = metrics.uptime_seconds || 0;
                const uptimeMinutes = Math.floor(uptimeSeconds / 60);
                const uptimeHours = Math.floor(uptimeMinutes / 60);
                const uptimeDays = Math.floor(uptimeHours / 24);
                
                let uptimeText = '';
                if (uptimeDays > 0) {
                    uptimeText = `${uptimeDays}d ${uptimeHours % 24}h`;
                } else if (uptimeHours > 0) {
                    uptimeText = `${uptimeHours}h ${uptimeMinutes % 60}m`;
                } else if (uptimeMinutes > 0) {
                    uptimeText = `${uptimeMinutes}m ${Math.floor(uptimeSeconds % 60)}s`;
                } else {
                    uptimeText = `${Math.floor(uptimeSeconds)}s`;
                }
                document.getElementById('uptime').textContent = uptimeText;
            }
            
            // HTTP
            if (document.getElementById('http-requests')) {
                document.getElementById('http-requests').textContent = 
                    (metrics.http_requests_total || 0).toLocaleString();
            }
            if (document.getElementById('http-errors')) {
                document.getElementById('http-errors').textContent = 
                    (metrics.http_errors_5xx || 0) + '%';
            }
            
            // Database
            if (document.getElementById('db-pool')) {
                const poolUsed = metrics.db_pool_size - metrics.db_pool_available;
                document.getElementById('db-pool').textContent = 
                    `${metrics.db_pool_available || 0}/${metrics.db_pool_size || 0}`;
            }
            if (document.getElementById('db-overflow')) {
                document.getElementById('db-overflow').textContent = metrics.db_pool_overflow || 0;
            }
            
            // Cache
            if (document.getElementById('cache-ratio')) {
                document.getElementById('cache-ratio').textContent = 
                    ((metrics.cache_hit_ratio || 0) * 100).toFixed(1) + '%';
            }
            
            // PgBouncer
            if (document.getElementById('pgbouncer-status')) {
                const pgbStatus = document.getElementById('pgbouncer-status');
                if (metrics.pgbouncer_in_use) {
                    pgbStatus.textContent = 'ON';
                    pgbStatus.className = 'metric metric-good';
                } else {
                    pgbStatus.textContent = 'OFF';
                    pgbStatus.className = 'metric metric-warning';
                }
            }
            
            // Redis
            if (document.getElementById('redis-status')) {
                document.getElementById('redis-status').textContent = 
                    metrics.redis_healthy ? 'OK' : 'DOWN';
                document.getElementById('redis-status').className = 
                    'metric ' + (metrics.redis_healthy ? 'metric-good' : 'metric-danger');
            }
            
            // Alerts
            if (document.getElementById('alert-count')) {
                document.getElementById('alert-count').textContent = alerts.length;
            }
            updateAlertList(alerts);
            
            // Recommendations
            updateRecommendations(recommendations);
            
            // Circuit Breakers
            updateCircuitBreakers(metrics.circuit_breakers);
            
            // Global status
            updateGlobalStatus(alerts, metrics);
        }
        
        function updateAlertList(alerts) {
            const container = document.getElementById('alert-list');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<div class="rec-item rec-ok">No active alerts</div>';
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div class="alert-item alert-${alert.severity}">
                    <div class="alert-title">${alert.name}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                </div>
            `).join('');
        }
        
        function updateRecommendations(recs) {
            const container = document.getElementById('recommendations');
            container.innerHTML = recs.map(rec => {
                let cls = 'rec-ok';
                if (rec.includes('URGENTE')) cls = 'rec-urgent';
                else if (rec.includes('WARN') || rec.includes('WARNING')) cls = 'rec-warning';
                return `<div class="rec-item ${cls}">${rec}</div>`;
            }).join('');
        }
        
        function updateCircuitBreakers(cbs) {
            const container = document.getElementById('circuit-list');
            if (!cbs || Object.keys(cbs).length === 0) {
                container.innerHTML = '<div style="color: var(--text-secondary);">No circuit breakers</div>';
                return;
            }
            
            container.innerHTML = Object.entries(cbs).map(([name, status]) => {
                const state = status.state || 'unknown';
                let cls = 'cb-closed';
                if (state === 'open') cls = 'cb-open';
                else if (state === 'half_open') cls = 'cb-half';
                
                return `
                    <div style="padding: 10px; margin-bottom: 8px; background: var(--bg-card-hover); border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600;">${name}</span>
                            <span class="cb-indicator ${cls}">${state.toUpperCase()}</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
                            Failures: ${status.failures} | Successes: ${status.successes}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateGlobalStatus(alerts, metrics) {
            const badge = document.getElementById('global-status');
            const hasCritical = alerts.some(a => a.severity === 'critical');
            const hasWarning = alerts.some(a => a.severity === 'warning');
            
            if (hasCritical) {
                badge.className = 'status-badge status-critical';
                badge.innerHTML = '<span class="status-indicator status-dot-red"></span>CRITICAL';
            } else if (hasWarning) {
                badge.className = 'status-badge status-warning';
                badge.innerHTML = '<span class="status-indicator status-dot-yellow"></span>WARNING';
            } else {
                badge.className = 'status-badge status-healthy';
                badge.innerHTML = '<span class="status-indicator status-dot-green"></span>HEALTHY';
            }
            
            // Update Usability Tab
            if (document.getElementById('user-online')) {
                document.getElementById('user-online').textContent = metrics.user_online || 0;
            }
            if (document.getElementById('user-offline')) {
                document.getElementById('user-offline').textContent = metrics.user_offline || 0;
            }
            if (document.getElementById('user-wifi')) {
                document.getElementById('user-wifi').textContent = metrics.user_wifi || 0;
            }
            if (document.getElementById('user-4g')) {
                document.getElementById('user-4g').textContent = metrics.user_4g || 0;
            }
            if (document.getElementById('user-3g')) {
                document.getElementById('user-3g').textContent = metrics.user_3g || 0;
            }
            if (document.getElementById('network-quality')) {
                document.getElementById('network-quality').textContent = (metrics.network_quality_avg || 0).toFixed(1);
            }
            
            // Update Analytics Tab
            if (document.getElementById('ocr-mobile-rate')) {
                document.getElementById('ocr-mobile-rate').textContent = (metrics.ocr_mobile_success_rate || 0).toFixed(0) + '%';
            }
            if (document.getElementById('ocr-server-rate')) {
                document.getElementById('ocr-server-rate').textContent = (metrics.ocr_server_success_rate || 0).toFixed(0) + '%';
            }
            if (document.getElementById('alerts-today')) {
                document.getElementById('alerts-today').textContent = metrics.alerts_today || 0;
            }
            if (document.getElementById('alerts-by-algo')) {
                document.getElementById('alerts-by-algo').textContent = metrics.algo_watchlist || 0;
            }
            if (document.getElementById('suspicion-confirmed')) {
                document.getElementById('suspicion-confirmed').textContent = metrics.suspicion_confirmed || 0;
            }
            if (document.getElementById('suspicion-rejected')) {
                document.getElementById('suspicion-rejected').textContent = metrics.suspicion_rejected || 0;
            }
            if (document.getElementById('suspicion-accuracy')) {
                document.getElementById('suspicion-accuracy').textContent = ((metrics.suspicion_accuracy || 0) * 100).toFixed(0) + '%';
            }
            if (document.getElementById('suspicion-recurrence')) {
                document.getElementById('suspicion-recurrence').textContent = metrics.suspicion_recurrence || 0;
            }
            
            // Severity distribution
            if (document.getElementById('severity-critical')) {
                document.getElementById('severity-critical').textContent = metrics.suspicion_critical || 0;
            }
            if (document.getElementById('severity-high')) {
                document.getElementById('severity-high').textContent = metrics.suspicion_high || 0;
            }
            if (document.getElementById('severity-medium')) {
                document.getElementById('severity-medium').textContent = metrics.suspicion_medium || 0;
            }
            if (document.getElementById('severity-low')) {
                document.getElementById('severity-low').textContent = metrics.suspicion_low || 0;
            }
            
            // Alerts per algorithm
            if (document.getElementById('algo-watchlist')) {
                document.getElementById('algo-watchlist').textContent = metrics.algo_watchlist || 0;
            }
            if (document.getElementById('algo-impossible')) {
                document.getElementById('algo-impossible').textContent = metrics.algo_impossible_travel || 0;
            }
            if (document.getElementById('algo-route')) {
                document.getElementById('algo-route').textContent = metrics.algo_route_anomaly || 0;
            }
            if (document.getElementById('algo-convoy')) {
                document.getElementById('algo-convoy').textContent = metrics.algo_convoy || 0;
            }
            if (document.getElementById('algo-roaming')) {
                document.getElementById('algo-roaming').textContent = metrics.algo_roaming || 0;
            }
        }
        
        // Audit tab functionality
        let auditData = [];
        let auditPage = 1;
        const auditPageSize = 50;
        
        async function loadAuditLogs() {
            const group = document.getElementById('audit-group-filter').value;
            const startDate = document.getElementById('audit-start-date').value;
            const endDate = document.getElementById('audit-end-date').value;
            const ttl = document.getElementById('audit-ttl').value;
            
            const params = new URLSearchParams();
            if (group) params.append('resource_type', group);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', end_date);
            params.append('ttl_days', ttl);
            params.append('page', '1');
            params.append('page_size', '500'); // Get more for export
            
            try {
                const res = await fetch(`/api/v1/audit/logs?${params.toString()}`);
                const data = await res.json();
                
                // Check if server is available
                if (data.error === 'server_unavailable') {
                    // Show server unavailable warning
                    showServerStatus('audit', false, data.message);
                    auditData = [];
                } else {
                    showServerStatus('audit', true, 'Conectado ao servidor');
                    auditData = Array.isArray(data) ? data : (data.data || []);
                }
                
                auditPage = 1;
                renderAuditTable();
            } catch (e) {
                console.error('Audit load error:', e);
                showServerStatus('audit', false, 'Erro de conexão: ' + e.message);
                auditData = [];
                renderAuditTable();
            }
        }
        
        function renderAuditTable() {
            const tbody = document.getElementById('audit-tbody');
            const start = (auditPage - 1) * auditPageSize;
            const end = start + auditPageSize;
            const pageData = auditData.slice(start, end);
            
            if (pageData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Nenhum registro encontrado</td></tr>';
            } else {
                tbody.innerHTML = pageData.map(log => `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 10px 8px;">${log.created_at ? new Date(log.created_at).toLocaleString('pt-BR') : '-'}</td>
                        <td style="padding: 10px 8px;">${log.actor_name || log.actor_user_id || '-'}</td>
                        <td style="padding: 10px 8px;"><span style="background: var(--accent); padding: 2px 8px; border-radius: 4px; font-size: 11px;">${log.action || '-'}</span></td>
                        <td style="padding: 10px 8px;">${log.entity_type || '-'}</td>
                        <td style="padding: 10px 8px; font-family: monospace; font-size: 11px;">${log.entity_id ? String(log.entity_id).substring(0, 8) + '...' : '-'}</td>
                        <td style="padding: 10px 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${log.justification || (log.details ? JSON.stringify(log.details).substring(0, 50) : '-')}</td>
                    </tr>
                `).join('');
            }
            
            // Update pagination info
            document.getElementById('audit-total').textContent = auditData.length;
            document.getElementById('audit-page').textContent = `Página ${auditPage}`;
            document.getElementById('audit-prev').disabled = auditPage <= 1;
            document.getElementById('audit-next').disabled = end >= auditData.length;
        }
        
        function prevAuditPage() {
            if (auditPage > 1) {
                auditPage--;
                renderAuditTable();
            }
        }
        
        function nextAuditPage() {
            if (auditPage * auditPageSize < auditData.length) {
                auditPage++;
                renderAuditTable();
            }
        }
        
        function exportAudit(format) {
            if (auditData.length === 0) {
                alert('Nenhum dado para exportar. Execute uma busca primeiro.');
                return;
            }
            
            if (format === 'csv') {
                const headers = ['Data/Hora', 'Usuário', 'Ação', 'Tipo', 'Recurso', 'Justificação'];
                const rows = auditData.map(log => [
                    log.created_at || '',
                    log.actor_name || log.actor_user_id || '',
                    log.action || '',
                    log.entity_type || '',
                    log.entity_id || '',
                    log.justification || ''
                ]);
                
                const csv = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';')).join('\n');
                downloadFile(csv, 'faro_audit_log.csv', 'text/csv');
            } else {
                const json = JSON.stringify(auditData, null, 2);
                downloadFile(json, 'faro_audit_log.json', 'application/json');
            }
        }
        
        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function resetAuditFilters() {
            document.getElementById('audit-group-filter').value = '';
            document.getElementById('audit-start-date').value = '';
            document.getElementById('audit-end-date').value = '';
            document.getElementById('audit-ttl').value = '30';
            auditData = [];
            auditPage = 1;
            document.getElementById('audit-tbody').innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>';
            document.getElementById('audit-total').textContent = '0';
        }
        
        // Alert History functionality
        let alertHistoryData = [];
        let alertHistoryPage = 1;
        const alertHistoryPageSize = 50;
        
        async function loadAlertHistory() {
            const alertGroup = document.getElementById('alert-group-filter').value;
            const severity = document.getElementById('alert-severity-filter').value;
            const startDate = document.getElementById('alert-start-date').value;
            const endDate = document.getElementById('alert-end-date').value;
            const ttl = document.getElementById('alert-ttl').value;
            
            const params = new URLSearchParams();
            if (alertGroup) params.append('alert_group', alertGroup);
            if (severity) params.append('severity', severity);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', end_date);
            if (ttl) params.append('ttl_days', ttl);
            params.append('limit', '500');
            
            try {
                const res = await fetch(`/api/v1/monitoring/history?${params.toString()}`);
                const data = await res.json();
                
                // Check if server is available
                if (data.error === 'server_unavailable') {
                    showServerStatus('alert-history', false, data.message);
                    alertHistoryData = [];
                    updateAlertHistoryStats();
                } else {
                    showServerStatus('alert-history', true, 'Conectado ao servidor');
                    alertHistoryData = Array.isArray(data) ? data : (data.data || []);
                    updateAlertHistoryStats();
                }
                
                alertHistoryPage = 1;
                renderAlertHistoryTable();
            } catch (e) {
                console.error('Alert history load error:', e);
                showServerStatus('alert-history', false, 'Erro de conexão: ' + e.message);
                alertHistoryData = [];
                renderAlertHistoryTable();
            }
        }
        
        function renderAlertHistoryTable() {
            const tbody = document.getElementById('alert-history-tbody');
            const start = (alertHistoryPage - 1) * alertHistoryPageSize;
            const end = start + alertHistoryPageSize;
            const pageData = alertHistoryData.slice(start, end);
            
            if (pageData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Nenhum registro encontrado</td></tr>';
            } else {
                tbody.innerHTML = pageData.map(alert => `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 10px 8px;">${alert.fired_at ? new Date(alert.fired_at).toLocaleString('pt-BR') : '-'}</td>
                        <td style="padding: 10px 8px; font-weight: 600;">${alert.alert_name || '-'}</td>
                        <td style="padding: 10px 8px;">${alert.alert_group || '-'}</td>
                        <td style="padding: 10px 8px;"><span class="severity-${alert.severity}" style="padding: 2px 8px; border-radius: 4px; font-size: 11px;">${alert.severity || '-'}</span></td>
                        <td style="padding: 10px 8px;">${alert.acknowledged ? 'Ack' : (alert.resolved_at ? 'Resolved' : 'Firing')}</td>
                        <td style="padding: 10px 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${alert.message || alert.insight || '-'}</td>
                    </tr>
                `).join('');
            }
            
            // Update pagination info
            document.getElementById('alert-history-total').textContent = alertHistoryData.length;
            document.getElementById('alert-history-page').textContent = `Página ${alertHistoryPage}`;
            document.getElementById('alert-history-prev').disabled = alertHistoryPage <= 1;
            document.getElementById('alert-history-next').disabled = end >= alertHistoryData.length;
        }
        
        function updateAlertHistoryStats() {
            const total = alertHistoryData.length;
            const critical = alertHistoryData.filter(a => a.severity === 'critical').length;
            const warning = alertHistoryData.filter(a => a.severity === 'warning').length;
            const acknowledged = alertHistoryData.filter(a => a.acknowledged).length;
            
            document.getElementById('stat-total').textContent = total;
            document.getElementById('stat-critical').textContent = critical;
            document.getElementById('stat-warning').textContent = warning;
            document.getElementById('stat-acknowledged').textContent = acknowledged;
        }
        
        function prevAlertHistoryPage() {
            if (alertHistoryPage > 1) {
                alertHistoryPage--;
                renderAlertHistoryTable();
            }
        }
        
        function nextAlertHistoryPage() {
            if (alertHistoryPage * alertHistoryPageSize < alertHistoryData.length) {
                alertHistoryPage++;
                renderAlertHistoryTable();
            }
        }
        
        function exportAlertHistory(format) {
            if (alertHistoryData.length === 0) {
                alert('Nenhum dado para exportar. Execute uma busca primeiro.');
                return;
            }
            
            if (format === 'csv') {
                const headers = ['Data/Hora', 'Alerta', 'Grupo', 'Severidade', 'Status', 'Mensagem'];
                const rows = alertHistoryData.map(alert => [
                    alert.fired_at || '',
                    alert.alert_name || '',
                    alert.alert_group || '',
                    alert.severity || '',
                    alert.acknowledged ? 'Acknowledged' : (alert.resolved_at ? 'Resolved' : 'Firing'),
                    (alert.message || alert.insight || '').replace(/"/g, '""'),
                ]);
                
                const csv = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';')).join('\n');
                downloadFile(csv, 'faro_alert_history.csv', 'text/csv');
            } else {
                const json = JSON.stringify(alertHistoryData, null, 2);
                downloadFile(json, 'faro_alert_history.json', 'application/json');
            }
        }
        
        function resetAlertHistoryFilters() {
            document.getElementById('alert-group-filter').value = '';
            document.getElementById('alert-severity-filter').value = '';
            document.getElementById('alert-start-date').value = '';
            document.getElementById('alert-end-date').value = '';
            document.getElementById('alert-ttl').value = '30';
            alertHistoryData = [];
            alertHistoryPage = 1;
            document.getElementById('alert-history-tbody').innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>';
            document.getElementById('alert-history-total').textContent = '0';
            document.getElementById('stat-total').textContent = '0';
            document.getElementById('stat-critical').textContent = '0';
            document.getElementById('stat-warning').textContent = '0';
            document.getElementById('stat-acknowledged').textContent = '0';
        }
        
            </script>
</body>
</html>
"""


# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=9002,
        reload=False,
    )