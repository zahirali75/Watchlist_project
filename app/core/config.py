"""Validasi seluruh environment variable saat boot.

Dulu: os.getenv("SECRET_KEY") or "supersecretkey"  -> app tetap jalan dengan
secret palsu. Sekarang: app MENOLAK start kalau ada yang salah/kurang.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Fragmen yang menandakan nilai contoh/placeholder, bukan secret sungguhan.
_PLACEHOLDER_MARKERS = ("replace_", "replace-", "your_", "your-", "changeme", "change_me", "example")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # variabel lain di .env tidak bikin error
    )

    # ---- App ----
    APP_NAME: str = "CineList API"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    APP_DESCRIPTION: str = "REST API untuk aplikasi CineList"

    # CORS_ORIGINS sengaja disimpan sebagai string (dipisah koma), bukan list[str].
    # Sebab pydantic-settings mem-parse field bertipe kompleks sebagai JSON dulu;
    # nilai "http://a,http://b" akan gagal di-parse sebelum validator sempat jalan.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ---- Direct PostgreSQL ----
    DATABASE_URL: str = Field(..., min_length=1, description="PostgreSQL DSN for the active API")

    # ---- JWT ----
    SECRET_KEY: str = Field(..., min_length=32, description="Minimal 32 karakter")
    # Hanya HS256 yang didukung. Literal mencegah konfigurasi env mengganti algoritma
    # (mis. ke "none" atau algoritma asimetris yang tidak disiapkan).
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, ge=1)
    # Masa berlaku refresh token (hari). Access token boleh sering kedaluwarsa;
    # refresh token yang membuat pengguna tidak perlu login ulang terus-menerus.
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(14, ge=1)

    # ---- Pembatas login (in-memory) ----
    # LOGIN_MAX_ATTEMPTS: gagal per (IP + email). LOGIN_IP_MAX_ATTEMPTS: gagal per IP
    # untuk SEMUA email (menahan password spraying). Keduanya dalam jendela LOGIN_WINDOW_SECONDS.
    LOGIN_MAX_ATTEMPTS: int = Field(5, ge=1)
    LOGIN_IP_MAX_ATTEMPTS: int = Field(50, ge=1)
    LOGIN_WINDOW_SECONDS: int = Field(300, ge=1)

    # ---- Paginasi ----
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ---- Opsional (dipakai script seeding) ----
    TMDB_API_KEY: str | None = None

    # ---- Lupa password ----
    # Masa berlaku tautan reset (menit). Sengaja pendek: tautan ini setara password.
    PASSWORD_RESET_EXPIRE_MINUTES: int = Field(30, ge=1)
    # Alamat API dipakai untuk menyusun tautan reset yang dikirim ke email.
    APP_BASE_URL: str = "http://localhost:5173"
    # SMTP opsional. Bila SMTP_HOST kosong, email DITULIS ke log server saja
    # (mode pengembangan) - tidak ada email sungguhan yang terkirim.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = Field(587, ge=1)
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "no-reply@cinelist.local"
    SMTP_USE_TLS: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def _secret_not_placeholder(cls, value: str) -> str:
        # .env.example berisi teks contoh yang panjangnya >= 32. Tanpa pemeriksaan ini,
        # menyalin contoh apa adanya membuat siapa pun bisa memalsukan token admin.
        lowered = value.lower()
        if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
            raise ValueError("SECRET_KEY masih berupa nilai contoh; ganti dengan secret acak (lihat .env.example)")
        return value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _no_wildcard_origin(cls, value: str) -> str:
        # allow_credentials=True tidak boleh digabung dengan origin '*'.
        if "*" in [item.strip() for item in value.split(",")]:
            raise ValueError("CORS_ORIGINS tidak boleh '*'; isi daftar origin frontend yang dipercaya")
        return value

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Dibaca sekali lalu di-cache; gagal = app tidak boot."""
    return Settings()
