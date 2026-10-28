"""Alembic: dari nol, bolak-balik, dan model == skema."""
from __future__ import annotations

import psycopg

from tests.integration.conftest import _alembic, reset_schema


def test_upgrade_dari_database_kosong_dan_model_sama_dengan_skema(migrated_db):
    result = _alembic("check")  # gagal bila model SQLAlchemy dan skema database berbeda
    assert result.returncode == 0, result.stdout + result.stderr
    with psycopg.connect(migrated_db) as conn:
        tables = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert {"users", "movies", "watchlists", "audit_logs", "reviews", "alembic_version"} <= tables


def test_downgrade_base_lalu_upgrade_lagi(db_dsn, schema_ke_head):
    reset_schema(db_dsn)
    assert _alembic("upgrade", "head").returncode == 0
    assert _alembic("downgrade", "base").returncode == 0
    with psycopg.connect(db_dsn) as conn:
        left = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert left == {"alembic_version"}
    assert _alembic("upgrade", "head").returncode == 0


def test_0003_berhenti_jelas_bila_ada_email_kembar(db_dsn, schema_ke_head):
    reset_schema(db_dsn)
    assert _alembic("upgrade", "0002").returncode == 0
    with psycopg.connect(db_dsn, autocommit=True) as conn:
        conn.execute("INSERT INTO users (name,email,password_hash) VALUES ('a','Dup@x.com','h'),('b','dup@x.com','h')")
    result = _alembic("upgrade", "head")
    assert result.returncode != 0 and "email kembar" in (result.stdout + result.stderr)
