"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.models import UserModel
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    UserResponse,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import BadRequestException, UnauthorizedException, ConflictException
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """User login - returns JWT tokens"""
    # Find user by username
    result = await db.execute(
        select(UserModel).where(
            UserModel.user_name == request.username,
            UserModel.del_flag == "0"
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise UnauthorizedException("Incorrect username or password")

    if user.status != "active":
        raise BadRequestException("User account is disabled")

    # Update login info
    user.login_date = datetime.utcnow()
    # Note: In production, get real IP from request
    # user.login_ip = request.client.host

    # Create tokens
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Store session token
    user.session_token = access_token
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """User registration"""
    # Check if username exists
    result = await db.execute(
        select(UserModel).where(UserModel.user_name == request.username)
    )
    if result.scalar_one_or_none():
        raise ConflictException("Username already registered")

    # Check if email exists
    if request.email:
        result = await db.execute(
            select(UserModel).where(UserModel.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ConflictException("Email already registered")

    # Create user
    user = UserModel(
        user_name=request.username,
        password_hash=get_password_hash(request.password),
        name=request.name,
        email=request.email,
        phone=request.phone,
        status="active",
        del_flag="0"
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/logout")
async def logout(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """User logout - invalidate session"""
    current_user.session_token = None
    await db.commit()
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    # Verify user exists and is active
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == user_id,
            UserModel.del_flag == "0",
            UserModel.status == "active"
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User not found or inactive")

    # Create new tokens
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    user.session_token = access_token
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/password/change")
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if not verify_password(request.old_password, current_user.password_hash):
        raise BadRequestException("Incorrect current password")

    current_user.password_hash = get_password_hash(request.new_password)
    current_user.session_token = None  # Force re-login
    await db.commit()

    return {"message": "Password changed successfully"}