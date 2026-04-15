"""
F.A.R.O. Alert Schemas - Alert engine and rules
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.db.base import AlertSeverity, AlertType


class AlertBase(BaseModel):
    """Base alert data."""
    model_config = ConfigDict(from_attributes=True)
    
    alert_type: AlertType
    severity: AlertSeverity
    title: str = Field(..., max_length=255)
    description: str
    context_data: Optional[Dict[str, Any]] = None


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    observation_id: Optional[UUID] = None
    suspicion_report_id: Optional[UUID] = None
    triggered_by_rule_id: Optional[UUID] = None
    triggered_manually_by: Optional[UUID] = None


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert."""
    acknowledged_by: UUID
    acknowledged_at: datetime = Field(default_factory=datetime.utcnow)


class AlertResponse(AlertBase):
    """Schema for alert response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    
    observation_id: Optional[UUID] = None
    suspicion_report_id: Optional[UUID] = None
    plate_number: Optional[str] = None
    
    is_acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    acknowledged_by_name: Optional[str] = None


class AlertRuleBase(BaseModel):
    """Base alert rule data."""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., max_length=255)
    description: str
    conditions: Dict[str, Any]  # JSON-based flexible conditions
    alert_type: AlertType
    severity: AlertSeverity
    priority: int = Field(default=100, ge=1, le=1000)


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating an alert rule."""
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    """Schema for alert rule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    created_by: UUID
    created_by_name: str
    trigger_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AlertFilter(BaseModel):
    """Filter parameters for alerts."""
    model_config = ConfigDict(from_attributes=True)
    
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    is_acknowledged: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    plate_number: Optional[str] = None


class AlertStats(BaseModel):
    """Alert statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_alerts: int
    critical_count: int
    warning_count: int
    info_count: int
    unacknowledged_count: int
    acknowledged_count: int
    by_type: Dict[str, int]
    by_day: List[Dict[str, Any]]
