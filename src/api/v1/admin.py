"""Admin endpoints for system management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, CurrentTenant, DBSession, AdminUser
from src.models.tenant import Tenant, TenantPlan, TenantStatus
from src.models.user import User, UserRole
from src.models.student import Student
from src.models.ml_model import MLModel, ModelVersion, ModelStatus


router = APIRouter()


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[TenantPlan] = None
    max_students: Optional[int] = None
    max_users: Optional[int] = None
    settings: Optional[dict] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    plan: TenantPlan
    status: TenantStatus
    max_students: int
    max_users: int
    student_count: int = 0
    user_count: int = 0
    
    class Config:
        from_attributes = True


@router.get("/tenant", response_model=TenantResponse)
async def get_tenant_info(
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Get current tenant information."""
    # Get counts
    student_count = await db.scalar(
        select(func.count()).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False
        )
    )
    user_count = await db.scalar(
        select(func.count()).where(
            User.tenant_id == tenant.id,
            User.is_deleted == False
        )
    )
    
    response = TenantResponse.model_validate(tenant)
    response.student_count = student_count
    response.user_count = user_count
    
    return response


@router.patch("/tenant", response_model=TenantResponse)
async def update_tenant(
    data: TenantUpdate,
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Update tenant settings (admin only)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    await db.commit()
    await db.refresh(tenant)
    
    return TenantResponse.model_validate(tenant)


@router.get("/models")
async def list_models(
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """List ML models and versions."""
    result = await db.execute(
        select(MLModel).where(
            (MLModel.tenant_id == tenant.id) | (MLModel.tenant_id.is_(None))
        ).order_by(MLModel.created_at.desc())
    )
    models = result.scalars().all()
    
    model_list = []
    for model in models:
        # Get latest version
        version_result = await db.execute(
            select(ModelVersion).where(
                ModelVersion.model_id == model.id
            ).order_by(ModelVersion.created_at.desc()).limit(1)
        )
        latest_version = version_result.scalar_one_or_none()
        
        model_list.append({
            "id": model.id,
            "name": model.name,
            "type": model.model_type.value,
            "is_active": model.is_active,
            "latest_version": latest_version.version if latest_version else None,
            "deployed_version": model.current_version_id,
            "created_at": model.created_at.isoformat()
        })
    
    return model_list


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    version_id: str,
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Deploy a specific model version."""
    # Get model
    result = await db.execute(
        select(MLModel).where(MLModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get version
    version_result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.id == version_id,
            ModelVersion.model_id == model_id
        )
    )
    version = version_result.scalar_one_or_none()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model version not found"
        )
    
    # Update current version
    model.current_version_id = version_id
    version.status = ModelStatus.DEPLOYED
    version.deployed_at = datetime.utcnow()
    version.deployed_by = current_user.id
    
    await db.commit()
    
    return {"message": f"Model {model.name} v{version.version} deployed successfully"}


@router.get("/audit-logs")
async def get_audit_logs(
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
    limit: int = 100,
):
    """Get audit logs (admin only)."""
    from src.models.audit import AuditLog
    
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == tenant.id
        ).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "action": log.action.value,
            "user_email": log.user_email,
            "description": log.description,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


from datetime import datetime
