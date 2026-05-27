"""
Authentication routes.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from src.api.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, verify_refresh_token
from src.api.dependencies import get_current_user, get_db, MockDBSession, JWT_SECRET_KEY, JWT_ALGORITHM
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
)
async def register(request: UserRegisterRequest, db: MockDBSession = Depends(get_db)):
    try:
        if request.email in db.users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user_id = len(db.users) + 1
        db.users[request.email] = {
            "user_id": user_id,
            "email": request.email,
            "name": request.name,
            "password": hash_password(request.password),
            "role": "user",
            "created_at": datetime.now(),
        }
        return UserResponse(
            user_id=user_id,
            email=request.email,
            name=request.name,
            role="user",
            created_at=db.users[request.email]["created_at"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return JWT tokens.",
)
async def login(request: UserLoginRequest, db: MockDBSession = Depends(get_db)):
    try:
        user = db.users.get(request.email)
        if not user or not verify_password(request.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        access_token, exp = create_access_token(
            user["user_id"], user["email"], user["role"], JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        refresh_token, _ = create_refresh_token(
            user["user_id"], JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=exp,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token.",
)
async def refresh(request: RefreshTokenRequest, db: MockDBSession = Depends(get_db)):
    try:
        user_id = verify_refresh_token(request.refresh_token, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        user = next((u for u in db.users.values() if u["user_id"] == user_id), None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        access_token, exp = create_access_token(
            user["user_id"], user["email"], user["role"], JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        new_refresh_token, _ = create_refresh_token(
            user["user_id"], JWT_SECRET_KEY, algorithm=JWT_ALGORITHM
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=exp,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get details of the currently authenticated user.",
)
async def get_me(current_user: dict = Depends(get_current_user), db: MockDBSession = Depends(get_db)):
    try:
        user = db.users.get(current_user["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name", ""),
            role=user["role"],
            created_at=user.get("created_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )
