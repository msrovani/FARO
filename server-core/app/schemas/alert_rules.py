"""
Alert Rule Schemas - Pydantic models for alert rule management.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AlertRuleTypeEnum(str, Enum):
    """Tipos de regras de alerta disponíveis."""
    WATCHLIST_MATCH = "watchlist_match"
    SUSPICIOUS_ROUTE = "suspicious_route"
    HOTSPOT_ZONE = "hotspot_zone"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    CONVOY_DETECTION = "convoy_detection"
    ROAMING_DETECTION = "roaming_detection"
    SENSITIVE_ASSET = "sensitive_asset"
    CUSTOM = "custom"


class AlertRuleSeverityEnum(str, Enum):
    """Níveis de severidade para regras de alerta."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertRuleBase(BaseModel):
    """Base schema for alert rules."""
    name: str = Field(..., min_length=1, max_length=255, description="Nome da regra")
    description: Optional[str] = Field(None, description="Descrição da regra")
    rule_type: AlertRuleTypeEnum = Field(..., description="Tipo de regra")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condições da regra em JSON")
    severity: AlertRuleSeverityEnum = Field(default=AlertRuleSeverityEnum.MEDIUM, description="Severidade da regra")
    is_active: bool = Field(default=True, description="Se a regra está ativa")
    priority: int = Field(default=0, ge=0, description="Prioridade de execução")


class AlertRuleCreate(AlertRuleBase):
    """Schema for creating a new alert rule."""
    pass


class AlertRuleUpdate(BaseModel):
    """Schema for updating an existing alert rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    severity: Optional[AlertRuleSeverityEnum] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


class AlertRuleResponse(AlertRuleBase):
    """Schema for alert rule response."""
    id: UUID
    agency_id: Optional[str]
    created_by: UUID
    times_triggered: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AlertRuleListResponse(BaseModel):
    """Schema for list of alert rules."""
    total: int
    rules: list[AlertRuleResponse]


class AlertRuleStatsResponse(BaseModel):
    """Schema for alert rule statistics."""
    total_rules: int
    active_rules: int
    inactive_rules: int
    rules_by_type: Dict[str, int]
    rules_by_severity: Dict[str, int]
    most_triggered: list[dict]
