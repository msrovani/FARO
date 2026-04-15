"""
F.A.R.O. Sync Schemas - Offline-first synchronization
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.db.base import SyncStatus


class SyncItemBase(BaseModel):
    """Base sync item data."""
    model_config = ConfigDict(from_attributes=True)
    
    entity_type: str = Field(..., max_length=50)  # "observation", "suspicion", etc.
    entity_local_id: str = Field(..., max_length=255)
    operation: str = Field(..., pattern="^(create|update)$")
    payload: Dict[str, Any]
    
    # Hash for idempotency check
    payload_hash: Optional[str] = Field(None, max_length=64)
    
    # Local timestamp for ordering
    created_at_local: datetime


class SyncBatchRequest(BaseModel):
    """Request for batch sync from mobile app."""
    model_config = ConfigDict(from_attributes=True)
    
    device_id: str = Field(..., max_length=255)
    app_version: str = Field(..., max_length=50)
    
    items: List[SyncItemBase]
    
    # Client timestamp
    client_timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncResult(BaseModel):
    """Result of a single sync operation."""
    model_config = ConfigDict(from_attributes=True)
    
    entity_local_id: str
    entity_server_id: Optional[UUID] = None
    status: SyncStatus
    error: Optional[str] = None
    synced_at: Optional[datetime] = None


class SyncBatchResponse(BaseModel):
    """Response for batch sync."""
    model_config = ConfigDict(from_attributes=True)
    
    processed_count: int
    success_count: int
    failed_count: int
    results: List[SyncResult]
    
    # Server timestamp for client sync
    server_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Pending items to sync back to client (e.g., feedback)
    pending_feedback: List[Dict[str, Any]] = []


class SyncQueueItem(BaseModel):
    """Item in sync queue (for monitoring)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    client_id: str
    device_id: str
    entity_type: str
    entity_local_id: str
    entity_server_id: Optional[UUID] = None
    operation: str
    status: SyncStatus
    attempt_count: int
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at_local: datetime
    synced_at: Optional[datetime] = None


class SyncStatusResponse(BaseModel):
    """Sync status for a device/client."""
    model_config = ConfigDict(from_attributes=True)
    
    device_id: str
    pending_count: int
    syncing_count: int
    failed_count: int
    completed_count: int
    last_sync_at: Optional[datetime] = None
    
    # Failed items that need attention
    failed_items: List[SyncQueueItem] = []


class SyncRetryRequest(BaseModel):
    """Request to retry failed sync items."""
    model_config = ConfigDict(from_attributes=True)
    
    device_id: str
    item_ids: List[UUID]


class SyncDiagnostics(BaseModel):
    """Sync diagnostics for troubleshooting."""
    model_config = ConfigDict(from_attributes=True)
    
    total_queued: int
    by_status: Dict[str, int]
    by_entity_type: Dict[str, int]
    oldest_pending: Optional[datetime] = None
    average_attempts: float
    failure_rate_24h: float
