"""Audit logging service."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog, AuditAction


async def create_audit_log(
    db: AsyncSession,
    action: AuditAction,
    user_id: Optional[str],
    tenant_id: Optional[str],
    resource_type: Optional[str],
    resource_id: Optional[str],
    description: str,
    details: dict = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    user_email: Optional[str] = None,
    user_role: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry."""
    log = AuditLog(
        id=str(uuid4()),
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(log)
    # Note: Commit is handled by the caller or context manager
    
    return log
