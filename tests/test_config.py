"""Env yang salah harus membuat aplikasi menolak start."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _base_env() -> dict:
    return {
        "SUPABASE_URL": "https://dummy.supabase.co",
        "SUPABASE_KEY": "dummy-key",
        "SECRET_KEY": "x" * 40,
    }


def test_settings_valid():
    settings = Settings(**{**_base_env(), "_env_file": None})
    assert settings.ALGORITHM == "HS256"
    assert settings.cors_origins == ["http://localhost:5173", "http://localhost:3000"]


def test_secret_key_terlalu_pendek_ditolak(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(**{**_base_env(), "SECRET_KEY": "pendek"}, _env_file=None)


def test_supabase_url_wajib_ada(monkeypatch):
    # Variabel environment menang atas kwarg, jadi harus dibersihkan dulu.
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    env = _base_env()
    env.pop("SUPABASE_URL")
    with pytest.raises(ValidationError):
        Settings(**env, _env_file=None)


def test_cors_bisa_diatur_ulang():
    settings = Settings(**_base_env(), CORS_ORIGINS="http://a.test, http://b.test", _env_file=None)
    assert settings.cors_origins == ["http://a.test", "http://b.test"]
