"""Fixture bersama.

Tes di tests/unit dan tests/api TIDAK menyentuh database: repository di-stub.
Tes di tests/integration memakai PostgreSQL asli dan hanya jalan bila
TEST_DATABASE_URL diisi (database khusus tes; lihat docs/database.md).
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Nilai env HARUS di-set sebelum app di-import, sebab app.core.config
# memvalidasi env saat boot (memang itu tujuannya).
if os.getenv("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:5432/cinelist_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-yang-panjangnya-lebih-dari-32-karakter")
os.environ.setdefault("APP_ENV", "test")

from app.core.rate_limit import login_throttle  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.users import repository as user_repository  # noqa: E402

USER_ID = "11111111-1111-1111-1111-111111111111"
ADMIN_ID = "22222222-2222-2222-2222-222222222222"
OTHER_USER_ID = "33333333-3333-3333-3333-333333333333"

# "Tabel users" palsu untuk tes API: id -> role terkini.
FAKE_ROLES = {USER_ID: "user", ADMIN_ID: "admin", OTHER_USER_ID: "user"}


@pytest.fixture(autouse=True)
def _isolasi_tes(request, monkeypatch):
    """Stub cek identitas JWT (kecuali tes integrasi) dan reset throttle login."""
    login_throttle.clear_all()
    if "integration" not in request.node.nodeid:
        monkeypatch.setattr(
            user_repository,
            "find_identity",
            lambda user_id: {"id": user_id, "role": FAKE_ROLES[user_id]} if user_id in FAKE_ROLES else None,
        )
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def user_token() -> str:
    return create_access_token(USER_ID, "user")


@pytest.fixture
def admin_token() -> str:
    return create_access_token(ADMIN_ID, "admin")


@pytest.fixture
def user_auth(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
