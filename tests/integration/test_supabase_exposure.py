"""Pengamanan paparan tabel untuk Supabase Data API (migrasi 0004). PostgreSQL asli.

Peran `anon` dan `authenticated` dibuat secara lokal untuk meniru Supabase.
Tes ini hanya berjalan bila TEST_DATABASE_URL diisi (lihat tests/integration/conftest.py).
"""
from __future__ import annotations

import psycopg
import pytest
from sqlalchemy.engine import make_url

from tests.integration.conftest import TEST_DB_URL, _alembic, reset_schema

TABLES = ("users", "movies", "watchlists", "audit_logs")
GUEST_ROLE = "cinelist_guest_test"
GUEST_PASSWORD = "guest_pw_test_only"


def _ensure_role(conn, name: str) -> None:
    conn.execute(
        f"DO $$ BEGIN CREATE ROLE {name} NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )


@pytest.fixture(scope="module")
def exposed_db(db_dsn: str) -> str:
    """Database kosong + peran Supabase tiruan, lalu `alembic upgrade head` (termasuk 0004)."""
    with psycopg.connect(db_dsn, autocommit=True) as conn:
        try:
            _ensure_role(conn, "anon")
            _ensure_role(conn, "authenticated")
        except psycopg.errors.InsufficientPrivilege:
            pytest.skip("Role tes tidak dapat dibuat (butuh CREATEROLE)")
    reset_schema(db_dsn)
    # Supabase memberi USAGE pada schema public ke anon/authenticated. reset_schema
    # membuat ulang schema tanpa itu, jadi tanpa baris ini tes RLS lulus karena alasan
    # yang salah (schema tidak terlihat), bukan karena RLS.
    with psycopg.connect(db_dsn, autocommit=True) as conn:
        conn.execute("GRANT USAGE ON SCHEMA public TO anon, authenticated")
    result = _alembic("upgrade", "head")
    assert result.returncode == 0, result.stderr
    return db_dsn


def test_rls_aktif_di_semua_tabel_aplikasi(exposed_db):
    with psycopg.connect(exposed_db) as conn:
        rows = conn.execute(
            "SELECT relname, relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND relkind = 'r' AND relname = ANY(%s)",
            (list(TABLES),),
        ).fetchall()
    assert {name: enabled for name, enabled in rows} == {t: True for t in TABLES}


def test_anon_dan_authenticated_tidak_punya_hak_akses(exposed_db):
    with psycopg.connect(exposed_db) as conn:
        for role in ("anon", "authenticated"):
            for table in TABLES:
                allowed = conn.execute(
                    "SELECT has_table_privilege(%s, %s, 'SELECT, INSERT, UPDATE, DELETE')", (role, table)
                ).fetchone()[0]
                assert allowed is False, f"{role} masih punya hak pada {table}"
            for seq in ("movies_id_seq", "watchlists_id_seq", "audit_logs_id_seq"):
                allowed = conn.execute(
                    "SELECT has_sequence_privilege(%s, %s, 'USAGE')", (role, seq)
                ).fetchone()[0]
                assert allowed is False, f"{role} masih punya hak pada sequence {seq}"


def test_rls_menolak_baris_walau_grant_diberikan(exposed_db):
    """Defense in depth: bila grant tidak sengaja dibuka lagi, RLS tanpa policy tetap memblokir."""
    with psycopg.connect(exposed_db, autocommit=True) as conn:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role) "
            "VALUES ('Rahasia', 'rls@example.com', '$pbkdf2-sha256$x$y', 'user')"
        )
        conn.execute("GRANT SELECT ON users TO anon")
        try:
            conn.execute("SET ROLE anon")
            visible = conn.execute("SELECT count(*) FROM users").fetchone()[0]
            conn.execute("RESET ROLE")
            owner_view = conn.execute("SELECT count(*) FROM users").fetchone()[0]
        finally:
            conn.execute("RESET ROLE")
            conn.execute("REVOKE SELECT ON users FROM anon")
    assert visible == 0, "RLS seharusnya menyembunyikan semua baris dari anon"
    assert owner_view >= 1, "pemilik tabel (aplikasi) harus tetap melihat data"


def test_migrasi_menolak_role_non_pemilik_tanpa_bypassrls(exposed_db):
    """Role aplikasi yang bukan pemilik dan tidak BYPASSRLS akan diblokir RLS; migrasi harus berhenti jelas."""
    if "supabase.com" in TEST_DB_URL:
        pytest.skip("Tes ownership dilewati di Supabase (pooler butuh SNI/external_id untuk multi-role)")
    
    assert _alembic("downgrade", "0003").returncode == 0
    with psycopg.connect(exposed_db, autocommit=True) as conn:
        conn.execute(f"DROP ROLE IF EXISTS {GUEST_ROLE}")
        conn.execute(f"CREATE ROLE {GUEST_ROLE} LOGIN PASSWORD '{GUEST_PASSWORD}' NOBYPASSRLS")
        # Guest harus sampai ke pemeriksaan migrasi: boleh membuat objek di public dan
        # membaca tabel, tetapi bukan pemilik tabel dan tidak punya BYPASSRLS.
        conn.execute(f"GRANT USAGE, CREATE ON SCHEMA public TO {GUEST_ROLE}")
        conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {GUEST_ROLE}")
    try:
        guest_url = make_url(TEST_DB_URL).set(username=GUEST_ROLE, password=GUEST_PASSWORD).render_as_string(
            hide_password=False
        )
        import os
        import subprocess
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        env = {**os.environ, "DATABASE_URL": guest_url}
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=root, env=env, capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "bukan pemilik tabel" in (result.stderr + result.stdout)
    finally:
        assert _alembic("upgrade", "head").returncode == 0
        with psycopg.connect(exposed_db, autocommit=True) as conn:
            conn.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {GUEST_ROLE}")
            conn.execute(f"REVOKE ALL ON SCHEMA public FROM {GUEST_ROLE}")
            conn.execute(f"DROP ROLE IF EXISTS {GUEST_ROLE}")
