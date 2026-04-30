"""
F.A.R.O. Unified Suspicion Service - Centralized suspicion processing pipeline
Handles capture, approach, feedback, and second approaches with unified data model
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import (
    VehicleObservation,
    SuspicionReport,
    User,
    Alert,
    AnalystFeedbackEvent,
    WatchlistEntry
)
from app.core.config import settings
from app.services.cache_service import cache_service
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


class SuspicionReason(str, Enum):
    """Unified suspicion reasons"""
    STOLEN_VEHICLE = "stolen_vehicle"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    WANTED_PLATE = "wanted_plate"
    UNUSUAL_HOURS = "unusual_hours"
    KNOWN_ASSOCIATE = "known_associate"
    DRUG_TRAFFICKING = "drug_trafficking"
    WEAPONS = "weapons"
    GANG_ACTIVITY = "gang_activity"
    OTHER = "other"


class SuspicionLevel(str, Enum):
    """Unified suspicion levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UrgencyLevel(str, Enum):
    """Unified urgency levels"""
    MONITOR = "monitor"
    INTELLIGENCE = "intelligence"
    APPROACH = "approach"


class SuspicionStatus(str, Enum):
    """Unified suspicion status"""
    PENDING_APPROACH = "pending_approach"
    APPROACHED = "approached"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class IncidentType(str, Enum):
    """Types of incidents during approach"""
    TRAFFIC_VIOLATION = "traffic_violation"
    ARREST = "arrest"
    WARNING = "warning"
    SEARCH = "search"
    CITATION = "citation"
    OTHER = "other"


@dataclass
class Evidence:
    """Evidence attached to suspicion"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "image"  # image, audio, document
    url: str = ""
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApproachHistory:
    """History of approaches for a vehicle"""
    agent_id: str
    agent_name: str
    approach_time: datetime
    confirmed_suspicion: bool
    approach_level: int  # 0-100
    has_incident: bool
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    incident_type: Optional[IncidentType] = None
    notes: str = ""
    evidence: List[Evidence] = field(default_factory=list)


@dataclass
class UnifiedSuspicionReport:
    """Unified suspicion model - single source of truth"""
    observation_id: str
    agent_id: str
    
    # Initial suspicion (capture)
    initial_reason: SuspicionReason
    initial_level: SuspicionLevel
    initial_urgency: UrgencyLevel
    
    # System metadata
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initial_notes: Optional[str] = None
    initial_evidence: List[Evidence] = field(default_factory=list)
    
    # Approach confirmation
    was_approached: bool = False
    approach_confirmed_suspicion: bool = False
    approach_level: int = 0  # 0-100 normalized
    approach_notes: Optional[str] = None
    approach_evidence: List[Evidence] = field(default_factory=list)
    
    # Incident details
    has_incident: bool = False
    incident_type: Optional[IncidentType] = None
    incident_report: Optional[str] = None
    
    # System metadata
    status: SuspicionStatus = SuspicionStatus.PENDING_APPROACH
    priority: int = 0  # 0-100 calculated
    previous_approaches: List[ApproachHistory] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    approached_at: Optional[datetime] = None


class UnifiedSuspicionService:
    """Unified suspicion processing service for F.A.R.O."""
    
    def __init__(self):
        self.cache_ttl = {
            "suspicion": 3600,      # 1 hour
            "approach": 86400,     # 24 hours
            "feedback": 604800,    # 7 days
            "history": 2592000     # 30 days
        }
    
    async def capture_suspicion(
        self,
        db: AsyncSession,
        observation_id: str,
        agent_id: str,
        reason: SuspicionReason,
        level: SuspicionLevel,
        urgency: UrgencyLevel,
        notes: Optional[str] = None,
        evidence_urls: Optional[List[str]] = None
    ) -> UnifiedSuspicionReport:
        """
        Capture initial suspicion from field agent.
        
        Args:
            db: Database session
            observation_id: Vehicle observation ID
            agent_id: Agent ID
            reason: Suspicion reason
            level: Suspicion level
            urgency: Urgency level
            notes: Agent notes
            evidence_urls: List of evidence URLs
            
        Returns:
            UnifiedSuspicionReport: Created suspicion report
        """
        try:
            # Create unified suspicion report
            suspicion = UnifiedSuspicionReport(
                observation_id=observation_id,
                agent_id=agent_id,
                initial_reason=reason,
                initial_level=level,
                initial_urgency=urgency,
                initial_notes=notes,
                initial_evidence=[
                    Evidence(type="image", url=url) 
                    for url in (evidence_urls or [])
                ]
            )
            
            # Calculate priority based on initial data
            suspicion.priority = self._calculate_priority(suspicion)
            
            # Save to database
            await self._save_suspicion(db, suspicion)
            
            # Generate alerts if needed
            if urgency == UrgencyLevel.APPPROACH:
                await self._generate_alert(db, suspicion)
            
            # Cache for quick access
            await self._cache_suspicion(suspicion)
            
            # Notify relevant agents
            await self._notify_suspicion_capture(suspicion)
            
            logger.info(f"Captured suspicion: {suspicion.id} for observation {observation_id}")
            
            return suspicion
            
        except Exception as e:
            logger.error(f"Failed to capture suspicion: {e}")
            raise
    
    async def confirm_approach(
        self,
        db: AsyncSession,
        suspicion_id: str,
        agent_id: str,
        confirmed_suspicion: bool,
        approach_level: int,
        has_incident: bool,
        incident_type: Optional[IncidentType] = None,
        notes: Optional[str] = None,
        evidence_urls: Optional[List[str]] = None
    ) -> UnifiedSuspicionReport:
        """
        Confirm vehicle approach with detailed feedback.
        
        Args:
            db: Database session
            suspicion_id: Suspicion report ID
            agent_id: Approaching agent ID
            confirmed_suspicion: Whether suspicion was confirmed
            approach_level: Approach confidence level (0-100)
            has_incident: Whether incident occurred
            incident_type: Type of incident
            notes: Approach notes
            evidence_urls: Evidence from approach
            
        Returns:
            UnifiedSuspicionReport: Updated suspicion report
        """
        try:
            # Get existing suspicion
            suspicion = await self._get_suspicion(db, suspicion_id)
            if not suspicion:
                raise ValueError(f"Suspicion {suspicion_id} not found")
            
            # Update approach data
            suspicion.was_approached = True
            suspicion.approach_confirmed_suspicion = confirmed_suspicion
            suspicion.approach_level = approach_level
            suspicion.has_incident = has_incident
            suspicion.incident_type = incident_type
            suspicion.approach_notes = notes
            suspicion.approach_evidence = [
                Evidence(type="image", url=url) 
                for url in (evidence_urls or [])
            ]
            suspicion.approached_at = datetime.utcnow()
            
            # Update status
            if confirmed_suspicion:
                suspicion.status = SuspicionStatus.CONFIRMED
                # Add to watchlist for future monitoring
                await self._add_to_watchlist(db, suspicion)
            else:
                suspicion.status = SuspicionStatus.FALSE_POSITIVE
            
            # Recalculate priority
            suspicion.priority = self._calculate_priority(suspicion)
            
            # Create approach history
            approach_history = ApproachHistory(
                agent_id=agent_id,
                agent_name=await self._get_agent_name(db, agent_id),
                approach_time=suspicion.approached_at,
                confirmed_suspicion=confirmed_suspicion,
                approach_level=approach_level,
                has_incident=has_incident,
                incident_type=incident_type,
                notes=notes or "",
                evidence=suspicion.approach_evidence
            )
            suspicion.previous_approaches.append(approach_history)
            
            # Save updates
            await self._save_suspicion(db, suspicion)
            
            # Generate feedback for original agent
            await self._generate_feedback(db, suspicion, agent_id)
            
            # Update cache
            await self._cache_suspicion(suspicion)
            
            # Notify relevant users
            await self._notify_approach_confirmation(suspicion)
            
            logger.info(f"Confirmed approach: {suspicion_id} by agent {agent_id}")
            
            return suspicion
            
        except Exception as e:
            logger.error(f"Failed to confirm approach: {e}")
            raise
    
    async def add_feedback(
        self,
        db: AsyncSession,
        suspicion_id: str,
        analyst_id: str,
        feedback_type: str,
        feedback_content: str,
        priority_adjustment: Optional[int] = None
    ) -> UnifiedSuspicionReport:
        """
        Add analyst feedback to suspicion report.
        
        Args:
            db: Database session
            suspicion_id: Suspicion report ID
            analyst_id: Analyst ID
            feedback_type: Type of feedback
            feedback_content: Feedback content
            priority_adjustment: Priority adjustment (-100 to 100)
            
        Returns:
            UnifiedSuspicionReport: Updated suspicion report
        """
        try:
            # Get existing suspicion
            suspicion = await self._get_suspicion(db, suspicion_id)
            if not suspicion:
                raise ValueError(f"Suspicion {suspicion_id} not found")
            
            # Create feedback event
            feedback = AnalystFeedbackEvent(
                id=str(uuid.uuid4()),
                observation_id=suspicion.observation_id,
                analyst_id=analyst_id,
                feedback_type=feedback_type,
                feedback_content=feedback_content,
                created_at=datetime.utcnow()
            )
            
            # Save feedback
            db.add(feedback)
            await db.commit()
            
            # Adjust priority if specified
            if priority_adjustment:
                suspicion.priority = max(0, min(100, suspicion.priority + priority_adjustment))
                await self._save_suspicion(db, suspicion)
            
            # Cache updated data
            await self._cache_suspicion(suspicion)
            
            # Notify relevant users
            await self._notify_feedback_added(suspicion, feedback)
            
            logger.info(f"Added feedback to suspicion: {suspicion_id} by analyst {analyst_id}")
            
            return suspicion
            
        except Exception as e:
            logger.error(f"Failed to add feedback: {e}")
            raise
    
    async def get_suspicion_context(
        self,
        db: AsyncSession,
        observation_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get complete context for approaching a vehicle.
        
        Args:
            db: Database session
            observation_id: Vehicle observation ID
            agent_id: Requesting agent ID
            
        Returns:
            Dict: Complete suspicion context
        """
        try:
            # Check cache first
            cache_key = f"suspicion_context:{observation_id}"
            cached_context = await cache_service.get(cache_key)
            if cached_context:
                return cached_context
            
            # Get current suspicion
            current_suspicion = await self._get_current_suspicion(db, observation_id)
            
            # Get suspicion history for this plate
            plate_number = await self._get_plate_number(db, observation_id)
            suspicion_history = await self._get_plate_suspicion_history(db, plate_number)
            
            # Get agent feedback
            agent_feedback = await self._get_agent_feedback(db, observation_id)
            
            # Calculate recommendations
            recommendations = await self._calculate_recommendations(
                current_suspicion, suspicion_history, agent_feedback
            )
            
            context = {
                "current_suspicion": current_suspicion.__dict__ if current_suspicion else None,
                "suspicion_history": [h.__dict__ for h in suspicion_history],
                "agent_feedback": [f.__dict__ for f in agent_feedback],
                "recommendations": recommendations,
                "plate_number": plate_number,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache context
            await cache_service.set(cache_key, context, ttl=self.cache_ttl["approach"])
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get suspicion context: {e}")
            raise
    
    async def get_suspicion_history(
        self,
        db: AsyncSession,
        plate_number: str,
        limit: int = 10
    ) -> List[UnifiedSuspicionReport]:
        """
        Get complete suspicion history for a plate.
        
        Args:
            db: Database session
            plate_number: Vehicle plate number
            limit: Maximum number of records
            
        Returns:
            List[UnifiedSuspicionReport]: Suspicion history
        """
        try:
            # Check cache
            cache_key = f"suspicion_history:{plate_number}:{limit}"
            cached_history = await cache_service.get(cache_key)
            if cached_history:
                return cached_history
            
            # Query database
            query = (
                select(VehicleObservation, SuspicionReport)
                .join(SuspicionReport, VehicleObservation.id == SuspicionReport.observation_id)
                .where(VehicleObservation.plate_number == plate_number)
                .order_by(desc(VehicleObservation.observed_at))
                .limit(limit)
            )
            
            result = await db.execute(query)
            history = []
            
            for observation, suspicion_report in result:
                # Convert to unified model
                unified = await self._convert_to_unified(suspicion_report, observation)
                history.append(unified)
            
            # Cache results
            await cache_service.set(cache_key, history, ttl=self.cache_ttl["history"])
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get suspicion history: {e}")
            raise
    
    def _calculate_priority(self, suspicion: UnifiedSuspicionReport) -> int:
        """Calculate suspicion priority based on multiple factors."""
        base_score = {
            SuspicionLevel.LOW: 20,
            SuspicionLevel.MEDIUM: 50,
            SuspicionLevel.HIGH: 80
        }[suspicion.initial_level]
        
        urgency_boost = {
            UrgencyLevel.MONITOR: 0,
            UrgencyLevel.INTELLIGENCE: 10,
            UrgencyLevel.APPPROACH: 20
        }[suspicion.initial_urgency]
        
        # Boost for high-risk reasons
        reason_boost = {
            SuspicionReason.STOLEN_VEHICLE: 15,
            SuspicionReason.WANTED_PLATE: 15,
            SuspicionReason.WEAPONS: 10,
            SuspicionReason.DRUG_TRAFFICKING: 10,
            SuspicionReason.GANG_ACTIVITY: 10
        }.get(suspicion.initial_reason, 0)
        
        # Boost for confirmed approaches
        if suspicion.approach_confirmed_suspicion:
            base_score += 20
        
        # Boost for incidents
        if suspicion.has_incident:
            base_score += 15
        
        # Boost for recurring suspicions
        if len(suspicion.previous_approaches) > 0:
            base_score += min(10, len(suspicion.previous_approaches) * 5)
        
        return min(100, base_score + urgency_boost + reason_boost)
    
    async def _save_suspicion(self, db: AsyncSession, suspicion: UnifiedSuspicionReport):
        """Save unified suspicion to database."""
        # Convert to SuspicionReport model
        db_suspicion = SuspicionReport(
            id=suspicion.id,
            observation_id=uuid.UUID(suspicion.observation_id),
            reason=suspicion.initial_reason.value,
            level=suspicion.initial_level.value,
            urgency=suspicion.initial_urgency.value,
            notes=suspicion.initial_notes,
            abordado=suspicion.was_approached,
            nivel_abordagem=suspicion.approach_level,
            texto_ocorrencia=suspicion.approach_notes,
            ocorrencia_registrada=suspicion.has_incident,
            created_at=suspicion.created_at,
            updated_at=suspicion.updated_at
        )
        
        db.add(db_suspicion)
        await db.commit()
    
    async def _get_suspicion(self, db: AsyncSession, suspicion_id: str) -> Optional[UnifiedSuspicionReport]:
        """Get suspicion by ID."""
        # Check cache first
        cache_key = f"suspicion:{suspicion_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached
        
        # Query database
        query = select(SuspicionReport).where(SuspicionReport.id == suspicion_id)
        result = await db.execute(query)
        db_suspicion = result.scalar_one_or_none()
        
        if not db_suspicion:
            return None
        
        # Convert to unified model
        unified = await self._convert_to_unified(db_suspicion)
        
        # Cache result
        await cache_service.set(cache_key, unified, ttl=self.cache_ttl["suspicion"])
        
        return unified
    
    async def _convert_to_unified(self, db_suspicion: SuspicionReport, observation: Optional[VehicleObservation] = None) -> UnifiedSuspicionReport:
        """Convert database model to unified model."""
        return UnifiedSuspicionReport(
            id=str(db_suspicion.id),
            observation_id=str(db_suspicion.observation_id),
            agent_id=str(observation.agent_id) if observation else "",
            initial_reason=SuspicionReason(db_suspicion.reason),
            initial_level=SuspicionLevel(db_suspicion.level),
            initial_urgency=UrgencyLevel(db_suspicion.urgency),
            initial_notes=db_suspicion.notes,
            was_approached=db_suspicion.abordado or False,
            approach_confirmed_suspicion=db_suspicion.abordado and (db_suspicion.nivel_abordagem or 0) > 50,
            approach_level=db_suspicion.nivel_abordagem or 0,
            approach_notes=db_suspicion.texto_ocorrencia,
            has_incident=db_suspicion.ocorrencia_registrada or False,
            status=SuspicionStatus.APPROACHED if db_suspicion.abordado else SuspicionStatus.PENDING_APPROACH,
            created_at=db_suspicion.created_at,
            updated_at=db_suspicion.updated_at,
            approached_at=db_suspicion.updated_at if db_suspicion.abordado else None
        )
    
    async def _generate_alert(self, db: AsyncSession, suspicion: UnifiedSuspicionReport):
        """Generate alert for high-priority suspicion."""
        if suspicion.priority < 70:
            return
        
        alert = Alert(
            id=str(uuid.uuid4()),
            suspicion_report_id=uuid.UUID(suspicion.id),
            alert_type="suspicion_approach",
            severity="high" if suspicion.priority >= 85 else "medium",
            title=f"High Priority Suspicion: {suspicion.initial_reason.value}",
            message=f"Vehicle requires immediate attention. Priority: {suspicion.priority}/100",
            created_at=datetime.utcnow()
        )
        
        db.add(alert)
        await db.commit()
    
    async def _notify_suspicion_capture(self, suspicion: UnifiedSuspicionReport):
        """Notify relevant agents about new suspicion."""
        await websocket_manager.broadcast_to_role(
            "intelligence",
            {
                "type": "suspicion_captured",
                "suspicion_id": suspicion.id,
                "observation_id": suspicion.observation_id,
                "priority": suspicion.priority,
                "reason": suspicion.initial_reason.value,
                "urgency": suspicion.initial_urgency.value
            }
        )
    
    async def _notify_approach_confirmation(self, suspicion: UnifiedSuspicionReport):
        """Notify about approach confirmation."""
        await websocket_manager.broadcast_to_role(
            "intelligence",
            {
                "type": "approach_confirmed",
                "suspicion_id": suspicion.id,
                "observation_id": suspicion.observation_id,
                "confirmed": suspicion.approach_confirmed_suspicion,
                "approach_level": suspicion.approach_level,
                "has_incident": suspicion.has_incident
            }
        )
    
    async def _notify_feedback_added(self, suspicion: UnifiedSuspicionReport, feedback: AnalystFeedbackEvent):
        """Notify about new feedback."""
        await websocket_manager.broadcast_to_user(
            suspicion.agent_id,
            {
                "type": "feedback_added",
                "suspicion_id": suspicion.id,
                "feedback_type": feedback.feedback_type,
                "feedback_content": feedback.feedback_content
            }
        )
    
    async def _cache_suspicion(self, suspicion: UnifiedSuspicionReport):
        """Cache suspicion data."""
        cache_key = f"suspicion:{suspicion.id}"
        await cache_service.set(cache_key, suspicion.__dict__, ttl=self.cache_ttl["suspicion"])
    
    async def _get_agent_name(self, db: AsyncSession, agent_id: str) -> str:
        """Get agent name from ID."""
        query = select(User.full_name).where(User.id == uuid.UUID(agent_id))
        result = await db.execute(query)
        return result.scalar() or "Unknown Agent"
    
    async def _get_plate_number(self, db: AsyncSession, observation_id: str) -> str:
        """Get plate number from observation ID."""
        query = select(VehicleObservation.plate_number).where(
            VehicleObservation.id == uuid.UUID(observation_id)
        )
        result = await db.execute(query)
        return result.scalar() or ""
    
    async def _get_current_suspicion(self, db: AsyncSession, observation_id: str) -> Optional[UnifiedSuspicionReport]:
        """Get current suspicion for observation."""
        query = select(SuspicionReport).where(
            SuspicionReport.observation_id == uuid.UUID(observation_id)
        )
        result = await db.execute(query)
        db_suspicion = result.scalar_one_or_none()
        
        if not db_suspicion:
            return None
        
        return await self._convert_to_unified(db_suspicion)
    
    async def _get_plate_suspicion_history(self, db: AsyncSession, plate_number: str) -> List[UnifiedSuspicionReport]:
        """Get suspicion history for plate."""
        # Implementation would query all suspicions for this plate
        return []
    
    async def _get_agent_feedback(self, db: AsyncSession, observation_id: str) -> List[AnalystFeedbackEvent]:
        """Get agent feedback for observation."""
        query = select(AnalystFeedbackEvent).where(
            AnalystFeedbackEvent.observation_id == uuid.UUID(observation_id)
        ).order_by(desc(AnalystFeedbackEvent.created_at))
        
        result = await db.execute(query)
        return list(result.scalars())
    
    async def _calculate_recommendations(
        self,
        current_suspicion: Optional[UnifiedSuspicionReport],
        history: List[UnifiedSuspicionReport],
        feedback: List[AnalystFeedbackEvent]
    ) -> List[Dict[str, Any]]:
        """Calculate approach recommendations."""
        recommendations = []
        
        if not current_suspicion:
            return recommendations
        
        # Base recommendation from current suspicion
        if current_suspicion.initial_urgency == UrgencyLevel.APPPROACH:
            recommendations.append({
                "type": "approach",
                "priority": "high",
                "reason": f"High urgency suspicion: {current_suspicion.initial_reason.value}",
                "confidence": current_suspicion.priority / 100
            })
        
        # Historical recommendations
        confirmed_count = sum(1 for h in history if h.approach_confirmed_suspicion)
        if confirmed_count > 0:
            recommendations.append({
                "type": "enhanced_scrutiny",
                "priority": "medium",
                "reason": f"Vehicle has {confirmed_count} confirmed suspicions in history",
                "confidence": min(0.9, confirmed_count * 0.3)
            })
        
        # Feedback-based recommendations
        negative_feedback = sum(1 for f in feedback if "false_positive" in f.feedback_content.lower())
        if negative_feedback > 0:
            recommendations.append({
                "type": "caution",
                "priority": "low",
                "reason": f"Previous false positive reports: {negative_feedback}",
                "confidence": negative_feedback * 0.2
            })
        
        return recommendations
    
    async def _add_to_watchlist(self, db: AsyncSession, suspicion: UnifiedSuspicionReport):
        """Add confirmed suspicion to watchlist."""
        plate_number = await self._get_plate_number(db, suspicion.observation_id)
        
        # Check if already in watchlist
        existing = await db.execute(
            select(WatchlistEntry).where(
                and_(
                    WatchlistEntry.plate_number == plate_number,
                    WatchlistEntry.is_active == True
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            watchlist = WatchlistEntry(
                id=str(uuid.uuid4()),
                plate_number=plate_number,
                reason=suspicion.initial_reason.value,
                priority=suspicion.priority,
                added_by=uuid.UUID(suspicion.agent_id),
                expires_at=datetime.utcnow() + timedelta(days=30),
                is_active=True
            )
            
            db.add(watchlist)
            await db.commit()


# Singleton instance
unified_suspicion_service = UnifiedSuspicionService()
