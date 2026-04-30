"""
F.A.R.O. Field Agents API - Real-time location and status tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import to_shape
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.db.base import AgentLocationLog, User, UserRole, Agency
from app.schemas.common import GeolocationPoint
from app.schemas.user import AgentLocationResponse
from app.utils.cache import cached_query

logger = logging.getLogger(__name__)

router = APIRouter()


def require_intelligence_or_supervisor(current_user: User = Depends(get_current_user)) -> User:
    """Require intelligence role or supervisor to access agent locations."""
    if current_user.role not in {UserRole.INTELLIGENCE, UserRole.SUPERVISOR, UserRole.ADMIN}:
        raise HTTPException(
            status_code=403, 
            detail="Acesso de inteligência ou supervisor requerido"
        )
    return current_user


@router.get("/live-locations", response_model=List[dict])
async def get_live_agent_locations(
    agency_id: Optional[UUID] = Query(None, description="Filter by agency (admin only)"),
    on_duty_only: bool = Query(True, description="Show only agents currently on duty"),
    minutes_threshold: int = Query(30, description="Maximum minutes since last location update"),
    current_user: User = Depends(require_intelligence_or_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current live locations of all field agents.
    
    Returns agents with their last known location, status, and recent activity.
    """
    # Build base query
    query = (
        select(
            User.id,
            User.full_name,
            User.badge_number,
            User.email,
            User.role,
            User.is_on_duty,
            User.last_seen,
            User.last_known_location,
            User.agency_id,
            Agency.name.label("agency_name"),
        )
        .select_from(User)
        .join(Agency, User.agency_id == Agency.id)
        .where(User.role == UserRole.FIELD_AGENT)
    )
    
    # Apply filters based on user role
    if current_user.role == UserRole.ADMIN:
        if agency_id:
            query = query.where(User.agency_id == agency_id)
    else:
        # Non-admin users see only their agency
        query = query.where(User.agency_id == current_user.agency_id)
    
    if on_duty_only:
        query = query.where(User.is_on_duty == True)
    
    # Filter by recent activity
    time_threshold = datetime.utcnow() - timedelta(minutes=minutes_threshold)
    query = query.where(User.last_seen >= time_threshold)
    
    # Execute query
    result = await db.execute(query)
    agents = result.all()
    
    live_locations = []
    for agent in agents:
        if not agent.last_known_location:
            continue
            
        # Convert PostGIS point to lat/lng
        point = to_shape(agent.last_known_location)
        
        # Get recent location count (activity level)
        recent_count = await db.scalar(
            select(func.count(AgentLocationLog.id))
            .where(
                and_(
                    AgentLocationLog.agent_id == agent.id,
                    AgentLocationLog.recorded_at >= time_threshold
                )
            )
        )
        
        live_locations.append({
            "agent_id": str(agent.id),
            "full_name": agent.full_name,
            "badge_number": agent.badge_number,
            "email": agent.email,
            "agency_id": str(agent.agency_id),
            "agency_name": agent.agency_name,
            "is_on_duty": agent.is_on_duty,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
            "location": {
                "latitude": float(point.y),
                "longitude": float(point.x)
            },
            "status": _get_agent_status(agent, recent_count),
            "activity_level": recent_count or 0,
            "minutes_since_last_update": int((datetime.utcnow() - agent.last_seen).total_seconds() / 60) if agent.last_seen else None
        })
    
    return live_locations


@router.get("/{agent_id}/location-history", response_model=List[AgentLocationResponse])
async def get_agent_location_history(
    agent_id: UUID,
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),
    current_user: User = Depends(require_intelligence_or_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed location history for a specific agent.
    
    Returns chronological location points with connectivity and battery status.
    """
    # Verify agent exists and user has permission
    agent = await db.get(User, agent_id)
    if not agent or agent.role != UserRole.FIELD_AGENT:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Check agency permissions
    if current_user.role != UserRole.ADMIN and agent.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Sem permissão para visualizar este agente")
    
    # Get location history
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        select(AgentLocationLog)
        .where(
            and_(
                AgentLocationLog.agent_id == agent_id,
                AgentLocationLog.recorded_at >= start_time
            )
        )
        .order_by(desc(AgentLocationLog.recorded_at))
    )
    
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return [
        AgentLocationResponse(
            id=location.id,
            agent_id=location.agent_id,
            agent_name=agent.full_name,
            location={
                "latitude": float(to_shape(location.location).y),
                "longitude": float(to_shape(location.location).x)
            },
            recorded_at=location.recorded_at,
            connectivity_status=location.connectivity_status,
            battery_level=location.battery_level,
            agency_id=str(agent.agency_id)
        )
        for location in locations
    ]


@router.get("/coverage-map", response_model=dict)
async def get_agent_coverage_map(
    hours: int = Query(24, description="Hours of coverage analysis", ge=1, le=168),
    grid_size: float = Query(0.01, description="Grid size in degrees for coverage analysis", ge=0.001, le=0.1),
    current_user: User = Depends(require_intelligence_or_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate coverage heatmap data for agent movements.
    
    Returns grid-based coverage analysis showing areas with agent presence.
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Build query for agent locations in time window
    query = (
        select(AgentLocationLog.agent_id, AgentLocationLog.location)
        .join(User, User.id == AgentLocationLog.agent_id)
        .where(
            and_(
                User.role == UserRole.FIELD_AGENT,
                User.is_on_duty == True,
                AgentLocationLog.recorded_at >= start_time
            )
        )
    )
    
    # Apply agency filter
    if current_user.role != UserRole.ADMIN:
        query = query.where(User.agency_id == current_user.agency_id)
    
    result = await db.execute(query)
    locations = result.all()
    
    # Generate coverage grid
    coverage_grid = {}
    
    for agent_id, location in locations:
        point = to_shape(location)
        
        # Calculate grid cell
        lat_grid = int(point.y / grid_size) * grid_size
        lng_grid = int(point.x / grid_size) * grid_size
        grid_key = f"{lat_grid:.3f},{lng_grid:.3f}"
        
        if grid_key not in coverage_grid:
            coverage_grid[grid_key] = {
                "latitude": lat_grid,
                "longitude": lng_grid,
                "agent_count": 0,
                "location_count": 0,
                "agents": set()
            }
        
        coverage_grid[grid_key]["agent_count"] = len(coverage_grid[grid_key]["agents"])
        coverage_grid[grid_key]["agents"].add(str(agent_id))
        coverage_grid[grid_key]["location_count"] += 1
    
    # Convert sets to counts and prepare response
    coverage_data = []
    for grid_data in coverage_grid.values():
        coverage_data.append({
            "latitude": grid_data["latitude"],
            "longitude": grid_data["longitude"],
            "unique_agents": len(grid_data["agents"]),
            "total_locations": grid_data["location_count"],
            "intensity": grid_data["location_count"] / max(grid_data["agent_count"], 1)  # Average locations per agent
        })
    
    return {
        "grid_size": grid_size,
        "time_window_hours": hours,
        "coverage_points": coverage_data,
        "total_agents": len(set(str(loc[0]) for loc in locations)),
        "total_locations": len(locations),
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/movement-summary", response_model=dict)
async def get_agents_movement_summary(
    hours: int = Query(24, description="Hours of analysis", ge=1, le=168),
    current_user: User = Depends(require_intelligence_or_supervisor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get movement summary statistics for all agents.
    
    Returns metrics like total distance traveled, active agents, and coverage areas.
    """
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get basic agent stats
    agent_query = (
        select(
            func.count(User.id).label("total_agents"),
            func.sum(func.case((User.is_on_duty == True, 1), else_=0)).label("agents_on_duty"),
            func.count(func.nullif(User.last_known_location, None)).label("agents_with_location")
        )
        .where(User.role == UserRole.FIELD_AGENT)
    )
    
    # Apply agency filter
    if current_user.role != UserRole.ADMIN:
        agent_query = agent_query.where(User.agency_id == current_user.agency_id)
    
    agent_stats = await db.execute(agent_query).first()
    
    # Get location activity stats
    location_query = (
        select(
            func.count(AgentLocationLog.id).label("total_locations"),
            func.count(func.distinct(AgentLocationLog.agent_id)).label("active_agents"),
            func.avg(func.extract('epoch', AgentLocationLog.recorded_at)).label("avg_timestamp")
        )
        .join(User, User.id == AgentLocationLog.agent_id)
        .where(
            and_(
                User.role == UserRole.FIELD_AGENT,
                AgentLocationLog.recorded_at >= start_time
            )
        )
    )
    
    # Apply agency filter
    if current_user.role != UserRole.ADMIN:
        location_query = location_query.where(User.agency_id == current_user.agency_id)
    
    location_stats = await db.execute(location_query).first()
    
    return {
        "time_window_hours": hours,
        "agent_stats": {
            "total_agents": agent_stats.total_agents or 0,
            "agents_on_duty": agent_stats.agents_on_duty or 0,
            "agents_with_location": agent_stats.agents_with_location or 0
        },
        "activity_stats": {
            "total_locations": location_stats.total_locations or 0,
            "active_agents": location_stats.active_agents or 0,
            "avg_locations_per_agent": (
                (location_stats.total_locations or 0) / max(location_stats.active_agents or 1, 1)
            )
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def _get_agent_status(agent, recent_count: int) -> str:
    """Determine agent status based on location and activity."""
    if not agent.is_on_duty:
        return "off_duty"
    
    if not agent.last_seen:
        return "unknown"
    
    minutes_ago = (datetime.utcnow() - agent.last_seen).total_seconds() / 60
    
    if minutes_ago > 60:
        return "offline"
    elif minutes_ago > 15:
        return "inactive"
    elif recent_count > 10:
        return "highly_active"
    elif recent_count > 5:
        return "active"
    else:
        return "normal"
