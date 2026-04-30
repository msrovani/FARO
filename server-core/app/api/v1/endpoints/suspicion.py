"""
F.A.R.O. Suspicion API - Unified suspicion management endpoints
Handles capture, approach, feedback, and history for vehicle suspicions
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from uuid import UUID

from app.services.unified_suspicion_service import (
    UnifiedSuspicionService,
    SuspicionReason,
    SuspicionLevel,
    UrgencyLevel,
    SuspicionStatus,
    IncidentType
)
from app.services.unified_suspicion_service import unified_suspicion_service
from app.db.base import User
from app.api.v1.deps import require_field_agent, require_intelligence_analyst, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models
class SuspicionCaptureRequest(BaseModel):
    """Request model for capturing suspicion."""
    observation_id: str = Field(..., description="Vehicle observation ID")
    reason: SuspicionReason = Field(..., description="Suspicion reason")
    level: SuspicionLevel = Field(..., description="Suspicion level")
    urgency: UrgencyLevel = Field(..., description="Urgency level")
    notes: Optional[str] = Field(None, description="Agent notes")
    evidence_urls: Optional[List[str]] = Field(None, description="Evidence URLs")


class SuspicionApproachRequest(BaseModel):
    """Request model for confirming approach."""
    suspicion_id: str = Field(..., description="Suspicion report ID")
    confirmed_suspicion: bool = Field(..., description="Whether suspicion was confirmed")
    approach_level: int = Field(..., ge=0, le=100, description="Approach confidence level (0-100)")
    has_incident: bool = Field(False, description="Whether incident occurred")
    incident_type: Optional[IncidentType] = Field(None, description="Type of incident")
    notes: Optional[str] = Field(None, description="Approach notes")
    evidence_urls: Optional[List[str]] = Field(None, description="Evidence from approach")


class SuspicionFeedbackRequest(BaseModel):
    """Request model for adding feedback."""
    suspicion_id: str = Field(..., description="Suspicion report ID")
    feedback_type: str = Field(..., description="Type of feedback")
    feedback_content: str = Field(..., description="Feedback content")
    priority_adjustment: Optional[int] = Field(None, ge=-100, le=100, description="Priority adjustment")


class SuspicionResponse(BaseModel):
    """Response model for suspicion data."""
    id: str
    observation_id: str
    agent_id: str
    initial_reason: str
    initial_level: str
    initial_urgency: str
    initial_notes: Optional[str]
    was_approached: bool
    approach_confirmed_suspicion: bool
    approach_level: int
    approach_notes: Optional[str]
    has_incident: bool
    incident_type: Optional[str]
    status: str
    priority: int
    created_at: str
    updated_at: str
    approached_at: Optional[str]


class SuspicionContextResponse(BaseModel):
    """Response model for suspicion context."""
    current_suspicion: Optional[SuspicionResponse]
    suspicion_history: List[Dict[str, Any]]
    agent_feedback: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    plate_number: str
    generated_at: str


class SuspicionHistoryResponse(BaseModel):
    """Response model for suspicion history."""
    plate_number: str
    total_suspicions: int
    confirmed_suspicions: int
    false_positives: int
    history: List[SuspicionResponse]


@router.post("/capture", response_model=SuspicionResponse)
async def capture_suspicion(
    request: SuspicionCaptureRequest,
    current_user: User = Depends(require_field_agent),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Capture initial suspicion from field agent.
    
    Args:
        request: Suspicion capture data
        current_user: Authenticated field agent
        service: Unified suspicion service
        
    Returns:
        SuspicionResponse: Created suspicion report
    """
    try:
        suspicion = await service.capture_suspicion(
            db=None,  # Will be injected by dependency
            observation_id=request.observation_id,
            agent_id=str(current_user.id),
            reason=request.reason,
            level=request.level,
            urgency=request.urgency,
            notes=request.notes,
            evidence_urls=request.evidence_urls
        )
        
        return SuspicionResponse(
            id=suspicion.id,
            observation_id=suspicion.observation_id,
            agent_id=suspicion.agent_id,
            initial_reason=suspicion.initial_reason.value,
            initial_level=suspicion.initial_level.value,
            initial_urgency=suspicion.initial_urgency.value,
            initial_notes=suspicion.initial_notes,
            was_approached=suspicion.was_approached,
            approach_confirmed_suspicion=suspicion.approach_confirmed_suspicion,
            approach_level=suspicion.approach_level,
            approach_notes=suspicion.approach_notes,
            has_incident=suspicion.has_incident,
            incident_type=suspicion.incident_type.value if suspicion.incident_type else None,
            status=suspicion.status.value,
            priority=suspicion.priority,
            created_at=suspicion.created_at.isoformat(),
            updated_at=suspicion.updated_at.isoformat(),
            approached_at=suspicion.approached_at.isoformat() if suspicion.approached_at else None
        )
        
    except Exception as e:
        logger.error(f"Failed to capture suspicion: {e}")
        raise HTTPException(status_code=500, detail=f"Capture failed: {str(e)}")


@router.post("/approach", response_model=SuspicionResponse)
async def confirm_approach(
    request: SuspicionApproachRequest,
    current_user: User = Depends(require_field_agent),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Confirm vehicle approach with detailed feedback.
    
    Args:
        request: Approach confirmation data
        current_user: Authenticated field agent
        service: Unified suspicion service
        
    Returns:
        SuspicionResponse: Updated suspicion report
    """
    try:
        suspicion = await service.confirm_approach(
            db=None,  # Will be injected by dependency
            suspicion_id=request.suspicion_id,
            agent_id=str(current_user.id),
            confirmed_suspicion=request.confirmed_suspicion,
            approach_level=request.approach_level,
            has_incident=request.has_incident,
            incident_type=request.incident_type,
            notes=request.notes,
            evidence_urls=request.evidence_urls
        )
        
        return SuspicionResponse(
            id=suspicion.id,
            observation_id=suspicion.observation_id,
            agent_id=suspicion.agent_id,
            initial_reason=suspicion.initial_reason.value,
            initial_level=suspicion.initial_level.value,
            initial_urgency=suspicion.initial_urgency.value,
            initial_notes=suspicion.initial_notes,
            was_approached=suspicion.was_approached,
            approach_confirmed_suspicion=suspicion.approach_confirmed_suspicion,
            approach_level=suspicion.approach_level,
            approach_notes=suspicion.approach_notes,
            has_incident=suspicion.has_incident,
            incident_type=suspicion.incident_type.value if suspicion.incident_type else None,
            status=suspicion.status.value,
            priority=suspicion.priority,
            created_at=suspicion.created_at.isoformat(),
            updated_at=suspicion.updated_at.isoformat(),
            approached_at=suspicion.approached_at.isoformat() if suspicion.approached_at else None
        )
        
    except Exception as e:
        logger.error(f"Failed to confirm approach: {e}")
        raise HTTPException(status_code=500, detail=f"Approach confirmation failed: {str(e)}")


@router.post("/feedback", response_model=SuspicionResponse)
async def add_feedback(
    request: SuspicionFeedbackRequest,
    current_user: User = Depends(require_intelligence_analyst),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Add analyst feedback to suspicion report.
    
    Args:
        request: Feedback data
        current_user: Authenticated intelligence analyst
        service: Unified suspicion service
        
    Returns:
        SuspicionResponse: Updated suspicion report
    """
    try:
        suspicion = await service.add_feedback(
            db=None,  # Will be injected by dependency
            suspicion_id=request.suspicion_id,
            analyst_id=str(current_user.id),
            feedback_type=request.feedback_type,
            feedback_content=request.feedback_content,
            priority_adjustment=request.priority_adjustment
        )
        
        return SuspicionResponse(
            id=suspicion.id,
            observation_id=suspicion.observation_id,
            agent_id=suspicion.agent_id,
            initial_reason=suspicion.initial_reason.value,
            initial_level=suspicion.initial_level.value,
            initial_urgency=suspicion.initial_urgency.value,
            initial_notes=suspicion.initial_notes,
            was_approached=suspicion.was_approached,
            approach_confirmed_suspicion=suspicion.approach_confirmed_suspicion,
            approach_level=suspicion.approach_level,
            approach_notes=suspicion.approach_notes,
            has_incident=suspicion.has_incident,
            incident_type=suspicion.incident_type.value if suspicion.incident_type else None,
            status=suspicion.status.value,
            priority=suspicion.priority,
            created_at=suspicion.created_at.isoformat(),
            updated_at=suspicion.updated_at.isoformat(),
            approached_at=suspicion.approached_at.isoformat() if suspicion.approached_at else None
        )
        
    except Exception as e:
        logger.error(f"Failed to add feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback addition failed: {str(e)}")


@router.get("/context/{observation_id}", response_model=SuspicionContextResponse)
async def get_suspicion_context(
    observation_id: str,
    current_user: User = Depends(get_current_user),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Get complete context for approaching a vehicle.
    
    Args:
        observation_id: Vehicle observation ID
        current_user: Authenticated user
        service: Unified suspicion service
        
    Returns:
        SuspicionContextResponse: Complete suspicion context
    """
    try:
        context = await service.get_suspicion_context(
            db=None,  # Will be injected by dependency
            observation_id=observation_id,
            agent_id=str(current_user.id)
        )
        
        return SuspicionContextResponse(**context)
        
    except Exception as e:
        logger.error(f"Failed to get suspicion context: {e}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.get("/history/{plate_number}", response_model=SuspicionHistoryResponse)
async def get_suspicion_history(
    plate_number: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records"),
    current_user: User = Depends(get_current_user),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Get complete suspicion history for a plate.
    
    Args:
        plate_number: Vehicle plate number
        limit: Maximum number of records
        current_user: Authenticated user
        service: Unified suspicion service
        
    Returns:
        SuspicionHistoryResponse: Suspicion history
    """
    try:
        history = await service.get_suspicion_history(
            db=None,  # Will be injected by dependency
            plate_number=plate_number,
            limit=limit
        )
        
        # Calculate statistics
        total_suspicions = len(history)
        confirmed_suspicions = sum(1 for h in history if h.approach_confirmed_suspicion)
        false_positives = sum(1 for h in history if h.was_approached and not h.approach_confirmed_suspicion)
        
        # Convert to response format
        history_responses = [
            SuspicionResponse(
                id=h.id,
                observation_id=h.observation_id,
                agent_id=h.agent_id,
                initial_reason=h.initial_reason.value,
                initial_level=h.initial_level.value,
                initial_urgency=h.initial_urgency.value,
                initial_notes=h.initial_notes,
                was_approached=h.was_approached,
                approach_confirmed_suspicion=h.approach_confirmed_suspicion,
                approach_level=h.approach_level,
                approach_notes=h.approach_notes,
                has_incident=h.has_incident,
                incident_type=h.incident_type.value if h.incident_type else None,
                status=h.status.value,
                priority=h.priority,
                created_at=h.created_at.isoformat(),
                updated_at=h.updated_at.isoformat(),
                approached_at=h.approached_at.isoformat() if h.approached_at else None
            )
            for h in history
        ]
        
        return SuspicionHistoryResponse(
            plate_number=plate_number,
            total_suspicions=total_suspicions,
            confirmed_suspicions=confirmed_suspicions,
            false_positives=false_positives,
            history=history_responses
        )
        
    except Exception as e:
        logger.error(f"Failed to get suspicion history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/suspicion/{suspicion_id}", response_model=SuspicionResponse)
async def get_suspicion(
    suspicion_id: str,
    current_user: User = Depends(get_current_user),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Get suspicion details by ID.
    
    Args:
        suspicion_id: Suspicion report ID
        current_user: Authenticated user
        service: Unified suspicion service
        
    Returns:
        SuspicionResponse: Suspicion details
    """
    try:
        suspicion = await service._get_suspicion(
            db=None,  # Will be injected by dependency
            suspicion_id=suspicion_id
        )
        
        if not suspicion:
            raise HTTPException(status_code=404, detail="Suspicion not found")
        
        return SuspicionResponse(
            id=suspicion.id,
            observation_id=suspicion.observation_id,
            agent_id=suspicion.agent_id,
            initial_reason=suspicion.initial_reason.value,
            initial_level=suspicion.initial_level.value,
            initial_urgency=suspicion.initial_urgency.value,
            initial_notes=suspicion.initial_notes,
            was_approached=suspicion.was_approached,
            approach_confirmed_suspicion=suspicion.approach_confirmed_suspicion,
            approach_level=suspicion.approach_level,
            approach_notes=suspicion.approach_notes,
            has_incident=suspicion.has_incident,
            incident_type=suspicion.incident_type.value if suspicion.incident_type else None,
            status=suspicion.status.value,
            priority=suspicion.priority,
            created_at=suspicion.created_at.isoformat(),
            updated_at=suspicion.updated_at.isoformat(),
            approached_at=suspicion.approached_at.isoformat() if suspicion.approached_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suspicion: {e}")
        raise HTTPException(status_code=500, detail=f"Suspicion retrieval failed: {str(e)}")


@router.get("/queue")
async def get_suspicion_queue(
    status: Optional[SuspicionStatus] = Query(None, description="Filter by status"),
    priority_min: Optional[int] = Query(None, ge=0, le=100, description="Minimum priority"),
    priority_max: Optional[int] = Query(None, ge=0, le=100, description="Maximum priority"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    current_user: User = Depends(require_intelligence_analyst),
    service: UnifiedSuspicionService = Depends(lambda: unified_suspicion_service)
):
    """
    Get suspicion queue for intelligence analysis.
    
    Args:
        status: Filter by suspicion status
        priority_min: Minimum priority filter
        priority_max: Maximum priority filter
        limit: Maximum number of records
        current_user: Authenticated intelligence analyst
        service: Unified suspicion service
        
    Returns:
        List[SuspicionResponse]: Suspicion queue
    """
    try:
        # This would be implemented in the service
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Failed to get suspicion queue: {e}")
        raise HTTPException(status_code=500, detail=f"Queue retrieval failed: {str(e)}")


@router.get("/reasons")
async def get_suspicion_reasons():
    """
    Get available suspicion reasons.
    
    Returns:
        List[Dict]: Available suspicion reasons
    """
    return [
        {"value": reason.value, "label": reason.value.replace("_", " ").title()}
        for reason in SuspicionReason
    ]


@router.get("/levels")
async def get_suspicion_levels():
    """
    Get available suspicion levels.
    
    Returns:
        List[Dict]: Available suspicion levels
    """
    return [
        {"value": level.value, "label": level.value.title()}
        for level in SuspicionLevel
    ]


@router.get("/urgencies")
async def get_urgency_levels():
    """
    Get available urgency levels.
    
    Returns:
        List[Dict]: Available urgency levels
    """
    return [
        {"value": urgency.value, "label": urgency.value.title()}
        for urgency in UrgencyLevel
    ]


@router.get("/incident-types")
async def get_incident_types():
    """
    Get available incident types.
    
    Returns:
        List[Dict]: Available incident types
    """
    return [
        {"value": incident.value, "label": incident.value.replace("_", " ").title()}
        for incident in IncidentType
    ]


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "unified-suspicion-service",
        "version": "1.0.0"
    }
