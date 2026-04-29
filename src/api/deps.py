"""
API Dependencies - Authentication, Authorization, Database.
Reusable dependencies for FastAPI endpoints.
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.security import decode_token, hash_api_key
from src.core.config import settings
from src.models.user import User, UserRole, UserStatus
from src.models.tenant import Tenant, TenantStatus


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    api_key: Annotated[Optional[str], Depends(api_key_header)] = None,
) -> User:
    """
    Get current authenticated user from JWT token or API key.
    Raises 401 if not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = None
    
    # Try JWT token first
    if token:
        payload = decode_token(token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                result = await db.execute(
                    select(User).where(
                        User.id == user_id,
                        User.is_deleted == False
                    )
                )
                user = result.scalar_one_or_none()
    
    # Try API key if no token
    if not user and api_key:
        hashed_key = hash_api_key(api_key)
        # API keys would be stored in a separate table
        # For now, skip this implementation
        pass
    
    if not user:
        raise credentials_exception
    
    # Check user status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_tenant(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> Tenant:
    """Get the current user's tenant."""
    result = await db.execute(
        select(Tenant).where(
            Tenant.id == current_user.tenant_id,
            Tenant.is_deleted == False
        )
    )
    tenant = result.scalar_one_or_none()
    
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not found or inactive"
        )
    
    return tenant


def require_roles(*roles: UserRole):
    """Dependency factory for role-based access control."""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if current_user.role not in roles and UserRole.SUPER_ADMIN not in roles:
            if current_user.role != UserRole.SUPER_ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
        return current_user
    return role_checker


def require_permission(permission: str):
    """Dependency factory for permission-based access control."""
    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


# Common dependency annotations
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
CurrentTenant = Annotated[Tenant, Depends(get_current_tenant)]
DBSession = Annotated[AsyncSession, Depends(get_db)]

# Role-specific dependencies
AdminUser = Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))]
MentorUser = Annotated[User, Depends(require_roles(UserRole.MENTOR, UserRole.COUNSELOR, UserRole.DEPARTMENT_HEAD, UserRole.TENANT_ADMIN))]
