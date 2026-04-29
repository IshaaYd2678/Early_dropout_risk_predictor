"""
Security utilities - Password hashing, JWT tokens, encryption.
Production-grade security implementation.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64

from src.core.config import settings


# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def create_refresh_token(subject: Union[str, int]) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# Encryption for PII
def get_fernet() -> Fernet:
    """Get Fernet instance for encryption."""
    # Ensure key is 32 bytes and base64 encoded
    key = settings.encryption_key[:32].encode()
    key_b64 = base64.urlsafe_b64encode(key.ljust(32, b'0'))
    return Fernet(key_b64)


def encrypt_pii(data: str) -> str:
    """Encrypt PII data."""
    if not data:
        return data
    fernet = get_fernet()
    return fernet.encrypt(data.encode()).decode()


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt PII data."""
    if not encrypted_data:
        return encrypted_data
    try:
        fernet = get_fernet()
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return encrypted_data  # Return as-is if decryption fails


def mask_email(email: str) -> str:
    """Mask email for display."""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "*" * len(local)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def mask_student_id(student_id: str) -> str:
    """Mask student ID for logs."""
    if not student_id or len(student_id) < 4:
        return "****"
    return student_id[:2] + "*" * (len(student_id) - 4) + student_id[-2:]
