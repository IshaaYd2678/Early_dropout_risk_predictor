"""User model with RBAC (Role-Based Access Control)."""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import BaseModel


class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    SUPER_ADMIN = "super_admin"      # Platform admin (us)
    TENANT_ADMIN = "tenant_admin"    # Institution admin
    DEPARTMENT_HEAD = "department_head"
    MENTOR = "mentor"
    COUNSELOR = "counselor"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    LOCKED = "locked"


class User(BaseModel):
    """
    User model with multi-tenancy and RBAC.
    Supports local auth, OAuth2, and SSO.
    """
    
    __tablename__ = "users"
    
    # Tenant association
    tenant_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic Info
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Role & Permissions
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.VIEWER,
        nullable=False
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        default=UserStatus.PENDING,
        nullable=False
    )
    
    # Auth tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # SSO/OAuth
    sso_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sso_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Preferences
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    notification_settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    assigned_students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="mentor",
        foreign_keys="Student.mentor_id"
    )
    interventions_created: Mapped[List["Intervention"]] = relationship(
        "Intervention",
        back_populates="created_by_user",
        foreign_keys="Intervention.created_by"
    )
    
    __table_args__ = (
        Index("ix_users_tenant_email", "tenant_id", "email", unique=True),
        Index("ix_users_role", "role"),
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        # Role-based permissions
        role_permissions = {
            UserRole.SUPER_ADMIN: ["*"],
            UserRole.TENANT_ADMIN: ["manage_users", "manage_students", "view_all", "manage_interventions", "view_reports", "manage_settings"],
            UserRole.DEPARTMENT_HEAD: ["view_department", "manage_interventions", "view_reports"],
            UserRole.MENTOR: ["view_assigned", "create_interventions", "update_interventions"],
            UserRole.COUNSELOR: ["view_assigned", "create_interventions", "update_interventions", "view_sensitive"],
            UserRole.ANALYST: ["view_all", "view_reports", "export_data"],
            UserRole.VIEWER: ["view_assigned"],
        }
        
        perms = role_permissions.get(self.role, [])
        
        # Check wildcard or specific permission
        if "*" in perms or permission in perms:
            return True
        
        # Check custom permissions
        return self.permissions.get(permission, False)
