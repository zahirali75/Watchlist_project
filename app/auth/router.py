"""Endpoint register, login, sesi (perpanjangan & logout), dan password."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.auth import service
from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    ChangePasswordIn,
    ForgotPasswordIn,
    LoginUser,
    RefreshSessionIn,
    RegisterUser,
    ResetPasswordIn,
    LogoutIn,
)

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


@router.post("/auth/refresh")
def refresh_session(payload: RefreshSessionIn):
    """PENAMBAHAN BARU: tukar refresh token dengan access token baru.

    Dipakai frontend saat access token sudah kedaluwarsa, supaya pengguna tidak
    perlu mengetik email & password lagi.
    """
    result = service.refresh_session(payload.refreshToken)
    return {"success": True, "message": "Sesi diperpanjang", **result}


@router.post("/auth/logout")
def logout(payload: LogoutIn, current_user: dict = Depends(get_current_user)):
    """PENAMBAHAN BARU: cabut satu sesi (perangkat ini saja)."""
    result = service.logout(payload.refreshToken, current_user["user_id"])
    return {"success": True, "message": "Logout berhasil", **result}


@router.post("/auth/change-password")
def change_password(payload: ChangePasswordIn, current_user: dict = Depends(get_current_user)):
    """PENAMBAHAN BARU: ganti password milik sendiri (wajib password lama)."""
    result = service.change_password(current_user["user_id"], payload.currentPassword, payload.newPassword)
    return {"success": True, "message": "Password berhasil diganti", **result}


@router.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordIn):
    """PENAMBAHAN BARU: minta tautan atur ulang password lewat email.

    Jawabannya SELALU sama, baik email terdaftar maupun tidak, supaya endpoint ini
    tidak bisa dipakai menebak email mana yang punya akun.
    """
    result = service.request_password_reset(payload.email)
    return {"success": True, **result}


@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordIn):
    """PENAMBAHAN BARU: pasang password baru memakai token dari email."""
    result = service.reset_password(payload.token, payload.newPassword)
    return {"success": True, "message": "Password berhasil diatur ulang", **result}


# --- Alias lama, supaya frontend yang sudah ada tidak langsung rusak ---
@router.post("/users", include_in_schema=False)
def register_legacy(payload: RegisterUser):
    return register(payload)


@router.post("/login", include_in_schema=False)
def login_legacy(payload: LoginUser, request: Request):
    return login(payload, request)
