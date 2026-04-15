"""
F.A.R.O. API Schemas - Pydantic v2 Models
"""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload,
)
from app.schemas.observation import (
    VehicleObservationCreate,
    VehicleObservationUpdate,
    VehicleObservationResponse,
    PlateReadCreate,
    PlateReadResponse,
)
from app.schemas.suspicion import (
    SuspicionReportCreate,
    SuspicionReportResponse,
)
from app.schemas.intelligence import (
    IntelligenceReviewCreate,
    IntelligenceReviewResponse,
    FeedbackEventCreate,
    FeedbackEventResponse,
)
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
)
from app.schemas.route import (
    RoutePatternResponse,
    RouteAnalysisRequest,
)
from app.schemas.watchlist import (
    WatchlistEntryCreate,
    WatchlistEntryUpdate,
    WatchlistEntryResponse,
)
from app.schemas.analytics import (
    AlgorithmResultResponse,
    ObservationAnalyticDetailResponse,
    QueueScoreSummary,
    SuspicionScoreResponse,
    SuspicionScoreFactorResponse,
    IntelligenceCaseCreate,
    IntelligenceCaseUpdate,
    IntelligenceCaseResponse,
    AnalystReviewCreateRequest,
    AnalystReviewUpdateRequest,
    AnalystReviewResponse,
    AnalystFeedbackCreateRequest,
    AnalystFeedbackResponse,
    AnalystFeedbackTemplateCreateRequest,
    AnalystFeedbackTemplateResponse,
    AuditLogResponse,
)
from app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncQueueItem,
)
from app.schemas.agency import (
    AgencyCreate,
    AgencyResponse,
    AgencyUpdate,
    AgencyListResponse,
)
from app.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    FilterParams,
    GeolocationPoint,
    ErrorResponse,
    SuccessResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    # Observation schemas
    "VehicleObservationCreate",
    "VehicleObservationUpdate",
    "VehicleObservationResponse",
    "PlateReadCreate",
    "PlateReadResponse",
    # Suspicion schemas
    "SuspicionReportCreate",
    "SuspicionReportResponse",
    # Intelligence schemas
    "IntelligenceReviewCreate",
    "IntelligenceReviewResponse",
    "FeedbackEventCreate",
    "FeedbackEventResponse",
    # Alert schemas
    "AlertCreate",
    "AlertResponse",
    "AlertRuleCreate",
    "AlertRuleResponse",
    # Route schemas
    "RoutePatternResponse",
    "RouteAnalysisRequest",
    "WatchlistEntryCreate",
    "WatchlistEntryUpdate",
    "WatchlistEntryResponse",
    "AlgorithmResultResponse",
    "ObservationAnalyticDetailResponse",
    "QueueScoreSummary",
    "SuspicionScoreResponse",
    "SuspicionScoreFactorResponse",
    "IntelligenceCaseCreate",
    "IntelligenceCaseUpdate",
    "IntelligenceCaseResponse",
    "AnalystReviewCreateRequest",
    "AnalystReviewUpdateRequest",
    "AnalystReviewResponse",
    "AnalystFeedbackCreateRequest",
    "AnalystFeedbackResponse",
    "AnalystFeedbackTemplateCreateRequest",
    "AnalystFeedbackTemplateResponse",
    "AuditLogResponse",
    # Sync schemas
    "SyncBatchRequest",
    "SyncBatchResponse",
    "SyncQueueItem",
    # Agency schemas
    "AgencyCreate",
    "AgencyResponse",
    "AgencyUpdate",
    "AgencyListResponse",
    # Common schemas
    "PaginationParams",
    "PaginatedResponse",
    "FilterParams",
    "GeolocationPoint",
    "ErrorResponse",
    "SuccessResponse",
]
