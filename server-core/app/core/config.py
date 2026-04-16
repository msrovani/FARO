"""
F.A.R.O. Server Core - Configuration
Centralized settings using Pydantic Settings
"""
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = Field(default="F.A.R.O. Server Core")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(default="Ferramenta de Análise de Rotas e Observações")
    debug: bool = Field(default=False)
    environment: str = Field(default="production")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default="auto")  # "auto" or number
    reload: bool = Field(default=False)
    auto_init_db: bool = Field(default=False)
    
    # Process Pool Executor for CPU-bound tasks
    process_pool_max_workers: int = Field(default="auto")  # "auto" or number
    process_pool_cpu_bound_workers: int = Field(default="auto")  # For CPU-intensive tasks
    process_pool_io_bound_workers: int = Field(default="auto")  # For I/O-intensive tasks
    
    # Security
    secret_key: str = Field(default="CHANGE_ME_IN_PRODUCTION_32CHARS_MIN")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    password_min_length: int = Field(default=8)
    
    # CORS
    cors_origins: List[str] = Field(default=["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["*"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Database - PostgreSQL with PostGIS
    database_url: str = Field(default="postgresql+asyncpg://faro:faro@localhost:5432/faro_db")
    database_echo: bool = Field(default=False)
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)
    database_pool_timeout: int = Field(default=30)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_streams_url: str = Field(default="redis://localhost:6379/1")
    redis_cache_url: str = Field(default="redis://localhost:6379/2")
    redis_streams_enabled: bool = Field(default=True)
    redis_stream_key: str = Field(default="faro.events")
    redis_stream_group: str = Field(default="faro-analytics")
    redis_stream_consumer_name: Optional[str] = Field(default=None)
    redis_stream_batch_size: int = Field(default=20)
    redis_stream_block_ms: int = Field(default=5000)
    redis_stream_error_backoff_seconds: int = Field(default=3)
    redis_socket_timeout: int = Field(default=5)
    redis_socket_connect_timeout: int = Field(default=5)
    
    # S3/MinIO Storage
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")
    s3_bucket_name: str = Field(default="faro-assets")
    s3_region: str = Field(default="us-east-1")
    s3_secure: bool = Field(default=False)
    s3_presigned_url_expiry: int = Field(default=3600)  # 1 hour
    
    # OCR Service (ML Kit integration via adapter)
    ocr_service_url: Optional[str] = Field(default=None)
    ocr_fallback_enabled: bool = Field(default=True)
    ocr_confidence_threshold: float = Field(default=0.7)
    ocr_auto_accept_enabled: bool = Field(default=False)
    ocr_auto_accept_threshold: float = Field(default=0.85)
    ocr_device: str = Field(default="auto")  # "auto", "cpu", "cuda", "mps"
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)
    
    # Alert Engine
    alert_evaluation_interval: int = Field(default=30)  # seconds
    alert_batch_size: int = Field(default=100)
    
    # Route Analysis
    route_analysis_enabled: bool = Field(default=True)
    route_min_observations: int = Field(default=3)
    route_time_window_hours: int = Field(default=72)
    route_spatial_buffer_meters: int = Field(default=500)
    
    # Queue Prioritization
    queue_auto_prioritization_enabled: bool = Field(default=False)
    queue_score_weight: float = Field(default=0.6)
    queue_urgency_weight: float = Field(default=0.4)
    queue_score_threshold: float = Field(default=0.7)
    
    # Progressive Upload
    progressive_upload_enabled: bool = Field(default=False)
    progressive_upload_chunk_size_mb: int = Field(default=5)
    progressive_upload_max_retries: int = Field(default=3)
    
    # Audit & Compliance
    audit_retention_days: int = Field(default=2555)  # 7 years
    audit_sensitive_operations: List[str] = Field(default=[
        "intelligence_review_completed",
        "feedback_sent",
        "alert_rule_modified",
    ])
    
    # Observability
    sentry_dsn: Optional[str] = Field(default=None)
    otlp_endpoint: Optional[str] = Field(default=None)
    prometheus_port: int = Field(default=9090)
    log_level: str = Field(default="INFO")
    structured_logging: bool = Field(default=True)
    
    # WebSocket / Push Notifications
    websocket_enabled: bool = Field(default=False)
    websocket_ping_interval: int = Field(default=20)
    websocket_ping_timeout: int = Field(default=30)
    websocket_max_connections: int = Field(default=1000)
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, v):
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        return v
    
    @field_validator("workers", "process_pool_max_workers", "process_pool_cpu_bound_workers", "process_pool_io_bound_workers", mode="before")
    @classmethod
    def resolve_auto_workers(cls, v):
        """Resolve 'auto' to actual worker count based on hardware."""
        if isinstance(v, str) and v.strip().lower() == "auto":
            try:
                from app.utils.hardware_detector import get_hardware_capabilities, calculate_optimal_workers
                hardware = get_hardware_capabilities()
                
                # Determine task type based on field name
                if "cpu_bound" in str(cls):
                    return calculate_optimal_workers(hardware, "cpu_bound")
                elif "io_bound" in str(cls):
                    return calculate_optimal_workers(hardware, "io_bound")
                else:
                    return calculate_optimal_workers(hardware, "general")
            except ImportError:
                # Fallback to default if hardware detection fails
                return 4
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
