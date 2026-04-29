"""Intervention model with workflow and outcome tracking."""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import BaseModel


class InterventionType(str, Enum):
    """Types of interventions."""
    ACADEMIC_TUTORING = "academic_tutoring"
    COUNSELING = "counseling"
    MENTAL_HEALTH = "mental_health"
    FINANCIAL_AID = "financial_aid"
    PEER_MENTORING = "peer_mentoring"
    CAREER_GUIDANCE = "career_guidance"
    ATTENDANCE_ALERT = "attendance_alert"
    ACADEMIC_PROBATION = "academic_probation"
    STUDY_GROUP = "study_group"
    OTHER = "other"


class InterventionStatus(str, Enum):
    """Intervention workflow status."""
    RECOMMENDED = "recommended"      # AI recommended
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DECLINED = "declined"


class InterventionOutcome(str, Enum):
    """Outcome of intervention."""
    PENDING = "pending"
    RISK_REDUCED = "risk_reduced"
    RISK_STABLE = "risk_stable"
    RISK_INCREASED = "risk_increased"
    STUDENT_RETAINED = "student_retained"
    STUDENT_DROPPED = "student_dropped"
    INCONCLUSIVE = "inconclusive"


class InterventionPriority(str, Enum):
    """Priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Intervention(BaseModel):
    """
    Intervention model tracking all actions taken for at-risk students.
    Supports workflow management and outcome analysis.
    """
    
    __tablename__ = "interventions"
    
    # Tenant association
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Student association
    student_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Intervention Details
    intervention_type: Mapped[InterventionType] = mapped_column(
        SQLEnum(InterventionType),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status & Workflow
    status: Mapped[InterventionStatus] = mapped_column(
        SQLEnum(InterventionStatus),
        default=InterventionStatus.RECOMMENDED,
        nullable=False
    )
    priority: Mapped[InterventionPriority] = mapped_column(
        SQLEnum(InterventionPriority),
        default=InterventionPriority.MEDIUM,
        nullable=False
    )
    
    # Scheduling
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # People involved
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # AI Recommendation
    ai_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Risk Context (at time of intervention)
    risk_score_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level_before: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Outcome Tracking
    outcome: Mapped[InterventionOutcome] = mapped_column(
        SQLEnum(InterventionOutcome),
        default=InterventionOutcome.PENDING,
        nullable=False
    )
    risk_score_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level_after: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Follow-up
    requires_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    followup_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    followup_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="interventions")
    created_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="interventions_created"
    )
    assigned_to_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to]
    )
    follow_ups: Mapped[List["InterventionFollowUp"]] = relationship(
        "InterventionFollowUp",
        back_populates="intervention"
    )
    
    __table_args__ = (
        Index("ix_interventions_student", "student_id"),
        Index("ix_interventions_status", "status"),
        Index("ix_interventions_type", "intervention_type"),
        Index("ix_interventions_tenant_date", "tenant_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Intervention {self.intervention_type.value} for student {self.student_id}>"
    
    @property
    def risk_change(self) -> Optional[float]:
        """Calculate risk score change."""
        if self.risk_score_before is not None and self.risk_score_after is not None:
            return self.risk_score_after - self.risk_score_before
        return None
    
    @property
    def was_effective(self) -> bool:
        """Check if intervention was effective."""
        return self.outcome in (
            InterventionOutcome.RISK_REDUCED,
            InterventionOutcome.STUDENT_RETAINED
        )


class InterventionFollowUp(BaseModel):
    """Follow-up records for interventions."""
    
    __tablename__ = "intervention_followups"
    
    intervention_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("interventions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    outcome_update: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    next_followup_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Relationships
    intervention: Mapped["Intervention"] = relationship("Intervention", back_populates="follow_ups")
