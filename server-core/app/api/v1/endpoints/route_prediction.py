"""
F.A.R.O. Route Prediction API - Predict future routes based on historical patterns.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import User, UserRole
from app.schemas.route_prediction import (
    RoutePredictionRequest,
    RoutePredictionResponse,
    RoutePredictionForPlateRequest,
    RoutePredictionForPlateResponse,
    PatternDriftAlertResponse,
    RecurringRouteAlertResponse,
)
from app.services.route_prediction_service import (
    predict_route,
    get_route_predictions_for_plate,
    get_pattern_drift_alert,
    get_recurring_route_alerts,
)

router = APIRouter()


def require_intelligence_role(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Acesso de inteligencia requerido")
    if current_user.role != UserRole.ADMIN and current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    return current_user


@router.post("/route-prediction", response_model=RoutePredictionResponse)
async def predict_route_endpoint(
    prediction_request: RoutePredictionRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Predict future route for a vehicle based on historical patterns."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    from app.services.route_prediction_service import RoutePredictionRequest as ServiceRequest
    
    service_request = ServiceRequest(
        plate_number=prediction_request.plate_number,
        agency_id=current_user.agency_id,
        min_observations=prediction_request.min_observations,
    )
    
    prediction = await predict_route(db, service_request)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum padrao de rota encontrado para {prediction_request.plate_number}",
        )
    
    return RoutePredictionResponse(
        plate_number=prediction.plate_number,
        predicted_corridor=prediction.predicted_corridor,
        confidence=prediction.confidence,
        predicted_hours=prediction.predicted_hours,
        predicted_days=prediction.predicted_days,
        last_pattern_analyzed=prediction.last_pattern_analyzed,
        pattern_strength=prediction.pattern_strength,
    )


@router.post("/route-prediction/for-plate", response_model=RoutePredictionForPlateResponse)
async def get_route_predictions_for_plate_endpoint(
    prediction_request: RoutePredictionForPlateRequest,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get route predictions for the next N days."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    predictions = await get_route_predictions_for_plate(
        db,
        plate_number=prediction_request.plate_number,
        agency_id=current_user.agency_id,
        days_ahead=prediction_request.days_ahead,
    )
    
    return RoutePredictionForPlateResponse(predictions=predictions)


@router.post("/route-prediction/pattern-drift", response_model=PatternDriftAlertResponse)
async def get_pattern_drift_alert_endpoint(
    plate_number: str,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Check if recent observations deviate significantly from historical pattern."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    alert = await get_pattern_drift_alert(db, plate_number, current_user.agency_id)
    
    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum alerta de drift encontrado para {plate_number}",
        )
    
    return PatternDriftAlertResponse(**alert)


@router.get("/route-prediction/recurring-alerts", response_model=list[RecurringRouteAlertResponse])
async def get_recurring_route_alerts_endpoint(
    min_recurrence_score: float = 0.7,
    min_pattern_strength: float = 0.6,
    current_user: User = Depends(require_intelligence_role),
    db: AsyncSession = Depends(get_db),
):
    """Get alerts for plates with strong recurring route patterns."""
    if current_user.agency_id is None:
        raise HTTPException(status_code=403, detail="Usuario sem vinculacao de agencia")
    
    alerts = await get_recurring_route_alerts(
        db,
        current_user.agency_id,
        min_recurrence_score,
        min_pattern_strength,
    )
    
    return [RecurringRouteAlertResponse(**alert) for alert in alerts]
