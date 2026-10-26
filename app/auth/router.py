"""Endpoint register & login."""
from __future__ import annotations

from fastapi import APIRouter, Request, status

from app.auth import service
from app.auth.schemas import LoginUser, RegisterUser

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterUser):
    result = service.register_user(payload)
    return {"success": True, "message": "Registrasi berhasil", **result}


@router.post("/auth/login")
def login(payload: LoginUser, request: Request):
    client_ip = request.client.host if request.client else None
    result = service.authenticate_user(payload.email, payload.password, client_ip=client_ip)
    return {"success": True, "message": "Login berhasil", **result}


# --- Alias lama, supaya frontend yang sudah ada tidak langsung rusak ---
@router.post("/users", include_in_schema=False)
def register_legacy(payload: RegisterUser):
    return register(payload)


@router.post("/login", include_in_schema=False)
def login_legacy(payload: LoginUser, request: Request):
    return login(payload, request)
