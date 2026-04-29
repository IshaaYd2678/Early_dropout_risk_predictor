"""User management endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, CurrentTenant, DBSession, AdminUser
from src.models.user import User, UserRole, UserStatus
from src.core.security import hash_password


router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.VIEWER
    department: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    department: Optional[str]
    status: UserStatus
    last_login_at: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
):
    """List users (admin only)."""
    query = select(User).where(
        User.tenant_id == tenant.id,
        User.is_deleted == False
    )
    
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    
    result = await db.execute(query.order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Create a new user (admin only)."""
    # Check duplicate
    existing = await db.execute(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == data.email.lower()
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    user = User(
        tenant_id=tenant.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        department=data.department,
        status=UserStatus.ACTIVE,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Update user (admin only)."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant.id,
            User.is_deleted == False
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: DBSession,
    current_user: AdminUser,
    tenant: CurrentTenant,
):
    """Delete user (soft delete, admin only)."""
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant.id,
            User.is_deleted == False
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user.is_deleted = True
    await db.commit()
    
    return {"message": "User deleted successfully"}
