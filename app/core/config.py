"""Validasi seluruh environment variable saat boot.

Dulu: os.getenv("SECRET_KEY") or "supersecretkey"  -> app tetap jalan dengan
secret palsu. Sekarang: app MENOLAK start kalau ada yang salah/kurang.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # ---- Supabase ----
    SUPABASE_URL: str = Field(..., min_length=1)
    SUPABASE_KEY: str = Field(..., min_length=1)

    # ---- JWT ----
    SECRET_KEY: str = Field(..., min_length=32, description="Minimal 32 karakter")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ---- Paginasi ----
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ---- Opsional (dipakai script seeding) ----
    TMDB_API_KEY: str | None = None
    DATABASE_URL: str | None = None  # connection string Postgres (untuk Alembic)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Dibaca sekali lalu di-cache; gagal = app tidak boot."""
    return Settings()
