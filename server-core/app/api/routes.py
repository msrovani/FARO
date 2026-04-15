"""
F.A.R.O. API Routes - Route aggregation
"""
from fastapi import APIRouter

from app.api.v1.endpoints import alert, audit, auth, hotspots, intelligence, mobile, route_prediction, suspicious_routes, websocket

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
    audit.router,
    prefix="/audit",
    tags=["Audit"],
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
    alert.router,
    prefix="/intelligence",
    tags=["Alerts"],
)

# WebSocket routes
api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"],
)
