"""
F.A.R.O. Database - Base Model Configuration
SQLAlchemy 2.0 with PostGIS support
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    Index,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    declared_attr,
)
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    # Common columns for all tables
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# =============================================================================
# ENUM DEFINITIONS
# =============================================================================

from enum import Enum as PyEnum


class UserRole(str, PyEnum):
    FIELD_AGENT = "field_agent"
    INTELLIGENCE = "intelligence"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class AgencyType(str, PyEnum):
    """Agency hierarchy level for intelligence organization."""
    LOCAL = "local"  # Agência local de inteligência (batalhões/regimentos)
    REGIONAL = "regional"  # Agência regional (agrega agências locais)
    CENTRAL = "central"  # Agência central (estado inteiro)


class SuspicionLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UrgencyLevel(str, PyEnum):
    MONITOR = "monitor"
    INTELLIGENCE = "intelligence"
    APPROACH = "approach"


class SuspicionReason(str, PyEnum):
    STOLEN_VEHICLE = "stolen_vehicle"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    WANTED_PLATE = "wanted_plate"
    UNUSUAL_HOURS = "unusual_hours"
    KNOWN_ASSOCIATE = "known_associate"
    DRUG_TRAFFICKING = "drug_trafficking"
    WEAPONS = "weapons"
    GANG_ACTIVITY = "gang_activity"
    OTHER = "other"


class ReviewStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISCARDED = "discarded"
    MONITORING = "monitoring"


class AlertType(str, PyEnum):
    INSTANT = "instant"
    PATTERN = "pattern"
    RECURRENCE = "recurrence"
    CORRELATION = "correlation"


class AlertSeverity(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SyncStatus(str, PyEnum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class WatchlistStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CLOSED = "closed"


class WatchlistCategory(str, PyEnum):
    SUSPECT_VEHICLE = "suspect_vehicle"
    MONITORED_VEHICLE = "monitored_vehicle"
    CASE_RELATED = "case_related"
    POSSIBLE_CLONE = "possible_clone"
    PARTIAL_PLATE = "partial_plate"
    VISUAL_ONLY = "visual_only"


class AlgorithmType(str, PyEnum):
    WATCHLIST = "watchlist"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    ROUTE_ANOMALY = "route_anomaly"
    SENSITIVE_ZONE_RECURRENCE = "sensitive_zone_recurrence"
    CONVOY = "convoy"
    ROAMING = "roaming"
    COMPOSITE_SCORE = "composite_score"


class AlgorithmDecision(str, PyEnum):
    NO_MATCH = "no_match"
    WEAK_MATCH = "weak_match"
    RELEVANT_MATCH = "relevant_match"
    CRITICAL_MATCH = "critical_match"
    IMPOSSIBLE = "impossible"
    HIGHLY_IMPROBABLE = "highly_improbable"
    ANOMALOUS = "anomalous"
    DISCARDED = "discarded"
    NORMAL = "normal"
    SLIGHT_DEVIATION = "slight_deviation"
    RELEVANT_ANOMALY = "relevant_anomaly"
    STRONG_ANOMALY = "strong_anomaly"
    LOW_RECURRENCE = "low_recurrence"
    MEDIUM_RECURRENCE = "medium_recurrence"
    RELEVANT_RECURRENCE = "relevant_recurrence"
    MONITORING_RECOMMENDED = "monitoring_recommended"
    CASUAL = "casual"
    REPEATED = "repeated"
    PROBABLE_CONVOY = "probable_convoy"
    STRONG_CONVOY = "strong_convoy"
    NORMAL_CIRCULATION = "normal_circulation"
    LIGHT_ROAMING = "light_roaming"
    RELEVANT_ROAMING = "relevant_roaming"
    LIKELY_LOITERING = "likely_loitering"
    INFORMATIVE = "informative"
    MONITOR = "monitor"
    RELEVANT = "relevant"
    HIGH_RISK = "high_risk"
    CRITICAL = "critical"


class AlgorithmRunStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class CaseStatus(str, PyEnum):
    OPEN = "open"
    MONITORING = "monitoring"
    ESCALATED = "escalated"
    CLOSED = "closed"


class CaseLinkType(str, PyEnum):
    OBSERVATION = "observation"
    WATCHLIST = "watchlist"
    SCORE = "score"
    OCCURRENCE = "occurrence"
    VEHICLE = "vehicle"


class AnalystReviewStatus(str, PyEnum):
    DRAFT = "draft"
    FINAL = "final"
    RECTIFIED = "rectified"
    SUPERVISOR_REVIEW = "supervisor_review"


class AnalystConclusion(str, PyEnum):
    IMPROCEDENTE = "improcedente"
    FRACA = "fraca"
    MODERADA = "moderada"
    RELEVANTE = "relevante"
    CRITICA = "critica"


class AnalystDecision(str, PyEnum):
    DISCARDED = "discarded"
    IN_ANALYSIS = "in_analysis"
    CONFIRMED_MONITORING = "confirmed_monitoring"
    CONFIRMED_APPROACH = "confirmed_approach"
    LINKED_TO_CASE = "linked_to_case"
    ESCALATED = "escalated"


class CrimeType(str, PyEnum):
    DRUG_TRAFFICKING = "drug_trafficking"
    CONTRABAND = "contraband"
    ESCAPE = "escape"
    WEAPONS_TRAFFICKING = "weapons_trafficking"
    KIDNAPPING = "kidnapping"
    CAR_THEFT = "car_theft"
    STOLEN_VEHICLE = "stolen_vehicle"
    GANG_ACTIVITY = "gang_activity"
    HUMAN_TRAFFICKING = "human_trafficking"
    MONEY_LAUNDERING = "money_laundering"
    OTHER = "other"


class RouteDirection(str, PyEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class RiskLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# USER MODELS
# =============================================================================


class Agency(Base):
    """Tenant agency/organization boundary for multi-agency deployments."""

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Hierarchy fields
    type: Mapped[AgencyType] = mapped_column(
        Enum(AgencyType, name="agencytype", create_constraint=True),
        nullable=False,
        default=AgencyType.LOCAL,
    )
    parent_agency_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=True,
        index=True,
    )

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="agency")
    units: Mapped[List["Unit"]] = relationship(back_populates="agency")
    parent_agency: Mapped[Optional["Agency"]] = relationship(
        "Agency",
        remote_side="Agency.id",
        backref="child_agencies",
    )


class User(Base):
    """User account for agents and intelligence staff."""

    # CPF - Brazilian individual taxpayer registry (optional for external auth)
    cpf: Mapped[Optional[str]] = mapped_column(
        String(11), unique=True, nullable=True, index=True
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_number: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", create_constraint=True),
        nullable=False,
        default=UserRole.FIELD_AGENT,
    )

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )

    unit_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("unit.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    agency: Mapped["Agency"] = relationship(back_populates="users")
    unit: Mapped[Optional["Unit"]] = relationship(back_populates="users")
    observations: Mapped[List["VehicleObservation"]] = relationship(
        back_populates="agent"
    )
    devices: Mapped[List["Device"]] = relationship(back_populates="user")
    reviews: Mapped[List["IntelligenceReview"]] = relationship(
        back_populates="reviewer"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user")

    __table_args__ = (Index("ix_user_role_active", "role", "is_active"),)


class Unit(Base):
    """Police unit/department."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    agency: Mapped["Agency"] = relationship(back_populates="units")
    users: Mapped[List[User]] = relationship(back_populates="unit")

    __table_args__ = (
        UniqueConstraint("agency_id", "code", name="uq_unit_agency_code"),
    )


class Device(Base):
    """Registered mobile device for field agents."""

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_model: Mapped[str] = mapped_column(String(255), nullable=False)
    os_version: Mapped[str] = mapped_column(String(100), nullable=False)
    app_version: Mapped[str] = mapped_column(String(50), nullable=False)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped[User] = relationship(back_populates="devices")
    observations: Mapped[List["VehicleObservation"]] = relationship(
        back_populates="device"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_device_user_device_id"),
    )


# =============================================================================
# VEHICLE OBSERVATION MODELS
# =============================================================================


class VehicleObservation(Base):
    """Core vehicle observation record from field agents."""

    # Client-generated ID for idempotency (offline-first)
    client_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    # Agent & Device
    agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("device.id"),
        nullable=False,
        index=True,
    )

    # Plate Information (confirmed by human)
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    plate_state: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    plate_country: Mapped[str] = mapped_column(String(10), default="BR", nullable=False)

    # Timestamps
    observed_at_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    observed_at_server: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Location (PostGIS)
    location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326),
        nullable=False,
    )
    location_accuracy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # meters

    # Additional metadata
    heading: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # degrees
    speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # km/h

    # Vehicle details
    vehicle_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    vehicle_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Sync status
    sync_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="syncstatus", create_constraint=True),
        default=SyncStatus.PENDING,
        nullable=False,
    )
    sync_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # System metadata
    connectivity_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    metadata_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    agent: Mapped[User] = relationship(back_populates="observations")
    device: Mapped[Device] = relationship(back_populates="observations")
    plate_reads: Mapped[List["PlateRead"]] = relationship(back_populates="observation")
    suspicion_report: Mapped[Optional["SuspicionReport"]] = relationship(
        back_populates="observation"
    )
    instant_alerts: Mapped[List["Alert"]] = relationship(back_populates="observation")
    reviews: Mapped[List["IntelligenceReview"]] = relationship(
        back_populates="observation"
    )

    __table_args__ = (
        Index("ix_observation_plate_time", "plate_number", "observed_at_local"),
        Index(
            "ix_observation_agency_plate_time",
            "agency_id",
            "plate_number",
            "observed_at_local",
        ),
        Index("ix_observation_agent_time", "agent_id", "observed_at_local"),
        Index("ix_observation_sync_status", "sync_status"),
    )


class PlateRead(Base):
    """OCR plate read with raw data and confidence."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
    )

    # OCR Raw data
    ocr_raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    ocr_engine: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "mlkit_v2", "fallback"

    # Image metadata
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # SHA-256
    image_width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing metadata
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    observation: Mapped[VehicleObservation] = relationship(back_populates="plate_reads")


# =============================================================================
# SUSPICION MODELS
# =============================================================================


class SuspicionReport(Base):
    """Structured suspicion report linked to observation."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        unique=True,
        nullable=False,
    )

    # Structured fields
    reason: Mapped[SuspicionReason] = mapped_column(
        Enum(SuspicionReason, name="suspicionreason", create_constraint=True),
        nullable=False,
    )
    level: Mapped[SuspicionLevel] = mapped_column(
        Enum(SuspicionReason, name="suspicionlevel", create_constraint=True),
        nullable=False,
    )
    urgency: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel, name="urgencylevel", create_constraint=True),
        nullable=False,
    )

    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- ABORDAGEM (APPROACH) FIELDS ---
    # These fields capture the result of field approach
    abordado: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, description="Whether the vehicle was approached"
    )
    nivel_abordagem: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, description="Suspicion level during approach (1-10)"
    )
    ocorrencia_registrada: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, description="Whether an occurrence was registered"
    )
    texto_ocorrencia: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, description="Details of the registered occurrence"
    )
    # -------------------------------

    # Optional media
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    # System evaluation
    system_relevance_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # Relationships
    observation: Mapped[VehicleObservation] = relationship(
        back_populates="suspicion_report"
    )
    alerts: Mapped[List["Alert"]] = relationship(back_populates="suspicion_report")


# =============================================================================
# ALERT MODELS
# =============================================================================


class Alert(Base):
    """Alert generated by system or manual triggers."""

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alerttype", create_constraint=True),
        nullable=False,
        index=True,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alertseverity", create_constraint=True),
        nullable=False,
        index=True,
    )

    # Source
    observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=True,
    )
    suspicion_report_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suspicionreport.id"),
        nullable=True,
    )

    # Alert content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Triggered by
    triggered_by_rule_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alertrule.id"),
        nullable=True,
    )
    triggered_manually_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

    # Status
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

    # Context data
    context_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    observation: Mapped[Optional[VehicleObservation]] = relationship(
        back_populates="instant_alerts"
    )
    suspicion_report: Mapped[Optional[SuspicionReport]] = relationship(
        back_populates="alerts"
    )
    rule: Mapped[Optional["AlertRule"]] = relationship(back_populates="alerts")

    __table_args__ = (
        Index("ix_alert_severity_type", "severity", "alert_type"),
        Index("ix_alert_acknowledged", "is_acknowledged"),
    )


class AlertRule(Base):
    """Configurable alert rules."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Conditions (stored as JSON for flexibility)
    conditions: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alerttype", create_constraint=True),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alertseverity", create_constraint=True),
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer, default=100
    )  # Lower = higher priority

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # Metrics
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    alerts: Mapped[List[Alert]] = relationship(back_populates="rule")


# =============================================================================
# INTELLIGENCE REVIEW MODELS
# =============================================================================


class IntelligenceReview(Base):
    """Human intelligence review of observations/suspicions."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
    )
    reviewer_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # Review decision
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="reviewstatus", create_constraint=True),
        nullable=False,
        index=True,
    )

    # Required justification for sensitive operations
    justification: Mapped[str] = mapped_column(Text, nullable=False)

    # Reclassification (optional)
    reclassified_reason: Mapped[Optional[SuspicionReason]] = mapped_column(
        Enum(SuspicionReason, name="suspicionreason", create_constraint=True),
        nullable=True,
    )
    reclassified_level: Mapped[Optional[SuspicionLevel]] = mapped_column(
        Enum(SuspicionLevel, name="suspicionlevel", create_constraint=True),
        nullable=True,
    )
    reclassified_urgency: Mapped[Optional[UrgencyLevel]] = mapped_column(
        Enum(UrgencyLevel, name="urgencylevel", create_constraint=True),
        nullable=True,
    )

    # Linked to occurrence
    occurrence_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    occurrence_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    observation: Mapped[VehicleObservation] = relationship(back_populates="reviews")
    reviewer: Mapped[User] = relationship(back_populates="reviews")
    feedback: Mapped[Optional["FeedbackEvent"]] = relationship(back_populates="review")


class FeedbackEvent(Base):
    """Feedback sent back to field agent after review."""

    review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intelligencereview.id"),
        unique=True,
        nullable=False,
    )

    # Target agent
    target_agent_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )

    # Feedback content
    feedback_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "confirmation", "guidance", "alert"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Actionable guidance
    recommended_action: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Delivery status
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    review: Mapped[IntelligenceReview] = relationship(back_populates="feedback")


# =============================================================================
# WATCHLIST / INDEPENDENT VEHICLE INTEREST
# =============================================================================


class WatchlistEntry(Base):
    """Independent registry of vehicles under intelligence interest."""

    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    )
    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[WatchlistStatus] = mapped_column(
        Enum(WatchlistStatus, name="watchliststatus", create_constraint=True),
        nullable=False,
        default=WatchlistStatus.ACTIVE,
        index=True,
    )
    category: Mapped[WatchlistCategory] = mapped_column(
        Enum(WatchlistCategory, name="watchlistcategory", create_constraint=True),
        nullable=False,
        index=True,
    )

    plate_number: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )
    plate_partial: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )
    vehicle_make: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vehicle_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    visual_traits: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    interest_reason: Mapped[str] = mapped_column(Text, nullable=False)
    information_source: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="reserved"
    )
    confidence_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    geographic_scope: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active_time_window: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    recommended_action: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    silent_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    review_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_watchlist_status_priority", "agency_id", "status", "priority"),
        Index("ix_watchlist_plate_status", "agency_id", "plate_number", "status"),
    )


# =============================================================================
# ROUTE ANALYSIS MODELS
# =============================================================================


class RoutePattern(Base):
    """Detected route pattern for a vehicle."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Pattern characteristics
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Spatial analysis
    centroid_location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326),
        nullable=False,
    )
    bounding_box: Mapped[Any] = mapped_column(
        Geometry("POLYGON", srid=4326),
        nullable=False,
    )

    # Route corridor (linestring of main path)
    corridor: Mapped[Optional[Any]] = mapped_column(
        Geometry("LINESTRING", srid=4326),
        nullable=True,
    )

    # Analysis results
    primary_corridor_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    predominant_direction: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # degrees
    recurrence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    pattern_strength: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "weak", "moderate", "strong"

    # Temporal patterns
    common_hours: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=True)
    common_days: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=True)

    # Metadata
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    analysis_version: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_route_pattern_plate", "agency_id", "plate_number"),
        Index("ix_route_pattern_strength", "pattern_strength"),
    )


# =============================================================================
# AUDIT & SYNC MODELS
# =============================================================================


class AuditLog(Base):
    """Comprehensive audit trail."""

    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "observation", "review", etc.
    resource_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Details
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # For sensitive operations
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional[User]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_action_time", "action", "created_at"),
    )


class SyncQueue(Base):
    """Queue for offline synchronization tracking."""

    client_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "observation", etc.
    entity_local_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_server_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    operation: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "create", "update"
    payload_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # SHA-256 for idempotency

    status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="syncstatus", create_constraint=True),
        default=SyncStatus.PENDING,
        nullable=False,
    )

    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_syncqueue_status_attempts", "status", "attempt_count"),
        Index("ix_syncqueue_client_device", "client_id", "device_id"),
    )


# =============================================================================
# EXTERNAL INTEGRATION MODELS
# =============================================================================


class ExternalQuery(Base):
    """Record of external system queries (plate check, etc)."""

    observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=True,
    )

    query_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "plate_check", "wanted_check"
    queried_value: Mapped[str] = mapped_column(String(255), nullable=False)

    # External system
    system_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Response
    response_status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "success", "error", "timeout"
    response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    response_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Metadata
    queried_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)


class Asset(Base):
    """Storage record for images, audio, attachments."""

    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "image", "audio"
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)

    # File metadata
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Upload metadata
    uploaded_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )
    uploaded_from_device: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("device.id"),
        nullable=True,
    )

    # Processing metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relations
    related_observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_asset_type_observation", "asset_type", "related_observation_id"),
    )


class WatchlistRule(Base):
    """Rules associated with a watchlist entry."""

    watchlist_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlistentry.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default="moderate"
    )
    target_scope: Mapped[str] = mapped_column(
        String(50), nullable=False, default="intelligence_only"
    )
    geographic_scope: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time_window: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    conditions_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class WatchlistHit(Base):
    """Match produced between an observation and a watchlist entry."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    watchlist_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlistentry.id"),
        nullable=False,
        index=True,
    )
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )

    __table_args__ = (
        Index(
            "ix_watchlisthit_observation_watchlist",
            "observation_id",
            "watchlist_entry_id",
        ),
    )


class RouteRegionOfInterest(Base):
    """Named region relevant to route anomaly analysis."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region_type: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    geometry: Mapped[Any] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SensitiveAssetZone(Base):
    """Zones around protected or sensitive assets."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False)
    municipality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="high")
    geometry: Mapped[Any] = mapped_column(
        Geometry("MULTIPOLYGON", srid=4326), nullable=False
    )
    radius_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ImpossibleTravelEvent(Base):
    """Result of impossible travel detection."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    previous_observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicleobservation.id"), nullable=True
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    travel_time_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    plausible_time_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )


class RouteAnomalyEvent(Base):
    """Route anomaly result for an observation."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    region_from_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routeregionofinterest.id"), nullable=True
    )
    region_to_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routeregionofinterest.id"), nullable=True
    )
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )


class SensitiveAssetRecurrenceEvent(Base):
    """Recurrence of a plate in a sensitive asset zone."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    zone_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sensitiveassetzone.id"),
        nullable=False,
        index=True,
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )


class ConvoyEvent(Base):
    """Co-occurrence or convoy relationship between vehicles."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    primary_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    related_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    cooccurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Advanced convoy analysis
    convoy_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Group multiple convoy events as same convoy
    convoy_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Number of vehicles in convoy
    spatial_proximity_meters: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Average distance between vehicles
    temporal_window_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Time window for convoy detection
    route_similarity: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Similarity score of routes (0-1)
    
    # Temporal patterns
    common_hours: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # Hours when convoy occurs
    common_days: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # Days when convoy occurs
    
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )
    
    __table_args__ = (
        Index("ix_convoy_convoy_id", "convoy_id"),
        Index("ix_convoy_primary_related", "primary_plate", "related_plate"),
    )


class RoamingEvent(Base):
    """Roaming or loitering detection result."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    area_label: Mapped[str] = mapped_column(String(255), nullable=False)
    recurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Advanced roaming analysis
    roaming_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Group multiple roaming events as same pattern
    area_geometry: Mapped[Optional[Any]] = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True
    )  # Geographic area of roaming
    area_size_km2: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Size of roaming area in km²
    average_stay_minutes: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Average time spent in area
    total_observations: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Total observations in area
    
    # Temporal patterns
    first_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    common_hours: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # Hours when roaming occurs
    common_days: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # Days when roaming occurs
    
    # Zone classification
    zone_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # residential, commercial, industrial, mixed
    zone_risk_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # low, medium, high based on historical data
    
    decision: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )
    
    __table_args__ = (
        Index("ix_roaming_roaming_id", "roaming_id"),
        Index("ix_roaming_plate_area", "plate_number", "area_label"),
    )


class SuspiciousRoute(Base):
    """Manually registered suspicious routes for intelligence analysis."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    crime_type: Mapped[CrimeType] = mapped_column(
        Enum(CrimeType, name="crimetype", create_constraint=True),
        nullable=False,
    )
    direction: Mapped[RouteDirection] = mapped_column(
        Enum(RouteDirection, name="routedirection", create_constraint=True),
        nullable=False,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel", create_constraint=True),
        nullable=False,
    )

    # Spatial geometry
    route_geometry: Mapped[Any] = mapped_column(
        Geometry("LINESTRING", srid=4326),
        nullable=False,
    )
    buffer_distance_meters: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # For ST_Buffer alert zone

    # Active period
    active_from_hour: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0-23
    active_to_hour: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 0-23
    active_days: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer), nullable=True
    )  # 0=Monday, 6=Sunday

    # Metadata
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )
    approval_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, approved, rejected
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    creator: Mapped[User] = relationship(
        foreign_keys=[created_by], back_populates="audit_logs"
    )
    approver: Mapped[Optional[User]] = relationship(
        foreign_keys=[approved_by], back_populates="audit_logs"
    )

    __table_args__ = (
        Index("ix_suspicious_route_agency_active", "agency_id", "is_active"),
        Index("ix_suspicious_route_crime_type", "crime_type"),
    )


class SuspicionScore(Base):
    """Composite suspicion score for an observation."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_label: Mapped[AlgorithmDecision] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )


class SuspicionScoreFactor(Base):
    """Weighted factors used to compute suspicion score."""

    suspicion_score_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suspicionscore.id"), nullable=False, index=True
    )
    factor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    factor_source: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False, default="positive"
    )


class IntelligenceCase(Base):
    """Analytical case or dossier."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="casestatus", create_constraint=True),
        nullable=False,
        default=CaseStatus.OPEN,
        index=True,
    )
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="reserved"
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    review_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CaseLink(Base):
    """Links cases to entities."""

    case_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("intelligencecase.id"),
        nullable=False,
        index=True,
    )
    link_type: Mapped[CaseLinkType] = mapped_column(
        Enum(CaseLinkType, name="caselinktype", create_constraint=True), nullable=False
    )
    linked_entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    linked_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )


class AnalystReview(Base):
    """Structured analyst review."""

    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=False,
        index=True,
    )
    analyst_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    status: Mapped[AnalystReviewStatus] = mapped_column(
        Enum(AnalystReviewStatus, name="analystreviewstatus", create_constraint=True),
        nullable=False,
        default=AnalystReviewStatus.DRAFT,
    )
    conclusion: Mapped[Optional[AnalystConclusion]] = mapped_column(
        Enum(AnalystConclusion, name="analystconclusion", create_constraint=True),
        nullable=True,
    )
    decision: Mapped[Optional[AnalystDecision]] = mapped_column(
        Enum(AnalystDecision, name="analystdecision", create_constraint=True),
        nullable=True,
    )
    source_quality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_reliability: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reinforcing_factors: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    weakening_factors: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    recommendation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    justification: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="reserved"
    )
    review_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    linked_case_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("intelligencecase.id"), nullable=True
    )
    linked_occurrence_ref: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )


class AnalystReviewVersion(Base):
    """Versioned history of analyst review."""

    analyst_review_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analystreview.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    snapshot_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)


class AnalystFeedbackTemplate(Base):
    """Reusable feedback templates."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="operational"
    )
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AnalystFeedbackEvent(Base):
    """Structured feedback to field agents or teams."""

    agency_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agency.id"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=True,
        index=True,
    )
    analyst_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    target_user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=True
    )
    target_team_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sensitivity_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="operational"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analystfeedbacktemplate.id"), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AlgorithmRun(Base):
    """Execution record for online or offline algorithm runs."""

    algorithm_type: Mapped[AlgorithmType] = mapped_column(
        Enum(AlgorithmType, name="algorithmtype", create_constraint=True),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicleobservation.id"),
        nullable=True,
        index=True,
    )
    run_scope: Mapped[str] = mapped_column(String(20), nullable=False, default="online")
    status: Mapped[AlgorithmRunStatus] = mapped_column(
        Enum(AlgorithmRunStatus, name="algorithmrunstatus", create_constraint=True),
        nullable=False,
        default=AlgorithmRunStatus.PENDING,
    )
    payload_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="v1"
    )
    input_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    output_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AlgorithmExplanation(Base):
    """Human-readable explanation for algorithm outputs."""

    algorithm_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("algorithmrun.id"), nullable=False, index=True
    )
    algorithm_type: Mapped[AlgorithmType] = mapped_column(
        Enum(AlgorithmType, name="algorithmtype", create_constraint=True),
        nullable=False,
        index=True,
    )
    decision: Mapped[Optional[AlgorithmDecision]] = mapped_column(
        Enum(AlgorithmDecision, name="algorithmdecision", create_constraint=True),
        nullable=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    false_positive_risk: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
