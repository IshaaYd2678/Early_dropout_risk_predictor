"""ML Model registry and versioning."""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import BaseModel


class ModelType(str, Enum):
    """Types of ML models."""
    XGBOOST = "xgboost"
    LOGISTIC_REGRESSION = "logistic_regression"
    DECISION_TREE = "decision_tree"
    EBM = "explainable_boosting"  # Interpretable by design
    ENSEMBLE = "ensemble"
    RULE_BASED = "rule_based"


class ModelStatus(str, Enum):
    """Model deployment status."""
    TRAINING = "training"
    VALIDATING = "validating"
    READY = "ready"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class MLModel(BaseModel):
    """
    ML Model registry entry.
    Tracks model configurations and metadata.
    """
    
    __tablename__ = "ml_models"
    
    # Tenant association (tenant-specific models)
    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # NULL = global model
        index=True
    )
    
    # Model Info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_type: Mapped[ModelType] = mapped_column(SQLEnum(ModelType), nullable=False)
    
    # Configuration
    features: Mapped[List[str]] = mapped_column(JSON, default=list)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)
    training_config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Current deployed version
    current_version_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    versions: Mapped[List["ModelVersion"]] = relationship(
        "ModelVersion",
        back_populates="model",
        order_by="desc(ModelVersion.created_at)"
    )
    
    __table_args__ = (
        Index("ix_ml_models_tenant_name", "tenant_id", "name", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<MLModel {self.name} ({self.model_type.value})>"


class ModelVersion(BaseModel):
    """
    Versioned ML model with metrics and artifacts.
    Supports rollback and A/B testing.
    """
    
    __tablename__ = "model_versions"
    
    # Parent model
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ml_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Version info
    version: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "1.0.0"
    status: Mapped[ModelStatus] = mapped_column(
        SQLEnum(ModelStatus),
        default=ModelStatus.TRAINING,
        nullable=False
    )
    
    # Artifact storage
    artifact_path: Mapped[str] = mapped_column(String(500), nullable=False)
    artifact_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Training metrics
    training_samples: Mapped[int] = mapped_column(Integer, default=0)
    training_duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Performance metrics
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    f1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    auc_roc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Fairness metrics
    fairness_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    bias_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Deployment info
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deployed_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    
    # Deprecation
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deprecation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata
    feature_importance: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="versions")
    
    __table_args__ = (
        Index("ix_model_versions_model_version", "model_id", "version", unique=True),
        Index("ix_model_versions_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<ModelVersion {self.version} ({self.status.value})>"


class Prediction(BaseModel):
    """
    Individual prediction record.
    Used for monitoring and explainability.
    """
    
    __tablename__ = "predictions"
    
    # Context
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    model_version_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=False
    )
    
    # Prediction
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Explanation
    top_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Input features (for debugging)
    input_features: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Request metadata
    requested_by: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    request_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # api, dashboard, batch
    
    __table_args__ = (
        Index("ix_predictions_student_date", "student_id", "created_at"),
        Index("ix_predictions_tenant_date", "tenant_id", "created_at"),
    )
