"""Kontrak input/output untuk modul auth (register, login, sesi, password)."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimal 8 karakter")
    name: str | None = Field(None, max_length=255)


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    userId: str
    email: str
    name: str | None = None
    role: str
    accessToken: str
    refreshToken: str | None = None


class RefreshSessionIn(BaseModel):
    """Perpanjangan sesi: kirim refresh token, dapat access token baru."""

    refreshToken: str = Field(..., min_length=16)


class LogoutIn(BaseModel):
    refreshToken: str = Field(..., min_length=16)


class ChangePasswordIn(BaseModel):
    currentPassword: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=8, description="Minimal 8 karakter")


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(..., min_length=16)
    newPassword: str = Field(..., min_length=8, description="Minimal 8 karakter")
