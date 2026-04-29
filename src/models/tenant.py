"""Tenant model for multi-tenancy (institutions/universities)."""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Integer, Boolean, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class TenantPlan(str, Enum):
    """Subscription plans."""
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Tenant(BaseModel):
    """
    Tenant model representing an institution (university/college).
    Each tenant has isolated data and configurations.
    """
    
    __tablename__ = "tenants"
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Contact
    admin_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="US")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Subscription
    plan: Mapped[TenantPlan] = mapped_column(
        SQLEnum(TenantPlan),
        default=TenantPlan.BASIC,
        nullable=False
    )
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus),
        default=TenantStatus.TRIAL,
        nullable=False
    )
    max_students: Mapped[int] = mapped_column(Integer, default=1000)
    max_users: Mapped[int] = mapped_column(Integer, default=50)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Features & Config
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # SSO Configuration
    sso_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sso_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sso_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Data Compliance
    data_region: Mapped[str] = mapped_column(String(20), default="us-east-1")
    gdpr_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    ferpa_compliant: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant")
    students: Mapped[List["Student"]] = relationship("Student", back_populates="tenant")
    
    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.slug})>"
    
    @property
    def is_active(self) -> bool:
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL)
    
    @property
    def has_feature(self) -> callable:
        def check(feature: str) -> bool:
            plan_features = {
                TenantPlan.BASIC: ["risk_prediction", "basic_dashboard"],
                TenantPlan.PRO: ["risk_prediction", "basic_dashboard", "xai", "interventions", "reports"],
                TenantPlan.ENTERPRISE: ["risk_prediction", "basic_dashboard", "xai", "interventions", 
                                        "reports", "api_access", "sso", "custom_fairness", "white_label"]
            }
            return feature in plan_features.get(self.plan, []) or self.features.get(feature, False)
        return check
