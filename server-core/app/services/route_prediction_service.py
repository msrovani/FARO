"""
Route Prediction Service for F.A.R.O.
Predicts future routes based on historical patterns.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from geoalchemy2.shape import to_shape
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import RoutePattern, VehicleObservation


@dataclass
class RoutePrediction:
    """Predicted route for a vehicle."""
    plate_number: str
    predicted_corridor: List[tuple[float, float]]  # (lat, lng)
    confidence: float
    predicted_hours: List[int]
    predicted_days: List[int]
    last_pattern_analyzed: datetime
    pattern_strength: float


@dataclass
class RoutePredictionRequest:
    """Request for route prediction."""
    plate_number: str
    agency_id: UUID
    min_observations: int = 5


async def predict_route(
    db: AsyncSession,
    request: RoutePredictionRequest,
) -> Optional[RoutePrediction]:
    """
    Predict future route for a vehicle based on historical patterns.
    Uses existing RoutePattern data to make predictions.
    """
    # Get latest route pattern for the plate
    query = select(RoutePattern).where(
        and_(
            RoutePattern.plate_number == request.plate_number.upper(),
            RoutePattern.agency_id == request.agency_id,
            RoutePattern.observation_count >= request.min_observations,
        )
    ).order_by(RoutePattern.analyzed_at.desc()).limit(1)
    
    pattern = (await db.execute(query)).scalar_one_or_none()
    
    if not pattern:
        return None
    
    # Extract corridor points from pattern
    corridor_points = []
    if pattern.corridor:
        corridor_shape = to_shape(pattern.corridor)
        corridor_points = [(lat, lng) for lng, lat in corridor_shape.coords]
    
    # Calculate prediction confidence based on pattern strength and recurrence
    confidence = min(1.0, pattern.pattern_strength * 0.7 + pattern.recurrence_score * 0.3)
    
    # Use temporal patterns from RoutePattern
    predicted_hours = pattern.common_hours or []
    predicted_days = pattern.common_days or []
    
    return RoutePrediction(
        plate_number=pattern.plate_number,
        predicted_corridor=corridor_points,
        confidence=confidence,
        predicted_hours=predicted_hours,
        predicted_days=predicted_days,
        last_pattern_analyzed=pattern.analyzed_at,
        pattern_strength=pattern.pattern_strength,
    )


async def get_route_predictions_for_plate(
    db: AsyncSession,
    plate_number: str,
    agency_id: UUID,
    days_ahead: int = 7,
) -> List[dict]:
    """
    Get route predictions for the next N days.
    Returns predicted locations and times.
    """
    request = RoutePredictionRequest(plate_number=plate_number, agency_id=agency_id)
    prediction = await predict_route(db, request)
    
    if not prediction:
        return []
    
    predictions = []
    today = datetime.utcnow()
    
    for day_offset in range(days_ahead):
        target_date = today + timedelta(days=day_offset)
        target_day = target_date.weekday()
        
        # Check if this day is in predicted days
        if prediction.predicted_days and target_day not in prediction.predicted_days:
            continue
        
        # Generate predictions for predicted hours
        for hour in prediction.predicted_hours or []:
            predictions.append({
                "date": target_date.date().isoformat(),
                "hour": hour,
                "confidence": prediction.confidence,
                "corridor_points": prediction.predicted_corridor,
                "pattern_strength": prediction.pattern_strength,
            })
    
    return predictions


async def get_pattern_drift_alert(
    db: AsyncSession,
    plate_number: str,
    agency_id: UUID,
    max_drift_percent: float = 30.0,
) -> Optional[dict]:
    """
    Check if recent observations deviate significantly from historical pattern.
    Returns alert if drift exceeds threshold.
    """
    # Get latest pattern
    query = select(RoutePattern).where(
        and_(
            RoutePattern.plate_number == plate_number.upper(),
            RoutePattern.agency_id == agency_id,
        )
    ).order_by(RoutePattern.analyzed_at.desc()).limit(1)
    
    pattern = (await db.execute(query)).scalar_one_or_none()
    
    if not pattern:
        return None
    
    # Get recent observations (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    obs_query = select(VehicleObservation).where(
        and_(
            VehicleObservation.plate_number == plate_number.upper(),
            VehicleObservation.agency_id == agency_id,
            VehicleObservation.observed_at_local >= week_ago,
        )
    )
    
    recent_observations = (await db.execute(obs_query)).scalars().all()
    
    if len(recent_observations) < 3:
        return None
    
    # Simple drift detection: check if recent observations are within pattern corridor
    from shapely.geometry import Point, LineString
    
    if pattern.corridor:
        corridor_shape = to_shape(pattern.corridor)
        corridor_line = LineString(corridor_shape.coords)
        
        out_of_corridor = 0
        for obs in recent_observations:
            obs_point = to_shape(obs.location)
            # Check distance to corridor
            distance = obs_point.distance(corridor_line)
            if distance > 0.01:  # ~1km in degrees
                out_of_corridor += 1
        
        drift_percent = (out_of_corridor / len(recent_observations)) * 100
        
        if drift_percent > max_drift_percent:
            return {
                "plate_number": plate_number,
                "drift_percent": drift_percent,
                "threshold_percent": max_drift_percent,
                "out_of_corridor_count": out_of_corridor,
                "total_recent_observations": len(recent_observations),
                "pattern_analyzed_at": pattern.analyzed_at.isoformat(),
                "alert_type": "pattern_drift",
            }
    
    return None


async def get_recurring_route_alerts(
    db: AsyncSession,
    agency_id: UUID,
    min_recurrence_score: float = 0.7,
    min_pattern_strength: str = "moderate",
    limit: int = 100,
) -> List[dict]:
    """
    Get alerts for plates with strong recurring route patterns.
    Useful for identifying potential regular suspicious activity.
    """
    query = select(RoutePattern).where(
        and_(
            RoutePattern.agency_id == agency_id,
            RoutePattern.recurrence_score >= min_recurrence_score,
        )
    ).order_by(RoutePattern.recurrence_score.desc()).limit(limit)
    
    patterns = (await db.execute(query)).scalars().all()
    
    alerts = []
    for pattern in patterns:
        alerts.append({
            "plate_number": pattern.plate_number,
            "recurrence_score": pattern.recurrence_score,
            "pattern_strength": pattern.pattern_strength,
            "primary_corridor": pattern.primary_corridor_name,
            "predominant_direction": pattern.predominant_direction,
            "observation_count": pattern.observation_count,
            "analyzed_at": pattern.analyzed_at.isoformat(),
            "alert_type": "recurring_route",
        })
    
    return alerts
