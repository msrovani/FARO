"""
F.A.R.O. API Routes - Route aggregation
"""
from fastapi import APIRouter

from app.api.v1.endpoints import alerts, alert_history, audit, auth, assets, boletim_atendimento, documentation, hotspots, intelligence, mobile, route_prediction, suspicious_routes, websocket, devices

api_router = APIRouter()

# Auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

# Mobile app routes
api_router.include_router(
    mobile.router,
    prefix="/mobile",
    tags=["Mobile App"],
)

# Intelligence console routes
api_router.include_router(
    intelligence.router,
    prefix="/intelligence",
    tags=["Intelligence"],
)

api_router.include_router(
    devices.router,
    prefix="/intelligence/devices",
    tags=["Devices Management"],
)

# Audit routes
api_router.include_router(
    audit.router,
    prefix="/audit",
    tags=["Audit"],
)

# Alert History routes (Prometheus)
api_router.include_router(
    alert_history.router,
    prefix="/monitoring",
    tags=["Monitoring - Alert History"],
)

api_router.include_router(
    suspicious_routes.router,
    prefix="/intelligence",
    tags=["Suspicious Routes"],
)

api_router.include_router(
    hotspots.router,
    prefix="/intelligence",
    tags=["Hotspots"],
)

api_router.include_router(
    route_prediction.router,
    prefix="/intelligence",
    tags=["Route Prediction"],
)

api_router.include_router(
    alerts.router,
    prefix="/intelligence",
    tags=["Alerts"],
)

# WebSocket routes
api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"],
)

# Boletim de Atendimento (BA) routes
api_router.include_router(
    boletim_atendimento.router,
    prefix="/intelligence",
    tags=["Boletim de Atendimento"],
)

# Documentation routes
api_router.include_router(
    documentation.router,
    prefix="/documentation",
    tags=["Documentation"],
)

# Assets routes (serve images/files from storage)
api_router.include_router(
    assets.router,
    prefix="/v1",
    tags=["Assets"],
)
