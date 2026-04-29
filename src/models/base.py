"""Base model with common fields and multi-tenancy support."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class TenantMixin:
    """Mixin for multi-tenancy support."""
    
    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        return mapped_column(
            UUID(as_uuid=False),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model with UUID primary key, timestamps, and soft delete."""
    
    __abstract__ = True
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4())
    )


class TenantBaseModel(BaseModel, TenantMixin):
    """Base model with multi-tenancy support."""
    
    __abstract__ = True
    
    @declared_attr
    def __table_args__(cls):
        return (
            Index(f"ix_{cls.__tablename__}_tenant_id", "tenant_id"),
        )
