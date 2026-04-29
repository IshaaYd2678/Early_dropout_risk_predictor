"""
Application configuration with environment-based settings.
Production-ready configuration management.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "StudentRetentionPlatform"
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    api_version: str = "v1"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/retention_platform"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    
    # JWT Authentication
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # OAuth2 / SSO
    oauth2_google_client_id: Optional[str] = None
    oauth2_google_client_secret: Optional[str] = None
    oauth2_microsoft_client_id: Optional[str] = None
    oauth2_microsoft_client_secret: Optional[str] = None
    
    # ML Settings
    model_registry_path: str = "./data/models"
    feature_store_path: str = "./data/features"
    model_retrain_interval_hours: int = 24
    
    # Security & Compliance
    encryption_key: str = Field(..., min_length=32)
    data_retention_days: int = 2555  # ~7 years for FERPA
    audit_log_enabled: bool = True
    pii_masking_enabled: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Monitoring
    prometheus_enabled: bool = True
    opentelemetry_enabled: bool = False
    sentry_dsn: Optional[str] = None
    
    # Multi-tenancy
    default_tenant_id: str = "default"
    max_students_per_tenant: int = 100000
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
