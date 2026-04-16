"""
F.A.R.O. Observation Schemas - Vehicle observation data
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.db.base import SyncStatus, StreetNumberingDirection
from app.schemas.common import GeolocationPoint, TimestampedSchema


class PlateReadBase(BaseModel):
    """Base OCR plate read data."""
    model_config = ConfigDict(from_attributes=True)
    
    ocr_raw_text: str = Field(..., max_length=50)
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    ocr_engine: str = Field(default="mlkit_v2", max_length=50)


class PlateReadCreate(PlateReadBase):
    """Schema for creating a plate read."""
    image_base64: Optional[str] = None  # Optional: image data for processing
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    processing_time_ms: Optional[int] = Field(None, ge=0)


class PlateReadResponse(PlateReadBase):
    """Schema for plate read response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    observation_id: UUID
    image_url: Optional[str] = None
    image_hash: Optional[str] = None
    processed_at: datetime
    processing_time_ms: Optional[int] = None


class VehicleObservationBase(BaseModel):
    """Base vehicle observation data."""
    model_config = ConfigDict(from_attributes=True)
    
    # Client-generated ID for idempotency (offline-first)
    client_id: Optional[str] = Field(None, max_length=255)
    
    # Plate (human confirmed)
    plate_number: str = Field(..., max_length=20)
    plate_state: Optional[str] = Field(None, max_length=10)
    plate_country: str = Field(default="BR", max_length=10)
    
    # Timestamps
    observed_at_local: datetime
    
    # Location
    location: GeolocationPoint
    heading: Optional[float] = Field(None, ge=0, le=360)
    speed: Optional[float] = Field(None, ge=0)
    
    # Vehicle details
    vehicle_color: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=100)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2100)


class VehicleObservationCreate(VehicleObservationBase):
    """Schema for creating a vehicle observation (from mobile app)."""
    device_id: str = Field(..., max_length=255)
    
    # OCR data
    plate_read: Optional[PlateReadCreate] = None
    
    # Optional media (will be uploaded separately if large)
    image_base64: Optional[str] = None
    
    # Metadata
    connectivity_type: Optional[str] = Field(None, max_length=20)
    app_version: str = Field(..., max_length=50)
    
    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, v: str) -> str:
        """Normalize plate number: uppercase, remove spaces."""
        return v.upper().replace(" ", "").replace("-", "").strip()


class VehicleObservationUpdate(BaseModel):
    """Schema for updating a vehicle observation."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: Optional[str] = Field(None, max_length=20)
    plate_state: Optional[str] = Field(None, max_length=10)
    vehicle_color: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[str] = Field(None, max_length=50)
    vehicle_model: Optional[str] = Field(None, max_length=100)
    vehicle_year: Optional[int] = Field(None, ge=1900, le=2100)
    sync_status: Optional[SyncStatus] = None


class InstantFeedback(BaseModel):
    """Instant feedback for field agent."""
    model_config = ConfigDict(from_attributes=True)
    
    has_alert: bool = False
    alert_level: Optional[str] = None  # "info", "warning", "critical"
    alert_title: Optional[str] = None
    alert_message: Optional[str] = None
    previous_observations_count: int = 0
    is_monitored: bool = False
    intelligence_interest: bool = False
    guidance: Optional[str] = None
    state_registry_status: Optional[Dict[str, Any]] = None
    prior_suspicion_context: Optional[Dict[str, Any]] = None
    requires_suspicion_confirmation: bool = False


class ApproachConfirmationRequest(BaseModel):
    """Field confirmation after approaching a vehicle."""
    model_config = ConfigDict(from_attributes=True)

    confirmed_suspicion: bool
    approach_outcome: str = Field(default="approached", max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)
    approached_at_local: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[GeolocationPoint] = None
    
    # Additional fields from mobile app to prevent silent data loss
    suspicion_level_slider: Optional[int] = Field(None, ge=0, le=100)
    was_approached: bool = True
    has_incident: bool = False
    street_direction: Optional[StreetNumberingDirection] = None


class ApproachConfirmationResponse(BaseModel):
    """Response for approach confirmation workflow."""
    model_config = ConfigDict(from_attributes=True)

    observation_id: UUID
    plate_number: str
    confirmed_suspicion: bool
    approach_outcome: str
    notified_original_agent: bool
    original_agent_id: Optional[UUID] = None
    original_agent_name: Optional[str] = None
    feedback_event_id: Optional[UUID] = None
    processed_at: datetime


class VehicleObservationResponse(VehicleObservationBase, TimestampedSchema):
    """Schema for vehicle observation response."""
    model_config = ConfigDict(from_attributes=True)
    
    # Server fields
    agent_id: UUID
    agent_name: str
    device_id: UUID
    observed_at_server: Optional[datetime] = None
    
    # Sync status
    sync_status: SyncStatus
    sync_attempts: int
    synced_at: Optional[datetime] = None
    
    # Related data
    plate_reads: List[PlateReadResponse] = []
    instant_feedback: Optional[InstantFeedback] = None
    
    # System metadata
    metadata_snapshot: Optional[Dict[str, Any]] = None


class ObservationListFilter(BaseModel):
    """Filter parameters for observation list."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: Optional[str] = None
    agent_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sync_status: Optional[SyncStatus] = None
    has_suspicion: Optional[bool] = None
    location_near: Optional[GeolocationPoint] = None
    location_radius_meters: Optional[float] = Field(None, gt=0)


class ObservationHistoryItem(BaseModel):
    """Item in observation history (for mobile app)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    client_id: Optional[str] = None
    plate_number: str
    observed_at_local: datetime
    location: GeolocationPoint
    sync_status: SyncStatus
    has_feedback: bool
    has_suspicion: bool


class ObservationHistoryResponse(BaseModel):
    """Response for observation history endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[ObservationHistoryItem]
    pending_sync_count: int
    total_count: int


class PlateSuspicionCheckResponse(BaseModel):
    """Response for plate suspicion check (post-OCR alert)."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    is_suspect: bool
    alert_level: Optional[str] = None  # "info", "warning", "critical"
    alert_title: Optional[str] = None
    alert_message: Optional[str] = None
    suspicion_reason: Optional[str] = None
    suspicion_level: Optional[str] = None
    previous_observations_count: int = 0
    is_monitored: bool = False
    intelligence_interest: bool = False
    has_active_watchlist: bool = False
    watchlist_category: Optional[str] = None
    guidance: Optional[str] = None
    requires_approach_confirmation: bool = False
    first_suspicion_agent_name: Optional[str] = None
    first_suspicion_observation_id: Optional[UUID] = None
    first_suspicion_at: Optional[datetime] = None


class OcrValidationRequest(BaseModel):
    """Request for OCR validation on backend (mobile can reprocess images when online)."""
    model_config = ConfigDict(from_attributes=True)
    
    image_base64: str = Field(..., description="Base64 encoded image")
    mobile_ocr_text: Optional[str] = Field(None, description="OCR result from mobile (ML Kit)")
    mobile_ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class OcrValidationResponse(BaseModel):
    """Response for OCR validation."""
    model_config = ConfigDict(from_attributes=True)
    
    plate_number: str
    confidence: float
    plate_format: str  # "old", "mercusor", "unknown"
    processing_time_ms: float
    ocr_engine: str = "yolov11_easyocr"
    is_valid_format: bool
    improved_over_mobile: bool = False
    mobile_comparison: Optional[Dict[str, Any]] = None
