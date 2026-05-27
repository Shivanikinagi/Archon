"""
Security and JWT authentication setup

Handles password hashing, JWT token generation, and authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: int
    email: str
    role: str
    exp: datetime


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plain password against hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
    iss: str = "research-agent",
    aud: str = "research-agent-api"
) -> tuple[str, int]:
    """
    Generate JWT access token
    
    Args:
        user_id: User ID
        email: User email
        role: User role
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default: HS256)
        expires_delta: Token expiration time
        iss: Token issuer
        aud: Token audience
        
    Returns:
        Tuple of (token, expiration_timestamp)
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=1)
    
    expire = datetime.utcnow() + expires_delta
    
    data = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "iss": iss,
        "aud": aud,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    try:
        encoded_jwt = jwt.encode(data, secret_key, algorithm=algorithm)
        return encoded_jwt, int(expire.timestamp())
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise


def create_refresh_token(
    user_id: int,
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
    iss: str = "research-agent",
    aud: str = "research-agent-api"
) -> tuple[str, int]:
    """
    Generate JWT refresh token
    
    Args:
        user_id: User ID
        secret_key: Secret key for signing
        algorithm: JWT algorithm (default: HS256)
        expires_delta: Token expiration time
        iss: Token issuer
        aud: Token audience
        
    Returns:
        Tuple of (token, expiration_timestamp)
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    expire = datetime.utcnow() + expires_delta
    
    data = {
        "user_id": user_id,
        "iss": iss,
        "aud": aud,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    try:
        encoded_jwt = jwt.encode(data, secret_key, algorithm=algorithm)
        return encoded_jwt, int(expire.timestamp())
    except Exception as e:
        logger.error(f"Refresh token generation error: {e}")
        raise


def verify_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
    expected_aud: str = "research-agent-api"
) -> TokenData:
    """
    Verify JWT token and return token data
    
    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithm: JWT algorithm
        expected_aud: Expected audience claim
        
    Returns:
        TokenData object
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm], audience=expected_aud)
        
        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")
        exp = datetime.fromtimestamp(payload.get("exp"))
        
        if not all([user_id, email, role]):
            raise JWTError("Missing required claims")
        
        return TokenData(user_id=user_id, email=email, role=role, exp=exp)
    
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise JWTError(f"Token verification failed: {str(e)}")


def verify_refresh_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
    expected_aud: str = "research-agent-api"
) -> int:
    """
    Verify refresh token and return user_id
    
    Args:
        token: Refresh token string
        secret_key: Secret key for verification
        algorithm: JWT algorithm
        expected_aud: Expected audience claim
        
    Returns:
        User ID from token
        
    Raises:
        JWTError: If token is invalid or not a refresh token
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm], audience=expected_aud)
        
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        
        user_id = payload.get("user_id")
        if not user_id:
            raise JWTError("Missing user_id claim")
        
        return user_id
    
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Refresh token verification error: {e}")
        raise JWTError(f"Token verification failed: {str(e)}")
