"""Tes integrasi: PostgreSQL ASLI, hanya jalan bila TEST_DATABASE_URL diisi.

PENGAMAN: tes ini menghapus dan membuat ulang schema `public`. Karena itu
TEST_DATABASE_URL wajib menunjuk ke database yang namanya mengandung "test"
(mis. cinelist_test). Jangan pernah mengarahkannya ke database produksi/Supabase.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")


def _psycopg_dsn() -> str:
    return TEST_DB_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def _alembic(*args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": TEST_DB_URL}
    return subprocess.run([sys.executable, "-m", "alembic", *args], cwd=ROOT, env=env, capture_output=True, text=True)


@pytest.fixture(scope="session")
def db_dsn() -> str:
    if not TEST_DB_URL:
        pytest.skip("TEST_DATABASE_URL belum diisi (tes integrasi dilewati)")
    name = make_url(TEST_DB_URL).database or ""
    if "test" not in name.lower():
        pytest.fail(f"Ditolak: database '{name}' bukan database tes (namanya harus mengandung 'test')")
    return _psycopg_dsn()


def reset_schema(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")


@pytest.fixture(scope="session")
def migrated_db(db_dsn: str) -> str:
    """Database kosong -> `alembic upgrade head` (sekaligus menguji migrasi dari nol)."""
    reset_schema(db_dsn)
    result = _alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr
    return db_dsn


@pytest.fixture
def clean_tables(migrated_db: str) -> str:
    """Kosongkan data antar tes (skema tetap)."""
    with psycopg.connect(migrated_db, autocommit=True) as conn:
        conn.execute("TRUNCATE audit_logs, watchlists, reviews, movies, users RESTART IDENTITY CASCADE")
    return migrated_db


@pytest.fixture
def schema_ke_head(db_dsn: str):
    """Untuk tes yang SENGAJA menurunkan skema (downgrade / berhenti di revisi lama).

    Tes seperti itu meninggalkan `public` tanpa tabel terbaru, dan karena
    `migrated_db` berskopi session, tes BERIKUTNYA di satu sesi akan gagal dengan
    "relation ... does not exist" yang menyesatkan. Fixture ini memulihkan skema
    ke `head` setelah tes selesai - termasuk bila tesnya gagal (yield).
    """
    yield
    reset_schema(db_dsn)
    assert _alembic("upgrade", "head").returncode == 0, "gagal memulihkan skema tes ke head"


@pytest.fixture
def sql(clean_tables: str):
    """Helper SQL langsung ke database tes (untuk menyiapkan/memeriksa data)."""
    conn = psycopg.connect(clean_tables, autocommit=True)
    yield conn
    conn.close()
