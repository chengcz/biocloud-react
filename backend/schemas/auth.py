"""Pydantic schemas for authentication"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6, max_length=100)


class RegisterRequest(BaseModel):
    """Registration request schema"""
    username: str = Field(..., min_length=3, max_length=30, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(..., min_length=1, max_length=30)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr