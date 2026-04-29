"""
Production configuration with environment variables and validation.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import secrets
from pathlib import Path


class Settings(BaseSettings):
    """Production settings with validation."""
    
    # Application
    app_name: str = Field(default="Early Warning System", env="APP_NAME")
    app_env: str = Field(default="production", env="APP_ENV")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./data/production.db",
        env="DATABASE_URL"
    )
    
    # Security
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="SECRET_KEY"
    )
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # ML Model
    model_path: Path = Field(
        default=Path("data/models/xgboost_model.pkl"),
        env="MODEL_PATH"
    )
    feature_names_path: Path = Field(
        default=Path("data/models/feature_names.pkl"),
        env="FEATURE_NAMES_PATH"
    )
    scaler_path: Path = Field(
        default=Path("data/models/scaler.pkl"),
        env="SCALER_PATH"
    )
    
    # Logging
    log_file: Path = Field(default=Path("logs/production.log"), env="LOG_FILE")
    log_max_bytes: int = Field(default=10485760, env="LOG_MAX_BYTES")  # 10MB
    log_backup_count: int = Field(default=10, env="LOG_BACKUP_COUNT")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from: str = Field(default="noreply@example.com", env="SMTP_FROM")
    
    # Cache
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # Feature Flags
    enable_predictions: bool = Field(default=True, env="ENABLE_PREDICTIONS")
    enable_interventions: bool = Field(default=True, env="ENABLE_INTERVENTIONS")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    enable_fairness_monitoring: bool = Field(default=True, env="ENABLE_FAIRNESS_MONITORING")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("secret_key", "jwt_secret_key")
    def validate_secret_keys(cls, v):
        """Ensure secret keys are strong enough."""
        if len(v) < 32:
            raise ValueError("Secret keys must be at least 32 characters long")
        return v
    
    @validator("api_workers")
    def validate_workers(cls, v):
        """Validate number of workers."""
        if v < 1 or v > 16:
            raise ValueError("API workers must be between 1 and 16")
        return v
    
    def ensure_directories(self):
        """Create necessary directories."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env.production"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
settings.ensure_directories()
