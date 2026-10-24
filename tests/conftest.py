"""Fixture test.

Kunci desain: repository di-monkeypatch. Jadi test berjalan TANPA menyentuh
Supabase sama sekali - tidak perlu jaringan, tidak perlu kredensial asli.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Nilai dummy HARUS di-set sebelum app di-import, sebab app.core.config
# memvalidasi env saat boot (memang itu tujuannya).
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-yang-panjangnya-lebih-dari-32-karakter")
os.environ.setdefault("APP_ENV", "test")

from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user_token() -> str:
    return create_access_token("11111111-1111-1111-1111-111111111111", "user")


@pytest.fixture
def admin_token() -> str:
    return create_access_token("22222222-2222-2222-2222-222222222222", "admin")


@pytest.fixture
def user_auth(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
