"""
F.A.R.O. Location Interception Service
Links INTERCEPT algorithm with geolocation for targeted alerts.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_Point
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    AgentLocationLog, 
    InterceptEvent, 
    User, 
    UserRole, 
    VehicleObservation,
    Agency
)
from app.services.event_bus import event_bus

logger = logging.getLogger(__name__)


class LocationContext:
    """Context information for location-based interception."""
    
    def __init__(self, is_urban: bool, location_name: str, nearby_agents: List[dict]):
        self.is_urban = is_urban
        self.location_name = location_name
        self.nearby_agents = nearby_agents
        self.alert_radius_km = 10.0 if is_urban else 25.0  # Larger radius for highways


async def determine_location_context(
    db: AsyncSession, 
    observation: VehicleObservation
) -> LocationContext:
    """
    Determine if observation is in urban area or highway and find nearby agents.
    
    Uses spatial analysis to identify context and nearby field agents.
    """
    from geoalchemy2.shape import to_shape
    
    # Get observation point
    obs_point = to_shape(observation.location)
    obs_lat, obs_lng = obs_point.y, obs_point.x
    
    # Check if location is in urban area (simplified logic)
    # In production, this would use GIS data for city boundaries
    is_urban = await _is_urban_area(db, obs_lat, obs_lng)
    location_name = await _get_location_name(db, obs_lat, obs_lng, is_urban)
    
    # Find nearby agents
    nearby_agents = await _find_nearby_agents(db, obs_point, is_urban)
    
    return LocationContext(is_urban, location_name, nearby_agents)


async def _is_urban_area(db: AsyncSession, latitude: float, longitude: float) -> bool:
    """
    Determine if coordinates are in urban area.
    
    Simplified logic - in production would use city boundary GIS data.
    """
    # For now, assume areas with higher agent density are urban
    # Check if there are multiple agencies within 20km
    point = ST_Point(longitude, latitude, srid=4326)
    
    agency_count = await db.scalar(
        select(func.count(Agency.id))
        .where(
            ST_DWithin(
                Agency.location,
                point,
                20000  # 20km in meters
            )
        )
    )
    
    # If 3+ agencies nearby, consider it urban
    return agency_count >= 3


async def _get_location_name(db: AsyncSession, latitude: float, longitude: float, is_urban: bool) -> str:
    """
    Get human-readable location name.
    
    In production would use reverse geocoding service.
    """
    if is_urban:
        # For urban areas, find the nearest agency
        point = ST_Point(longitude, latitude, srid=4326)
        
        nearest_agency = await db.execute(
            select(Agency.name, Agency.city)
            .where(Agency.location.isnot(None))
            .order_by(ST_Distance(Agency.location, point))
            .limit(1)
        ).first()
        
        if nearest_agency:
            return f"{nearest_agency.city} - {nearest_agency.name}"
        else:
            return f"Área Urbana ({latitude:.3f}, {longitude:.3f})"
    else:
        # For highways, use coordinate reference
        return f"Rodovia ({latitude:.3f}, {longitude:.3f})"


async def _find_nearby_agents(
    db: AsyncSession, 
    obs_point, 
    is_urban: bool
) -> List[dict]:
    """
    Find field agents near the observation location.
    """
    from geoalchemy2.shape import to_shape
    
    # Define search radius based on context
    radius_meters = 10000 if is_urban else 25000  # 10km urban, 25km highway
    
    # Find agents with recent locations
    recent_time = datetime.utcnow() - timedelta(minutes=30)
    
    query = (
        select(
            User.id,
            User.full_name,
            User.badge_number,
            User.agency_id,
            Agency.name.label("agency_name"),
            Agency.city,
            AgentLocationLog.location,
            AgentLocationLog.recorded_at,
            ST_Distance(
                AgentLocationLog.location,
                ST_Point(obs_point.x, obs_point.y, srid=4326)
            ).label("distance_meters")
        )
        .select_from(AgentLocationLog)
        .join(User, User.id == AgentLocationLog.agent_id)
        .join(Agency, Agency.id == User.agency_id)
        .where(
            and_(
                User.role == UserRole.FIELD_AGENT,
                User.is_on_duty == True,
                AgentLocationLog.recorded_at >= recent_time,
                ST_DWithin(
                    AgentLocationLog.location,
                    ST_Point(obs_point.x, obs_point.y, srid=4326),
                    radius_meters
                )
            )
        )
        .order_by("distance_meters")
        .limit(10)  # Top 10 nearest agents
    )
    
    result = await db.execute(query)
    agents = []
    
    for row in result:
        agent_point = to_shape(row.location)
        agents.append({
            "agent_id": str(row.id),
            "full_name": row.full_name,
            "badge_number": row.badge_number,
            "agency_id": str(row.agency_id),
            "agency_name": row.agency_name,
            "city": row.city,
            "location": {
                "latitude": float(agent_point.y),
                "longitude": float(agent_point.x)
            },
            "recorded_at": row.recorded_at.isoformat(),
            "distance_meters": float(row.distance_meters),
            "distance_km": float(row.distance_meters) / 1000
        })
    
    return agents


async def create_location_based_alerts(
    db: AsyncSession,
    intercept_event: InterceptEvent,
    observation: VehicleObservation
) -> None:
    """
    Create targeted alerts based on location context.
    
    Sends alerts to Web Intelligence and nearby field agents.
    """
    # Get location context
    location_context = await determine_location_context(db, observation)
    
    # Create alert data
    alert_data = {
        "intercept_event_id": str(intercept_event.id),
        "plate_number": observation.plate_number,
        "observation_id": str(observation.id),
        "location": {
            "latitude": float(to_shape(observation.location).y),
            "longitude": float(to_shape(observation.location).x)
        },
        "intercept_score": intercept_event.intercept_score,
        "recommendation": intercept_event.recommendation,
        "priority_level": intercept_event.priority_level,
        "location_context": {
            "is_urban": location_context.is_urban,
            "location_name": location_context.location_name,
            "alert_radius_km": location_context.alert_radius_km
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Send to Web Intelligence (always)
    await _send_web_intelligence_alert(db, alert_data, location_context)
    
    # Send to field agents based on recommendation
    if intercept_event.recommendation in ["APPROACH", "MONITOR"]:
        await _send_field_agent_alerts(db, alert_data, location_context)
    
    # Log the alert creation
    logger.info(
        f"Location-based alert created for {observation.plate_number} "
        f"in {location_context.location_name} "
        f"({'urban' if location_context.is_urban else 'highway'}) "
        f"with {len(location_context.nearby_agents)} nearby agents"
    )


async def _send_web_intelligence_alert(
    db: AsyncSession,
    alert_data: dict,
    location_context: LocationContext
) -> None:
    """
    Send alert to Web Intelligence console.
    
    Published via event bus for real-time updates.
    """
    await event_bus.publish("intercept_location_alert", {
        "payload_version": "v1",
        "alert_type": "web_intelligence",
        "target": "console",
        "data": alert_data
    })
    
    logger.info(f"Web Intelligence alert sent for {alert_data['plate_number']}")


async def _send_field_agent_alerts(
    db: AsyncSession,
    alert_data: dict,
    location_context: LocationContext
) -> None:
    """
    Send alerts to nearby field agents via mobile push notification.
    
    Different logic for urban vs highway contexts.
    """
    nearby_agents = location_context.nearby_agents
    
    if location_context.is_urban:
        # Urban: Alert agents in the same city
        city_agents = [
            agent for agent in nearby_agents 
            if agent.get("city") and location_context.location_name.startswith(agent["city"])
        ]
        
        # If no city-specific agents, use nearest 3
        target_agents = city_agents if city_agents else nearby_agents[:3]
        
    else:
        # Highway: Alert nearest agents regardless of city
        # Focus on the closest agents for highway incidents
        target_agents = nearby_agents[:5]  # Top 5 nearest for highway
    
    # Send alerts to target agents
    for agent in target_agents:
        agent_alert = {
            **alert_data,
            "target_agent": {
                "agent_id": agent["agent_id"],
                "full_name": agent["full_name"],
                "distance_km": agent["distance_km"]
            },
            "alert_type": "field_agent",
            "target": "mobile"
        }
        
        await event_bus.publish("intercept_location_alert", {
            "payload_version": "v1",
            "alert_type": "field_agent",
            "target": "mobile",
            "agent_id": agent["agent_id"],
            "data": {
                **agent_alert,
                "tactical_alert": {
                    "alert_level": _map_priority_to_alert_level(intercept_event.priority_level),
                    "vibration_pattern": _get_vibration_pattern(intercept_event.priority_level),
                    "sound_type": _get_sound_type(intercept_event.priority_level),
                    "urgency": "high" if intercept_event.recommendation == "APPROACH" else "medium"
                }
            }
        })
    
    logger.info(
        f"Field agent alerts sent to {len(target_agents)} agents "
        f"for {alert_data['plate_number']} "
        f"({'urban' if location_context.is_urban else 'highway'})"
    )


def _map_priority_to_alert_level(priority_level: str) -> str:
    """Map INTERCEPT priority to mobile alert level."""
    mapping = {
        "high": "CRITICAL",
        "medium": "MEDIUM", 
        "low": "LOW"
    }
    return mapping.get(priority_level, "MEDIUM")


def _get_vibration_pattern(priority_level: str) -> List[int]:
    """Get vibration pattern based on priority."""
    patterns = {
        "high": [0, 500, 200, 500, 200, 500, 200, 500],  # Critical: persistent pattern
        "medium": [0, 300, 100, 300],  # Medium: double pulse
        "low": [0, 100]  # Low: single short pulse
    }
    return patterns.get(priority_level, [0, 300, 100, 300])


def _get_sound_type(priority_level: str) -> str:
    """Get sound type based on priority."""
    sound_mapping = {
        "high": "ALARM",      # High priority: alarm sound
        "medium": "NOTIFICATION",  # Medium: notification sound
        "low": "NOTIFICATION"      # Low: notification sound
    }
    return sound_mapping.get(priority_level, "NOTIFICATION")


async def get_intercept_alerts_by_location(
    db: AsyncSession,
    user,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 50.0,
    hours: int = 24
) -> List[dict]:
    """
    Get INTERCEPT alerts within a geographic area.
    
    Used by Web Intelligence for location-based alert filtering.
    """
    if not latitude or not longitude:
        return []
    
    # Get recent intercept events
    start_time = datetime.utcnow() - timedelta(hours=hours)
    point = ST_Point(longitude, latitude, srid=4326)
    radius_meters = radius_km * 1000
    
    query = (
        select(
            InterceptEvent,
            VehicleObservation.plate_number,
            VehicleObservation.location,
            ST_Distance(
                VehicleObservation.location,
                point
            ).label("distance_meters")
        )
        .join(VehicleObservation, VehicleObservation.id == InterceptEvent.observation_id)
        .where(
            and_(
                InterceptEvent.created_at >= start_time,
                ST_DWithin(VehicleObservation.location, point, radius_meters),
                InterceptEvent.recommendation.in_(["APPROACH", "MONITOR"])
            )
        )
        .order_by(desc("distance_meters"))
    )
    
    # Apply agency filter for non-admin users
    if user.role != UserRole.ADMIN:
        query = query.where(VehicleObservation.agency_id == user.agency_id)
    
    result = await db.execute(query)
    alerts = []
    
    for row in result:
        obs_point = to_shape(row.location)
        alerts.append({
            "intercept_event_id": str(row.InterceptEvent.id),
            "plate_number": row.plate_number,
            "location": {
                "latitude": float(obs_point.y),
                "longitude": float(obs_point.x)
            },
            "distance_km": float(row.distance_meters) / 1000,
            "intercept_score": row.InterceptEvent.intercept_score,
            "recommendation": row.InterceptEvent.recommendation,
            "priority_level": row.InterceptEvent.priority_level,
            "created_at": row.InterceptEvent.created_at.isoformat()
        })
    
    return alerts
