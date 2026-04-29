"""Student model with risk tracking."""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import BaseModel


class RiskLevel(str, Enum):
    """Student risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StudentStatus(str, Enum):
    """Student enrollment status."""
    ENROLLED = "enrolled"
    ON_LEAVE = "on_leave"
    DROPPED_OUT = "dropped_out"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


class Student(BaseModel):
    """
    Student model with academic, behavioral, and engagement data.
    PII fields are encrypted.
    """
    
    __tablename__ = "students"
    
    # Tenant association
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Identifiers (encrypted in production)
    student_id: Mapped[str] = mapped_column(String(50), nullable=False)  # Institution's student ID
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Demographics (used for fairness monitoring, not prediction)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Academic Info
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    program: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    semester: Mapped[int] = mapped_column(Integer, default=1)
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_graduation: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    status: Mapped[StudentStatus] = mapped_column(
        SQLEnum(StudentStatus),
        default=StudentStatus.ENROLLED,
        nullable=False
    )
    
    # Socioeconomic (for fairness, not prediction)
    socioeconomic_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_generation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    financial_aid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Academic Performance
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    credits_completed: Mapped[int] = mapped_column(Integer, default=0)
    credits_attempted: Mapped[int] = mapped_column(Integer, default=0)
    
    # Engagement Metrics (updated periodically)
    attendance_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    assignment_submission_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    late_submissions: Mapped[int] = mapped_column(Integer, default=0)
    lms_login_frequency: Mapped[int] = mapped_column(Integer, default=0)
    forum_posts: Mapped[int] = mapped_column(Integer, default=0)
    resource_access_count: Mapped[int] = mapped_column(Integer, default=0)
    time_spent_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exam_scores: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Current Risk Assessment
    current_risk_level: Mapped[Optional[RiskLevel]] = mapped_column(
        SQLEnum(RiskLevel),
        nullable=True
    )
    current_risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Flags
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    intervention_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Mentor assignment
    mentor_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Additional data
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="students")
    mentor: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_students",
        foreign_keys=[mentor_id]
    )
    risk_scores: Mapped[List["StudentRiskScore"]] = relationship(
        "StudentRiskScore",
        back_populates="student",
        order_by="desc(StudentRiskScore.created_at)"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention",
        back_populates="student"
    )
    
    __table_args__ = (
        Index("ix_students_tenant_student_id", "tenant_id", "student_id", unique=True),
        Index("ix_students_risk_level", "current_risk_level"),
        Index("ix_students_department", "tenant_id", "department"),
        Index("ix_students_status", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<Student {self.student_id} ({self.department})>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_at_risk(self) -> bool:
        return self.current_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)


class StudentRiskScore(BaseModel):
    """Historical risk scores for tracking trends."""
    
    __tablename__ = "student_risk_scores"
    
    # Associations
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
    model_version_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Risk Assessment
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(SQLEnum(RiskLevel), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Explanation
    top_factors: Mapped[dict] = mapped_column(JSON, default=dict)
    all_contributions: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    week_of_semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="risk_scores")
    model_version: Mapped[Optional["ModelVersion"]] = relationship("ModelVersion")
    
    __table_args__ = (
        Index("ix_risk_scores_student_date", "student_id", "created_at"),
    )
