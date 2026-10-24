"""Kontrak input/output untuk modul auth (register & login)."""
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
