"""
Authentication endpoints.
Supports local auth, OAuth2, and SSO.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.models.user import User, UserStatus
from src.models.tenant import Tenant
from src.api.deps import CurrentUser, DBSession


router = APIRouter()


# Schemas
class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    tenant_slug: Optional[str] = None


class RegisterRequest(BaseModel):
    """User registration schema."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    tenant_slug: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    
    class Config:
        from_attributes = True


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DBSession = None,
):
    """
    Authenticate user and return tokens.
    Supports username (email) + password.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == form_data.username.lower(),
            User.is_deleted == False
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        # Track failed attempts
        user.failed_login_attempts += 1
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check user status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}"
        )
    
    # Update login tracking
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None
    user.failed_login_attempts = 0
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(
        subject=user.id,
        additional_claims={
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )


@router.post("/register", response_model=UserResponse)
async def register(
    data: RegisterRequest,
    db: DBSession,
):
    """
    Register a new user.
    Requires valid tenant slug.
    """
    # Find tenant
    result = await db.execute(
        select(Tenant).where(
            Tenant.slug == data.tenant_slug,
            Tenant.is_deleted == False
        )
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant"
        )
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(
            User.email == data.email.lower(),
            User.tenant_id == tenant.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        tenant_id=tenant.id,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        status=UserStatus.PENDING,  # Requires activation
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        tenant_id=user.tenant_id
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: DBSession,
):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_deleted == False,
            User.status == UserStatus.ACTIVE
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(
        subject=user.id,
        additional_claims={
            "tenant_id": user.tenant_id,
            "role": user.role.value
        }
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
):
    """Get current authenticated user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        tenant_id=current_user.tenant_id
    )


@router.post("/logout")
async def logout(
    current_user: CurrentUser,
):
    """
    Logout user.
    In production, would invalidate the token.
    """
    # In a production system, we'd add the token to a blacklist
    # or use Redis to track invalid tokens
    return {"message": "Successfully logged out"}
