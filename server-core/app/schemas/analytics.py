"""
F.A.R.O. Analytics Schemas - algoritmos, casos, reviews e feedback.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.base import (
    AlgorithmDecision,
    AlgorithmType,
    AnalystConclusion,
    AnalystDecision,
    AnalystReviewStatus,
    CaseStatus,
)
from app.schemas.observation import VehicleObservationResponse


class AlgorithmResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    algorithm_type: AlgorithmType
    observation_id: Optional[UUID] = None
    plate_number: Optional[str] = None
    decision: AlgorithmDecision
    confidence: float
    severity: str
    explanation: str
    false_positive_risk: str
    metrics: Dict[str, Any] = {}
    created_at: datetime


class SuspicionScoreFactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    factor_name: str
    factor_source: str
    weight: float
    contribution: float
    explanation: str
    direction: str


class SuspicionScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: UUID
    plate_number: str
    final_score: float
    final_label: AlgorithmDecision
    confidence: float
    severity: str
    explanation: str
    false_positive_risk: str
    factors: List[SuspicionScoreFactorResponse] = []
    created_at: datetime


class QueueScoreSummary(BaseModel):
    final_score: float
    final_label: AlgorithmDecision
    severity: str


class IntelligenceCaseCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    hypothesis: Optional[str] = None
    summary: Optional[str] = None
    status: CaseStatus = CaseStatus.OPEN
    sensitivity_level: str = Field(default="reserved", max_length=50)
    priority: int = Field(default=50, ge=1, le=100)
    review_due_at: Optional[datetime] = None


class IntelligenceCaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    hypothesis: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[CaseStatus] = None
    sensitivity_level: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    review_due_at: Optional[datetime] = None


class IntelligenceCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    hypothesis: Optional[str] = None
    summary: Optional[str] = None
    status: CaseStatus
    sensitivity_level: str
    priority: int
    review_due_at: Optional[datetime] = None
    created_by: UUID
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalystReviewCreateRequest(BaseModel):
    observation_id: UUID
    status: AnalystReviewStatus = AnalystReviewStatus.DRAFT
    conclusion: Optional[AnalystConclusion] = None
    decision: Optional[AnalystDecision] = None
    source_quality: Optional[str] = None
    data_reliability: Optional[str] = None
    reinforcing_factors: Dict[str, Any] = {}
    weakening_factors: Dict[str, Any] = {}
    recommendation: Optional[str] = None
    justification: str = Field(..., min_length=10)
    sensitivity_level: str = Field(default="reserved", max_length=50)
    review_due_at: Optional[datetime] = None
    linked_case_id: Optional[UUID] = None
    linked_occurrence_ref: Optional[str] = None
    change_reason: Optional[str] = None


class AnalystReviewUpdateRequest(BaseModel):
    status: Optional[AnalystReviewStatus] = None
    conclusion: Optional[AnalystConclusion] = None
    decision: Optional[AnalystDecision] = None
    source_quality: Optional[str] = None
    data_reliability: Optional[str] = None
    reinforcing_factors: Optional[Dict[str, Any]] = None
    weakening_factors: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    justification: Optional[str] = Field(None, min_length=10)
    sensitivity_level: Optional[str] = None
    review_due_at: Optional[datetime] = None
    linked_case_id: Optional[UUID] = None
    linked_occurrence_ref: Optional[str] = None
    change_reason: Optional[str] = None


class AnalystReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: UUID
    analyst_id: UUID
    analyst_name: Optional[str] = None
    status: AnalystReviewStatus
    conclusion: Optional[AnalystConclusion] = None
    decision: Optional[AnalystDecision] = None
    source_quality: Optional[str] = None
    data_reliability: Optional[str] = None
    reinforcing_factors: Optional[Dict[str, Any]] = None
    weakening_factors: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    justification: str
    sensitivity_level: str
    review_due_at: Optional[datetime] = None
    linked_case_id: Optional[UUID] = None
    linked_occurrence_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AnalystFeedbackCreateRequest(BaseModel):
    observation_id: Optional[UUID] = None
    target_user_id: Optional[UUID] = None
    target_team_label: Optional[str] = None
    feedback_type: str = Field(..., max_length=50)
    sensitivity_level: str = Field(default="operational", max_length=50)
    title: str = Field(..., max_length=255)
    message: Optional[str] = Field(None, min_length=5, max_length=4000)
    template_id: Optional[UUID] = None


class AnalystFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    observation_id: Optional[UUID] = None
    analyst_id: UUID
    analyst_name: Optional[str] = None
    target_user_id: Optional[UUID] = None
    target_team_label: Optional[str] = None
    feedback_type: str
    sensitivity_level: str
    title: str
    message: str
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime


class AnalystFeedbackTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    feedback_type: str = Field(..., max_length=50)
    sensitivity_level: str = Field(default="operational", max_length=50)
    body_template: str = Field(..., min_length=5, max_length=4000)
    is_active: bool = True


class AnalystFeedbackTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID
    created_by_name: Optional[str] = None
    name: str
    feedback_type: str
    sensitivity_level: str
    body_template: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FeedbackRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipient_type: str
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    unit_id: Optional[UUID] = None
    unit_code: Optional[str] = None
    unit_name: Optional[str] = None
    target_team_label: Optional[str] = None
    label: str


class ObservationAnalyticDetailResponse(VehicleObservationResponse):
    algorithm_results: List[AlgorithmResultResponse] = []
    suspicion_score: Optional[SuspicionScoreResponse] = None
    analyst_reviews: List[AnalystReviewResponse] = []
    feedback_events: List[AnalystFeedbackResponse] = []


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = None
    justification: Optional[str] = None
    created_at: datetime
