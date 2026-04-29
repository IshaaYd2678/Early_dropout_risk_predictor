"""Audit logging for compliance and transparency."""
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import String, Text, DateTime, JSON, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # Data Access
    VIEW_STUDENT = "view_student"
    VIEW_RISK_SCORE = "view_risk_score"
    EXPORT_DATA = "export_data"
    
    # Predictions
    PREDICTION_MADE = "prediction_made"
    BULK_PREDICTION = "bulk_prediction"
    
    # Interventions
    INTERVENTION_CREATED = "intervention_created"
    INTERVENTION_UPDATED = "intervention_updated"
    INTERVENTION_APPROVED = "intervention_approved"
    INTERVENTION_COMPLETED = "intervention_completed"
    
    # Admin Actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    SETTINGS_CHANGED = "settings_changed"
    
    # Model Operations
    MODEL_TRAINED = "model_trained"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_ROLLBACK = "model_rollback"
    
    # Compliance
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"
    CONSENT_UPDATED = "consent_updated"


class AuditLog(Base):
    """
    Comprehensive audit log for all system actions.
    Immutable records for compliance.
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True
    )
    
    # Tenant context
    tenant_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        index=True
    )
    
    # Actor
    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        nullable=True,
        index=True
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Action
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True
    )
    
    # Target
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamp (immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    __table_args__ = (
        Index("ix_audit_tenant_action", "tenant_id", "action"),
        Index("ix_audit_user_date", "user_id", "created_at"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} by {self.user_email} at {self.created_at}>"
