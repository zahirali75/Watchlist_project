"""Env yang salah harus membuat aplikasi menolak start."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _base_env() -> dict:
    return {
        "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:5432/cinelist_test",
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


def test_database_url_wajib_ada(monkeypatch):
    # Variabel environment menang atas kwarg, jadi harus dibersihkan dulu.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    env = _base_env()
    env.pop("DATABASE_URL")
    with pytest.raises(ValidationError):
        Settings(**env, _env_file=None)


def test_cors_bisa_diatur_ulang():
    settings = Settings(**_base_env(), CORS_ORIGINS="http://a.test, http://b.test", _env_file=None)
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_secret_key_placeholder_dari_env_example_ditolak():
    # Nilai contoh di .env.example panjangnya >= 32 tetapi bukan secret sungguhan.
    placeholder = "replace_with_a_private_random_secret_of_at_least_32_characters"
    assert len(placeholder) >= 32
    with pytest.raises(ValidationError, match="nilai contoh"):
        Settings(**{**_base_env(), "SECRET_KEY": placeholder}, _env_file=None)


def test_algorithm_hanya_hs256():
    with pytest.raises(ValidationError):
        Settings(**{**_base_env(), "ALGORITHM": "none"}, _env_file=None)
    with pytest.raises(ValidationError):
        Settings(**{**_base_env(), "ALGORITHM": "RS256"}, _env_file=None)
