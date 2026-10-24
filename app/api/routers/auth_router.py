"""Endpoint register & login."""
from __future__ import annotations

from fastapi import APIRouter, status

from app.schemas.auth_schema import LoginUser, RegisterUser
from app.services import auth_service

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterUser):
    result = auth_service.register_user(payload)
    return {"success": True, "message": "Registrasi berhasil", **result}


@router.post("/auth/login")
def login(payload: LoginUser):
    result = auth_service.authenticate_user(payload.email, payload.password)
    return {"success": True, "message": "Login berhasil", **result}


# --- Alias lama, supaya frontend yang sudah ada tidak langsung rusak ---
@router.post("/users", include_in_schema=False)
def register_legacy(payload: RegisterUser):
    return register(payload)


@router.post("/login", include_in_schema=False)
def login_legacy(payload: LoginUser):
    return login(payload)
