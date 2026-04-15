"""
F.A.R.O. Intelligence Schemas - Review and feedback workflows
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.db.base import ReviewStatus, SuspicionLevel, SuspicionReason, UrgencyLevel
from app.schemas.common import GeolocationPoint


class IntelligenceReviewBase(BaseModel):
    """Base intelligence review data."""
    model_config = ConfigDict(from_attributes=True)
    
    status: ReviewStatus
    justification: str = Field(..., min_length=10, max_length=5000)


class IntelligenceReviewCreate(IntelligenceReviewBase):
    """Schema for creating an intelligence review."""
    observation_id: UUID
    
    # Optional reclassification
    reclassified_reason: Optional[SuspicionReason] = None
    reclassified_level: Optional[SuspicionLevel] = None
    reclassified_urgency: Optional[UrgencyLevel] = None
    
    # Optional occurrence link
    occurrence_number: Optional[str] = Field(None, max_length=50)
    occurrence_url: Optional[str] = Field(None, max_length=500)
    
    # Generate feedback to field agent
    send_feedback: bool = True
    feedback_title: Optional[str] = Field(None, max_length=255)
    feedback_message: Optional[str] = Field(None, max_length=2000)
    recommended_action: Optional[str] = Field(None, max_length=255)


class IntelligenceReviewResponse(IntelligenceReviewBase):
    """Schema for intelligence review response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    observation_id: UUID
    reviewer_id: UUID
    reviewer_name: str
    reviewed_at: datetime
    
    reclassified_reason: Optional[SuspicionReason] = None
    reclassified_level: Optional[SuspicionLevel] = None
    reclassified_urgency: Optional[UrgencyLevel] = None
    
    occurrence_number: Optional[str] = None
    occurrence_url: Optional[str] = None


class IntelligenceQueueItem(BaseModel):
    """Item in intelligence triage queue."""
    model_config = ConfigDict(from_attributes=True)
    
    observation_id: UUID
    plate_number: str
    observed_at: datetime
    location: GeolocationPoint
    agent_name: str
    unit_name: Optional[str] = None
    
    suspicion_reason: SuspicionReason
    suspicion_level: SuspicionLevel
    urgency: UrgencyLevel
    suspicion_notes: Optional[str] = None
    
    previous_observations_count: int = 0
    is_monitored: bool = False
    has_image: bool = False
    score_value: Optional[float] = None
    score_label: Optional[str] = None
    priority_source: Optional[str] = None
    
    added_to_queue_at: datetime


class IntelligenceQueueFilter(BaseModel):
    """Filter for intelligence queue."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: Optional[str] = None
    suspicion_level: Optional[SuspicionLevel] = None
    urgency: Optional[UrgencyLevel] = None
    reason: Optional[SuspicionReason] = None
    agent_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    status: Optional[ReviewStatus] = Field(default=ReviewStatus.PENDING)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class FeedbackEventBase(BaseModel):
    """Base feedback event data."""
    model_config = ConfigDict(from_attributes=True)
    
    feedback_type: str = Field(..., max_length=50)  # "confirmation", "guidance", "alert"
    title: str = Field(..., max_length=255)
    message: str = Field(..., max_length=2000)
    recommended_action: Optional[str] = Field(None, max_length=255)


class FeedbackEventCreate(FeedbackEventBase):
    """Schema for creating a feedback event."""
    review_id: UUID
    target_agent_id: UUID


class FeedbackEventResponse(FeedbackEventBase):
    """Schema for feedback event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    review_id: UUID
    target_agent_id: UUID
    target_agent_name: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_read: bool = False


class FeedbackForAgent(BaseModel):
    """Feedback formatted for field agent display."""
    model_config = ConfigDict(from_attributes=True)
    
    feedback_id: UUID
    observation_id: UUID
    plate_number: str
    feedback_type: str
    title: str
    message: str
    recommended_action: Optional[str] = None
    sent_at: datetime
    is_read: bool
    read_at: Optional[datetime] = None
    reviewer_name: str


class MarkFeedbackReadRequest(BaseModel):
    """Request to mark feedback as read."""
    feedback_id: Optional[UUID] = None
    read_at: datetime = Field(default_factory=datetime.utcnow)
